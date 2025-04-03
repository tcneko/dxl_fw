#!/usr/bin/env python3


# author: tcneko <tcneko@outlook.com>
# start from: 2022.07
# last test environment: ubuntu 20.04
# description:


# import
import hashlib
import ipaddress
import json
import random
import subprocess
import typer


# variables
debug = False
iptables_exec = "iptables"
ipset_family_modify = ""


# function
def shell(cmd, non_zero_return=False):
    if debug:
        typer.echo(cmd)
    proc = subprocess.run(
        [cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    if proc.returncode != 0 and not non_zero_return:
        msg = {
            "severity": 3,
            "message": f"Command '{cmd}' return non-zero code: {proc.returncode}",
        }
        typer.echo(json.dumps(msg))
    return proc.returncode, proc.stdout, proc.stderr


def init_iptables_table(table):
    shell(f"{iptables_exec} -t {table} -F")
    shell(f"{iptables_exec} -t {table} -X")


def init_ipset(ipset, type):
    return_code = shell(f"ipset list {ipset}", non_zero_return=True)[0]
    if return_code == 0:
        shell(f"ipset destroy {ipset}")
    shell(f"ipset create {ipset} {type} {ipset_family_modify}")


def init_iptables_chain(table, chain):
    return_code = shell(
        f"{iptables_exec} -t {table} -L {chain} -vn", non_zero_return=True
    )[0]
    if return_code == 0:
        shell(f"{iptables_exec} -t {table} -F {chain}")
    else:
        shell(f"{iptables_exec} -t {table} -N {chain}")


def sterilize_ipset_member(raw_member):
    net = ipaddress.ip_network(raw_member, strict=False)
    if net.prefixlen == net.max_prefixlen:
        member = str(ipaddress.ip_interface(net).ip)
    else:
        member = str(net)
    return member


def sync_ipset_member(ipset, member_list):
    stdout = shell(f"ipset list {ipset}")[1]
    old_member_set = set(stdout.decode("utf-8").split("\n")[8:-1])
    new_member_set = set(map(sterilize_ipset_member, member_list))
    add_member_set = new_member_set - old_member_set
    del_member_set = old_member_set - new_member_set
    for member in add_member_set:
        shell(f"ipset add {ipset} {member}")
    for member in del_member_set:
        shell(f"ipset del {ipset} {member}")


def get_rule_index(table, chain, rule_hash):
    stdout = shell(f"{iptables_exec} -t {table} -L {chain} -vn --line-number")[1]
    line_list = stdout.decode("utf-8").split("\n")
    for line in line_list:
        if rule_hash in line:
            return line.split()[0]
    return 0


def get_lcs_list(list_x, list_y):
    list_x_len = len(list_x)
    list_y_len = len(list_y)
    dp = [[0] * (list_y_len + 1) for i in range(list_x_len + 1)]

    for i in range(list_x_len - 1, -1, -1):
        for j in range(list_y_len - 1, -1, -1):
            r = max(dp[i + 1][j], dp[i][j + 1])
            if list_x[i] == list_y[j]:
                r = max(r, dp[i + 1][j + 1] + 1)
            dp[i][j] = r

    lcs_list = []
    i = 0
    j = 0
    while i < list_x_len and j < list_y_len:
        if list_x[i] == list_y[j]:
            lcs_list.append(list_x[i])
            i += 1
            j += 1
        elif dp[i][j] == dp[i + 1][j]:
            i += 1
        elif dp[i][j] == dp[i][j + 1]:
            j += 1
    return lcs_list


def sync_iptables_rule(table, chain, rule_list):
    stdout = shell(f"{iptables_exec} -t {table} -L {chain} -vn --line-number")[1]
    old_rule_list = stdout.decode("utf-8").split("\n")[2:-1]
    old_rule_hash_list = []
    for rule in old_rule_list:
        try:
            rule_element_list = rule.split()
            comment_index = rule_element_list.index("/*") + 1
            comment = rule_element_list[comment_index]
            rule_hash = json.loads(comment)["rule_hash"]
        except:
            rule_hash = hashlib.sha256(
                str(random.getrandbits(128)).encode("utf-8")
            ).hexdigest()
        old_rule_hash_list.append(rule_hash)

    new_rule_list = rule_list
    new_rule_hash_list = []
    for rule in new_rule_list:
        rule_hash = hashlib.sha256(rule.encode("utf-8")).hexdigest()
        new_rule_hash_list.append(rule_hash)

    lcs_rule_hash_list = get_lcs_list(old_rule_hash_list, new_rule_hash_list)

    for ix in range(len(old_rule_hash_list) - 1, -1, -1):
        rule_hash = old_rule_hash_list[ix]
        if rule_hash in lcs_rule_hash_list:
            continue
        rule_index = ix + 1
        shell(f"{iptables_exec} -t {table} -D {chain} {rule_index}")

    rule_index = len(lcs_rule_hash_list) + 1
    for ix in range(len(new_rule_hash_list) - 1, -1, -1):
        rule_hash = new_rule_hash_list[ix]
        if rule_hash in lcs_rule_hash_list:
            rule_index = rule_index - 1
        else:
            rule = new_rule_list[ix]
            shell(
                f'{iptables_exec} -t {table} -I {chain} {rule_index} {rule} -m comment --comment \'{{"rule_hash":"{rule_hash}"}}\''
            )


def main(
    config_file: str = typer.Option(
        "config.json", "-c", "--config-file", help="Path to configuration"
    ),
    ipv6: bool = typer.Option(False, "-6", "--ipv6", help="IPv4 or IPv6"),
    debug: bool = typer.Option(False, help="Debug mode"),
):

    globals()["debug"] = debug
    try:
        with open(config_file) as fp:
            config = json.load(fp)
    except:
        msg = {
            "severity": 3,
            "message": f"Fail to load configuration file: {config_file}",
        }
        typer.echo(json.dumps(msg))
        raise typer.Exit(code=1)

    if ipv6:
        global iptables_exec, ipset_family_modify
        iptables_exec = "ip6tables"
        ipset_family_modify = "family inet6"

    task_list = config["task_list"]
    for task in task_list:
        type = task["type"]
        var_list = task["var_list"]
        for var in var_list:
            if type == "init_ipset":
                init_ipset(var["ipset"], var["type"])
            elif type == "init_iptables_table":
                init_iptables_table(var["table"])
            elif type == "init_iptables_chain":
                init_iptables_chain(var["table"], var["chain"])
            elif type == "sync_ipset_member":
                sync_ipset_member(var["ipset"], var["member_list"])
            elif type == "sync_iptables_rule":
                sync_iptables_rule(var["table"], var["chain"], var["rule_list"])


if __name__ == "__main__":
    typer.run(main)
