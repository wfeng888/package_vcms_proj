#! /bin/bash

check_port_busy(){
#1 mysql_port
[ `netstat -apn|grep -w ${1}|wc -l ` -gt 0 ] && return 1
return 0
}

##################################################
##      mysql_5_22的linux一键安装脚本
##      create by wlc
##      date：2018/05/28
##      注意：确定是root用户，.sh有x权限,将
##            sh文件与安装包放在同一目录下
##################################################

check_port_busy 8306
[ `$?` == 1 ] && echo " mysql port 8306 must be busy. please deal with this. install abort!!!!!!" && exit 1

#1、打开当前文件夹
export curdir=$(cd `dirname $0`;pwd)
cd $curdir
#2、列出当前文件夹下mysql5.7的安装包
export mysql_tar_file=`ls mysql-*-VCMS-*\.tar | awk '{print $1}'`
export basic_dir=$curdir/mysql
export mysql_root=$curdir
export mycnf_file=/etc

mkdir -p $mysql_root
cd $mysql_root

#3、判断mysql目录是否存在，如果已经存在，则认为数据库已经安装
if [ -d "$mysql_root/mysql" ]
then
        echo "***************************************************"
        echo "**   mysql service is exist,now, restarting ...  **"
        echo "***************************************************"
        service mysqld restart
        exit
fi

#4、解压安装包
echo "**************************************************"
echo "**   Unzip mysql install file,please wait ...   **"
echo "**************************************************"

tar -xpf $mysql_tar_file -C$mysql_root/
export mysql_dir_name=`ls -F |grep '/$' |grep 'mysql-5.7'`

if [ -d "$mysql_dir_name" ]
then
        mv $mysql_dir_name  mysql
fi

#5、生成配置文件
if [ -s /etc/my.cnf ]
then
        mv /etc/my.cnf /etc/my.cnf.`date +%Y%m%d%H%M`.bak
fi

echo "**************************************************"
echo "** create my.cnf ...                            **"
echo "**************************************************"

mkdir -p $basic_dir/tmp

cat > "$mycnf_file/my.cnf" <<EOF
[client]
socket="${basic_dir}/mysql.sock"
[mysql]
default-character-set=utf8
[mysqld]
lower_case_table_names=1
port=8306
socket="${basic_dir}/var/mysql.sock"
basedir="${basic_dir}"
innodb_file_per_table=1
datadir="${basic_dir}/data"
character-set-server=utf8
default-storage-engine=INNODB
sql-mode=STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION
innodb_log_buffer_size=64M
max_connections=1000
query_cache_size=0
tmp_table_size=128M
thread_cache_size=64
myisam_max_sort_file_size=10G
myisam_sort_buffer_size=30M
key_buffer_size=128M
read_buffer_size=16M
read_rnd_buffer_size=32M
sort_buffer_size=32M
innodb_flush_log_at_trx_commit=1
innodb_buffer_pool_size=4096M
innodb_log_file_size=1024M
innodb_log_files_in_group=2
slow-query-log=1
long_query_time=2
slow_query_log_file="${basic_dir}/log/slow.log"
log_slow_slave_statements=ON
innodb_thread_concurrency=64
event_scheduler=on
bulk_insert_buffer_size=64M
expire-logs-days=60
sync_binlog=1
binlog_format=row
log-bin="${basic_dir}/log/binlog"
log-bin-index="${basic_dir}/log/binlog.index"
log_error="${basic_dir}/log/log.err"
relay_log="${basic_dir}/log/relay_log"
relay_log_index="${basic_dir}/log/relay_log.index"
general_log_file="${basic_dir}/log/general.log"
master_info_repository=TABLE
relay_log_info_repository=TABLE
max_allowed_packet=128M
max_binlog_size=1024M
sql_mode=NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER
show_compatibility_56=on
group_concat_max_len=102400
log_bin_trust_function_creators=1
server-id=1
auto-increment-increment=1
auto-increment-offset=1
EOF

cp "$mycnf_file/my.cnf"  "${basic_dir}/"

#5、添加组

export m_group=mysql
export m_user=mysql

egrep "^$m_group" /etc/group >& /dev/null
if [ $? -ne 0 ]
then
        groupadd $m_group
fi

egrep "^$m_user" /etc/passwd >& /dev/null
if [ $? -ne 0 ]
then
        useradd -g $m_group $m_user
fi

chown -R mysql:mysql mysql

#6、安装服务
#for i in `ps -ef |grep 8036 |awk '{print $2}'`
#do
#        if [ "$i" != "0" ]
#        then
#                kill -9 $i
#        else
#                echo "****************************************"
#                echo "**  mysql process 8306 is  not exist  **"
#                echo "****************************************"
#                echo
#        fi
#done
#实例化mysql
#$basic_dir/bin/mysqld --initialize-insecure --user=mysql --datadir=$basic_dir/data

echo "**************************************"
echo "**    install completed ...         **"
echo "**************************************"
echo

echo "**************************************"
echo "**    create env  ...            **"
echo "**************************************"
echo

echo "###########################################"      >>~/.bashrc
echo "##        add for mysql                  ##"      >>~/.bashrc
echo "###########################################"      >>~/.bashrc
echo "PATH=\$PATH:$basic_dir/bin"                       >>~/.bashrc

source ~/.bashrc

echo "**************************************"
echo "**    create auto run  ...          **"
echo "**************************************"
echo

#7、修改启动配置文件
cp $basic_dir/support-files/mysql.server /etc/rc.d/init.d/mysqld

sed -i "/basedir=$/cbasedir=$basic_dir"  /etc/rc.d/init.d/mysqld
sed -i "/datadir=$/cdatadir=$basic_dir/data" /etc/rc.d/init.d/mysqld

chmod +x /etc/rc.d/init.d/mysqld
chkconfig --add mysqld

#8、启动服务
echo "**************************************"
echo "**    start service  ...            **"
echo "**************************************"
echo
service mysqld  start

echo "**************************************"
echo "**   now,completed!!                **"
echo "**************************************"
echo
