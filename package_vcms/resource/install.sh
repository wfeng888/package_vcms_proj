#!/bin/bash
cur_dir=$(cd `dirname $0`;pwd) 
source ${cur_dir}/set_param.sh
have_done="${cur_dir}/have_done_${cur_time}"
cat /dev/null > ${have_done}
[ `check_mysql_alive` -gt 0 ] && echo "Error: mysql is not running !" && exit 1
exec_sql "source init_db.sql"
for filename in 'table_shell_merge_mysql.sql' 'views_shell_merge_mysql.sql' \
'triggers_shell_merge_mysql.sql' 'procedures_functions_shell_merge_mysql.sql' 'basic_data_shell_merge_mysql.sql'
do
exec_sql "use usmsc ; source ${filename}"
check_sql_exec_result
if [ $? -eq 0 ] ; then 
    echo "$filename" >> ${have_done}
else
    [ `echo "${ignore_error}X"|tr a-z A-Z` != 'YX' ] && echo "$filename install failed ! " && exit 1
fi
done
exit 0