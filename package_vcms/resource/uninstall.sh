#!/bin/bash
cur_dir=$(cd `dirname $0`;pwd)
source ${cur_dir}/set_param.sh
[ `check_mysql_alive` -gt 0 ] && echo "Error: mysql is not running !" && exit 1
exec_sql "drop database usmsc;drop database usmschis;drop database activiti;"