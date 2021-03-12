@echo off
echo.

echo removing mysql service ,please wait ...
set MYSQL_HOME=%MYSQL_HOME%
echo MYSQL_HOME=%MYSQL_HOME%
rem cd %curdir% 
net stop ZNV_MySQL
%MYSQL_HOME%\bin\mysqld.exe --remove ZNV_MySQL 
echo.
echo *************************finish*************************

exit
