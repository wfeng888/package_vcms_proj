@echo off
color 0A
echo.
echo *************************change_password*************************
echo.
set /p input="Please ensure you have read the readme.txt !! Yes(y) or No(n): "
if /i "%input%"=="y" ( goto yes ) else ( if /i "%input%"=="yes" ( goto yes )  else (goto no) )
:no
echo please read the readme.txt first and then restart again ... 
echo.
echo *************************finish*************************
pause
exit

:yes
echo You are going to change user's password!
echo.
rem input user name
:inputuser_name
set /p modify_user="Please input the username which you want to change: "
if "%modify_user%A"=="A" ( echo username can not be null,input again &&  goto inputuser_name )

set /p rootpwd="Please input root's password: "

rem input newpwd
:gobacknewpwd
set /p newpwd="Please input %modify_user%'s new password:"
if "%newpwd%A"=="A" ( echo password can not be null,input again &&  goto gobacknewpwd )

:reinput_newpwd
set /p newpwd_adjust="Please input %modify_user%'s new password again:"
if "%newpwd_adjust%A" neq "%newpwd%A" ( echo password is not coincident,input again &&  goto gobacknewpwd )

echo please wait ...
set curdir_tmp=%MYSQL_HOME%
cd %curdir_tmp%
set curdir=%MYSQL_HOME%
set "curdir=%curdir:\\=\%"

rem 5.7版本 update user set authentication_string = password('root'),password_expired = 'N', password_last_changed = now() where user = 'root';
echo use mysql; >passwd_set_tmp.sql
echo update user set authentication_string=password('%newpwd%'),password_expired ='N', password_last_changed =now() where user='%modify_user%'; >>passwd_set_tmp.sql
echo commit;  >>passwd_set_tmp.sql
echo alter user '%modify_user%'@'^%%' identified by '%newpwd%'; >>passwd_set_tmp.sql
echo alter user '%modify_user%'@'localhost' identified by '%newpwd%'; >>passwd_set_tmp.sql
rem echo alter user 'root'@'localhost'  on *.* to root@'^%%' identified by '%newpwd%' with grant option; >>passwd_set_tmp.sql
rem echo flush privileges; >>passwd_set_tmp.sql
echo quit >>passwd_set_tmp.sql
echo.>>passwd_set_tmp.sql

echo. & timeout /t 3 > nul

%MYSQL_HOME%\bin\mysql.exe -uroot -p%rootpwd% -f < passwd_set_tmp.sql
net stop mysql
net start mysql

del /Q "%curdir%\passwd_set_tmp.sql"

echo Password Changed!!
echo.
echo *************************finish*************************
pause
exit

