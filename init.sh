#!/bin/bash

# author: tcneko <tcneko@outlook.com>
# start from: 2022.07
# last test environment: ubuntu 20.04
# description:

export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# variables
cur_dir="$(dirname ${BASH_SOURCE[0]})"
ins_dir='/opt/sh/dxl_fw'
cfg_dir='/opt/sh/dxl_fw'

# function
echo_error() {
  echo >&2 -e "\e[1;31m[Error]\e[0m $@"
}

install() {
  if [[ ! -d ${ins_dir} ]]; then
    mkdir -p ${ins_dir}
  fi
  cp -f ${cur_dir}/dxl_fw.py ${ins_dir}/dxl_fw.py

  if [[ ! -d ${cfg_dir} ]]; then
    mkdir -p ${cfg_dir}
  fi
  cp -n ${cur_dir}/onetime.json \
    ${cur_dir}/runtime.json \
    ${cfg_dir}
}

main() {
  if (($(id -u) != 0)); then
    echo_error 'Please run as root'
    return 1
  fi

  install
}

# main
main

exit $?
