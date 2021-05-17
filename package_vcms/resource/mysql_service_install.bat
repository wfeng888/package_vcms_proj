@echo off
color 0A
echo.
:before
echo *************************install*************************
echo.
set /p input="Please read the readme.txt first !!! Yes(y) or No(n):"
if /i "%input%"=="y" (goto yes) else (if /i "%input%"=="yes" (goto yes) else (goto no))

:no
echo please read the file "readme.txt" first and then restart again ...
echo.
echo *************************finish*************************
pause
exit

:yes
cd /d %~dp0
if "%1X"=="X" (set curr_path=%CD%) else (set curr_path=%1)
set curdir_tmp=%curr_path%
cd /d %curdir_tmp%
set curdir=%curdir_tmp%
set "curdir=%curdir:\=\\%"


echo [client]                                                                       >"%curdir_tmp%\my.ini"
echo port=8306                                                                      >>"%curdir_tmp%\my.ini"
echo.                                                                               >>"%curdir_tmp%\my.ini"

echo [mysql]                                                                        >>"%curdir_tmp%\my.ini"
echo default-character-set=utf8                                                     >>"%curdir_tmp%\my.ini"
echo.                                                                               >>"%curdir_tmp%\my.ini"

echo [mysqld]                                                                       >>"%curdir_tmp%\my.ini"
echo port=8306                                                                      >>"%curdir_tmp%\my.ini"
echo basedir="%curdir%"                                                             >>"%curdir_tmp%\my.ini"
echo innodb_file_per_table=1                                                        >>"%curdir_tmp%\my.ini"
echo datadir="%curdir%\\Data\\"                                                     >>"%curdir_tmp%\my.ini"
echo character-set-server=utf8                                                      >>"%curdir_tmp%\my.ini"
echo server-id=1                                                                    >>"%curdir_tmp%\my.ini"
echo default-storage-engine=INNODB                                                  >>"%curdir_tmp%\my.ini"
echo sql-mode="STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION"      >>"%curdir_tmp%\my.ini"
echo max_connections=3000                                                           >>"%curdir_tmp%\my.ini"
echo query_cache_size=0                                                             >>"%curdir_tmp%\my.ini"
echo tmp_table_size=64M                                                             >>"%curdir_tmp%\my.ini"
echo thread_cache_size=8                                                            >>"%curdir_tmp%\my.ini"
echo myisam_max_sort_file_size=100G                                                 >>"%curdir_tmp%\my.ini"
echo myisam_sort_buffer_size=30M                                                    >>"%curdir_tmp%\my.ini"
echo key_buffer_size=128M                                                           >>"%curdir_tmp%\my.ini"
echo read_buffer_size=64K                                                           >>"%curdir_tmp%\my.ini"
echo read_rnd_buffer_size=256K                                                      >>"%curdir_tmp%\my.ini"
echo sort_buffer_size=512K                                                          >>"%curdir_tmp%\my.ini"
echo innodb_flush_log_at_trx_commit=1                                               >>"%curdir_tmp%\my.ini"
echo innodb_log_buffer_size=16M                                                      >>"%curdir_tmp%\my.ini"
echo innodb_buffer_pool_size=2048M                                                  >>"%curdir_tmp%\my.ini"
echo group_concat_max_len=102400                                                    >>"%curdir_tmp%\my.ini"
echo innodb_log_file_size=512M                                                      >>"%curdir_tmp%\my.ini"
echo innodb_log_files_in_group=2                                                    >>"%curdir_tmp%\my.ini"
echo innodb_thread_concurrency=32                                                   >>"%curdir_tmp%\my.ini"
echo event_scheduler=on                                                             >>"%curdir_tmp%\my.ini"
echo bulk_insert_buffer_size = 64M                                                  >>"%curdir_tmp%\my.ini"
echo max_allowed_packet = 64M                                                       >>"%curdir_tmp%\my.ini"
echo sql_mode=NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER        >>"%curdir_tmp%\my.ini"
echo show_compatibility_56=on                                                       >>"%curdir_tmp%\my.ini"
echo slow-query-log=On                                                              >>"%curdir_tmp%\my.ini"
echo slow_query_log_file="%curdir%\\mysqlslowquery.log"                             >>"%curdir_tmp%\my.ini"
echo log_queries_not_using_indexes=OFF                                              >>"%curdir_tmp%\my.ini"
echo log_error="%curdir%\\log.err"                                                  >>"%curdir_tmp%\my.ini"
echo long_query_time=10                                                             >>"%curdir_tmp%\my.ini"
echo binlog_format=ROW                                                              >>"%curdir_tmp%\my.ini"
echo expire_logs_days=60                                                            >>"%curdir_tmp%\my.ini"
echo log_bin="%curdir%\\log\\binlog"                                                >>"%curdir_tmp%\my.ini"
echo log_bin_index="%curdir%\\log\\binlog.index"                                    >>"%curdir_tmp%\my.ini"
echo relay_log="%curdir%\\Data\\log\\relay_log"                                     >>"%curdir_tmp%\my.ini"
echo relay_log_index="%curdir%\\log\\relay_log.index"                               >>"%curdir_tmp%\my.ini"
echo relay_log_info_file="%curdir%\\log\\relay-log.info"                            >>"%curdir_tmp%\my.ini"
echo log_slave_updates=OFF                                                          >>"%curdir_tmp%\my.ini"
echo log_slow_slave_statements=ON                                                   >>"%curdir_tmp%\my.ini"
echo skip-slave-start                                                               >>"%curdir_tmp%\my.ini"
echo master_info_repository=TABLE                                                   >>"%curdir_tmp%\my.ini"
echo relay_log_info_repository=TABLE                                                >>"%curdir_tmp%\my.ini"
echo sync_binlog=1                                                                  >>"%curdir_tmp%\my.ini"
echo read_only=OFF                                                                  >>"%curdir_tmp%\my.ini"
echo super_read_only=OFF                                                            >>"%curdir_tmp%\my.ini"
echo log-bin-trust-function-creators=ON                                             >>"%curdir_tmp%\my.ini"



echo installing mysql server ...
echo. & timeout /t 3 > nul

setx MYSQL_HOME "%curdir%"
setx /M MYSQL_HOME "%curdir%"
setx /M Path "%Path%;%curdir%\\bin"

rem 安装服务
%curdir%\bin\mysqld.exe --install ZNV_MySQL --defaults-file=%curdir%\my.ini

rem 初始化数据库用户
%curdir%\bin\mysqld.exe  --initialize-insecure --console

rem 启动服务
echo starting mysql server ...
net start ZNV_MySQL
echo.
echo *************************finish*************************
pause
exit