import logging
import os
import subprocess
from abc import ABCMeta, abstractmethod
from os import path

from package_vcms import utils, record_log, WIN
from package_vcms.platform_func import platform_functool

logger = logging.getLogger(__file__)
class DatabaseInterface(object,metaclass=ABCMeta):
    def __init__(self,pconfig):
        self.config = pconfig
        self.lang = 1 if self.config.database_lang and self.config.database_lang.lower() == 'en' else 0

    @abstractmethod
    def startService(self):
        pass

    @abstractmethod
    def stopService(self):
        pass

    @record_log
    def isAlive(self):
        res = self.getOutput('select 1 from dual')
        logger.debug(res)
        if '1' == res :
            return True
        return False

    @record_log
    def isShutdown(self):
        return not platform_functool.portBusy(self.config.mysql_conn_port)


    @abstractmethod
    def execSql(self,sqlfile=None,sql=None,dbname=None):
        pass

    @abstractmethod
    def getVar(self,varname):
        pass

    @record_log
    def waitUntilAlive(self):
        # def _isAlive():
        #     return not self.isAlive()
        utils.wait_until_timeout(self.isAlive)

    @record_log
    def waitUntilShutdown(self,timeout=30):
        utils.wait_until_timeout(lambda : not self.isShutdown() ,timeout)

    @record_log
    def getOutput(self,cmd):
        res = self.execSql(sql=cmd)
        logger.debug(utils.getLine(res.stdout))
        return utils.getLine(res.stdout)

    @abstractmethod
    def initService(self):
        pass


class MysqlOper(DatabaseInterface):

    def __init__(self,pconfig):
        super(MysqlOper, self).__init__(pconfig)
        self._startProcess = None

    @record_log
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

    @record_log
    def getVar(self,varname):
        return self.getOutput(cmd='select @@' + varname + ' ; ')

    @record_log
    def startService(self):
        logger.info('start Mysql Database. ')
        cnf = path.join(self.config.mysql_seed_database_base,'my.cnf')
        if WIN:
            mysqld = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld')
            self._startProcess = subprocess.Popen([mysqld,'--defaults-file=' + cnf],shell=True,encoding='utf8')
            return self._startProcess
        else:
            mysqld_safe = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld_safe')
            self._startProcess = subprocess.Popen([mysqld_safe,'--defaults-file=' + cnf + ' & '],shell=True,encoding='utf8')
            return self._startProcess

    @record_log
    def stopService(self):
        logger.info('stop Mysql database. ')
        self.execSql(sql=' set global innodb_fast_shutdown=0;')
        self.execSql(sql=' shutdown;')
        self.waitUntilShutdown()
        # 这里记得停掉mysql的启动进程，否则因为子进程不会结束导致程序不能正常退出
        if self._startProcess:
            self._startProcess.kill()
            self._startProcess = None



    @record_log
    def initService(self):




