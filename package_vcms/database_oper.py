import logging
import os
import subprocess
from abc import ABCMeta, abstractmethod
from sys import path

from package_vcms import utils, record_log, WIN

logger = logging.getLogger(__file__)
class DatabaseInterface(object,metaclass=ABCMeta):
    def __init__(self,pconfig,pplatformFunc):
        self.config = pconfig
        self.platformFunc = pplatformFunc
        self.lang = 1 if self.config.database_lang and self.config.database_lang.lower() == 'en' else 0

    @abstractmethod
    def startService(self):
        pass

    @abstractmethod
    def stopService(self):
        pass

    @abstractmethod
    def isAlive(self,url):
        pass

    @abstractmethod
    def portBusy(self,port):
        pass

    @abstractmethod
    def checkSeedCorrect(self):
        pass

    @abstractmethod
    def execSql(self,sqlfile=None,sql=None,dbname=None):
        pass

    @abstractmethod
    def getVar(self,varname):
        pass

    def waitUntilAlive(self):
        def _isAlive():
            return not self.isAlive()
        utils.wait_until_timeout(_isAlive)

    @record_log
    def waitUntilShutdown(self,timeout=30):
        def _isShutdown():
            return not self.platformFunc.portBusy(self.config.mysql_conn_port)
        utils.wait_until_timeout(_isShutdown,timeout)

    def getOutput(self,cmd):
        res = self.execSql(sql=cmd)
        logger.debug(utils.getLine(res.stdout))
        return utils.getLine(res.stdout)

    @abstractmethod
    def installSql(self):
        pass

    @abstractmethod
    def slimming(self):
        pass

class MysqlOper(DatabaseInterface):

    def __init__(self,*args,**kwargs):
        super(MysqlOper, self).__init__(*args,**kwargs)

    def execSql(self,sqlfile=None,sql=None,dbname=None):
        cmd = self.config.mysql_software_path + ' ' + '-u' + self.config.mysql_conn_username + ' '
        if self.config.mysql_conn_password:
            cmd += ' ' + '-p' + self.config.mysql_conn_password
        cmd += ' ' + '-P' + str(self.config.mysql_conn_port) + ' ' + '-hlocalhost --protocol=tcp '
        if dbname:
            cmd += ' ' + '-D' + dbname
        if sqlfile:
            cmd += ' ' + '-f' + ' ' + '<' + sqlfile
        elif sql:
            cmd +=  ' -N -e "' + ' ' + sql + '"'
        else:
            return None
        logger.debug('execute %s'%cmd)
        res = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')
        return res

    def getVar(self,varname):
        return self.getOutput(cmd='select @@' + varname + ' ; ')

    def startService(self):
        cnf = path.join(self.config.mysql_seed_database_base,'my.cnf')
        if WIN:
            mysqld = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld')
            self._startProcess = subprocess.Popen([mysqld,'--defaults-file=' + cnf],shell=True,encoding='utf8')
            return self._startProcess
        else:
            mysqld_safe = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld_safe')
            self._startProcess = subprocess.Popen([mysqld_safe,'--defaults-file=' + cnf + ' & '],shell=True,encoding='utf8')
            return self._startProcess

    def stopService(self):
        self.execSql(sql=' set global innodb_fast_shutdown=0;')
        self.execSql(sql=' shutdown;')
        self.waitUntilShutdown()
        # 这里记得停掉mysql的启动进程，否则因为子进程不会结束导致程序不能正常退出
        if self._startProcess:
            self._startProcess.kill()
            self._startProcess = None

    def checkSeedCorrect(self):
        return self.getVar('datadir').startswith(self.config.mysql_seed_database_base)

    def installSql(self):
        sql_files=[path.join('tables','table_shell_merge_mysql.sql'),path.join('views','views_shell_merge_mysql.sql') \
            ,path.join('triggers','triggers_shell_merge_mysql.sql'),path.join('procedure','procedures_functions_shell_merge_mysql.sql')]
        if self.lang == 1:
            sql_files.append(path.join('db_basic_data_en','basic_data_shell_merge_mysql.sql'))
        else:
            sql_files.append(path.join('db_basic_data','basic_data_shell_merge_mysql.sql'))
        res = self.execSql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,'init_db.sql'))
        if getattr(res,'stderr'):
            logger.error(res.stderr)
        for file in sql_files:
            logger.info('execute %s'%file)
            res = self.execSql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,file),dbname='usmsc')
            if getattr(res,'stderr'):
                logger.error(res.stderr)

