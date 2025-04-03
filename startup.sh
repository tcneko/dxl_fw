#!/bin/bash

# author: tcneko <tcneko@outlook.com>
# start from: 2022.11
# last test environment: ubuntu 20.04
# description:

export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# variables
ins_dir='/opt/sh/dxl_fw'
cfg_dir='/opt/sh/dxl_fw'
py3_exec='/usr/local/venv/python3/bin/python3'

# function
main() {
  ${py3_exec} ${ins_dir}/dxl_fw.py -c ${cfg_dir}/onetime.json
  ${py3_exec} ${ins_dir}/dxl_fw.py -c ${cfg_dir}/runtime.json
  ${py3_exec} ${ins_dir}/dxl_fw.py --ipv6 -c ${cfg_dir}/onetime_v6.json
  ${py3_exec} ${ins_dir}/dxl_fw.py --ipv6 -c ${cfg_dir}/runtime_v6.json
}

# main
main

exit $?
