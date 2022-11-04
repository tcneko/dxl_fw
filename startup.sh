#!/bin/bash

# author: tcneko <tcneko@outlook.com>
# start from: 2022.11
# last test environment: ubuntu 20.04
# description:

export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# variables
ins_dir='/opt/sh/dxl_fw'
cfg_dir='/opt/sh/dxl_fw'

# function
main() {
  python3 ${ins_dir}/dxl_fw.py -c ${cfg_dir}/onetime.json
  python3 ${ins_dir}/dxl_fw.py -c ${cfg_dir}/runtime.json
}

# main
main

exit $?
