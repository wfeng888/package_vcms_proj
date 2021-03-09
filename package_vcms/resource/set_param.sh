#!/bin/bash
cur_dir=$(cd `dirname $0`;pwd) 
source ${cur_dir}/predefine.sh

pname_mysql_user="mysql_user"
pname_mysql_passwd="mysql_passwd"
pname_sync_ip="mysql_sync_ip"
pname_sync_port="mysql_sync_port"
pname_mysql_software_base="mysql_software_base"
pname_ignore_error="ignore_error"
pname_mysql_socket="mysql_socket"


mysql_user=`get_command_value "$1"  ${pname_mysql_user}  ${config_file}`
mysql_passwd=`get_command_value "$2"    ${pname_mysql_passwd}  ${config_file}`
mysql_sync_ip=`get_command_value "$3"    ${pname_sync_ip}  ${config_file}`
mysql_sync_port=`get_command_value "$4"    ${pname_sync_port}  ${config_file}`
mysql_software_base=`get_command_value "$5"    ${pname_mysql_software_base}  ${config_file}`
ignore_error=`get_command_value "$6"    ${pname_ignore_error}  ${config_file}`
mysql_socket=`get_command_value "$7"    ${pname_mysql_socket}  ${config_file}`
mysql="${mysql_software_base}/bin/mysql"
sqllog="${cur_dir}/exec-sql-log-${cur_time}.log"
login=`get_login_cmd "${mysql}"  "${mysql_user}" "${mysql_passwd}"  "${mysql_sync_ip}"  "${mysql_sync_port}" "${mysql_socket}"`