@echo off
echo.
color 0A
echo *************************stop*************************
echo.
set /p input="Are you sure stop mysql service ??? Yes(y) or No(n): "
if /i "%input%"=="y"  (goto yes) else (if /i "%input%"=="yes" (goto yes) else (goto no))
:no
echo Operation Cancel ...
echo. 
echo *************************finish*************************
pause
exit

:yes
set MYSQL_HOME=%MYSQL_HOME%
echo MYSQL_HOME=%MYSQL_HOME%
cd %MYSQL_HOME%
echo stopping mysql service ...
net stop ZNV_MySQL
echo. 
echo *************************finish*************************
pause
exit

