import logging
import os
import subprocess
import time
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
        return not utils.IsOpen(self.config.mysql_conn_port)


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
    def waitUntilShutdown(self,timeout=3600):
        utils.wait_until_timeout(lambda : self.isShutdown() ,timeout)

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
        _encoding = 'utf8'
        if WIN:
            _encoding = 'cp936'
        res = subprocess.run(cmd,capture_output=True,shell=True,encoding=_encoding)
        return res

    @record_log
    def getVar(self,varname):
        return self.getOutput(cmd='select @@' + varname + ' ; ')

    @record_log
    def startService(self):
        logger.info('start Mysql Database. ')
        cnf = path.join(self.config.mysql_seed_database_base,self.config.cnf_name)
        if WIN:
            mysqld = path.join(path.dirname(self.config.mysql_software_path),'mysqld')
            return subprocess.Popen([mysqld,'--defaults-file=' + cnf],shell=False,encoding='utf8')
        else:
            mysqld_safe = path.join(path.dirname(self.config.mysql_software_path),'mysqld_safe')
            cmd='%s --defaults-file=%s &'%(mysqld_safe,cnf)
            self._startProcess = subprocess.Popen(cmd,shell=True,encoding='utf8')
            return self._startProcess

    @record_log
    def stopService(self):
        logger.info('stop Mysql database. ')
        self.execSql(sql=' set global innodb_fast_shutdown=0;')
        self.mysqladmin_oper('shutdown')
        #??????1s??????mysqld?????????????????????????????????????????????????????????????????????
        time.sleep(1)
        # self.waitUntilShutdown()
        # ??????????????????mysql?????????????????????????????????????????????????????????????????????????????????
        if self._startProcess:
            self._startProcess.kill()
            self._startProcess = None

    @record_log
    def mysqladmin_oper(self,cmd):
        mysqladmin = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqladmin')
        mysqladmin += ' ' + '-u' + self.config.mysql_conn_username + ' '
        if self.config.mysql_conn_password:
            mysqladmin += ' ' + '-p' + self.config.mysql_conn_password
        mysqladmin += ' ' + '-P' + str(self.config.mysql_conn_port) + ' ' + '-hlocalhost --protocol=tcp '
        mysqladmin += ' ' + cmd
        platform_functool.exec_shell_indnpnt(mysqladmin)

    @record_log
    def initService(self):
        mysqld = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld')
        # stdout = None
        # stderr = None
        # with subprocess.Popen([mysqld, '--defaults-file=' + self.config.mysql_cnf_path, '--initialize-insecure'],shell=False,encoding='utf8',stderr=subprocess.PIPE,stdout=subprocess.PIPE,user='mysql') as _process:
        #     try:
        #         stdout, stderr = _process.communicate()
        #     except subprocess.TimeoutExpired as exc:
        #         _process.kill()
        #         if WIN:
        #             # Windows accumulates the output in a single blocking
        #             # read() call run on child threads, with the timeout
        #             # being done in a join() on those threads.  communicate()
        #             # _after_ kill() is required to collect that and add it
        #             # to the exception.
        #             exc.stdout, exc.stderr = _process.communicate()
        #         else:
        #             # POSIX _communicate already populated the output so
        #             # far into the TimeoutExpired exception.
        #             _process.wait()
        #         raise
        #     except:  # Including KeyboardInterrupt, communicate handled that.
        #         _process.kill()
        #         # We don't call process.wait() as .__exit__ does that for us.
        #         raise
        #     retcode = _process.poll()

        _result: subprocess.CompletedProcess = subprocess.run([mysqld, '--defaults-file=' + self.config.mysql_cnf_path, '--initialize-insecure'], shell=False,encoding='utf8')
        if _result.stdout:
            logger.info(utils.getLine(_result.stdout))
        if _result.stderr:
            logger.info(utils.getLine(_result.stderr))
        logger.info(_result.returncode)
        _result.check_returncode()
        assert _result.returncode == 0



