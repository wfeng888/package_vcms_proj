import logging
import os
import sys
from os import path
import subprocess
from configparser import ConfigParser
from shutil import copytree,rmtree,copyfile
from time import sleep


from package_vcms import Config, SvnDownloadException, MergeSqlFileException, CURRENT_DIR, record_log, \
    ConfigFileException, IncorrectOSUser, MysqlRunningException, WIN
from package_vcms.git_tools import Mgit
from package_vcms.merge import merge_sql
from package_vcms.platform_func import platform_functool
from package_vcms.utils import formatDate, formatDateTime, to_text, none_null_stringNone, getLine, path_join

logger = logging.getLogger('packaging')

class Packaging():
    STAGE_DOWNLOAD_REPO=1
    STAGE_INIT_SEEDDB=2
    def __init__(self):
        cp = ConfigParser(allow_no_value=True)
        cp.read(path.join(CURRENT_DIR,'config.ini'),encoding='utf-8')
        self.config = Config()
        self.config.setData(cp)
        if not self.config.work_dir:
            self.config.work_dir = CURRENT_DIR
        self.config.mysql_install_shell = path.abspath(path.join(CURRENT_DIR,*(Config._INSTALL_SCRIPT,)))
        if not none_null_stringNone(self.config.log_level) and logging._nameToLevel.get(self.config.log_level.upper(),None):
            logging.getLogger().setLevel(logging._nameToLevel[self.config.log_level.upper()])
        if not self.config.check():
            raise  ConfigFileException()
        #self.lang
        # 1 en
        # 0 zh
        self.lang = 1 if self.config.database_lang and self.config.database_lang.lower() == 'en' else 0
        logger.debug(self.config)
        self._startProcess = None

    def prepare(self):
        if not os.path.exists(self.config.work_dir):
            os.mkdir(self.config.work_dir)
        self.config.work_dir_new = path.join(self.config.work_dir,formatDateTime())
        os.mkdir(self.config.work_dir_new)
        #看看是否要拉取repo代码
        if (self.STAGE_DOWNLOAD_REPO != self.config.stage & self.STAGE_DOWNLOAD_REPO):
            _mgit = Mgit(self.config)
            _mgit.clone()
            self.config.mysql_sql_script_base_dir = path_join(self.config.work_dir_new,('DB','mysql','scimdb_objects'))
            self.config.download_repo = True
        self.config.package_name = self.config.mysql_packaging_name.format(platform=platform_functool.plat_form,date=formatDate(), \
                                                                lang='english' if self.config.database_lang and self.config.database_lang.lower()=='en' else 'chinese', \
                                                                type=self.config.package_type)
    def packaging(self):
        self.prepare()
        if not merge_sql(self.config.mysql_sql_script_base_dir,self.lang):
            logger.error('MergeSqlFileException')
            raise MergeSqlFileException()
        os.chdir(self.config.work_dir_new)
        if Config._PACKAGE_TYPE_SYNC == self.config.package_type:
            #将合并之后的几个sql脚本copy出来，放入到打包目录中
            sql_files=[path.join('tables','table_shell_merge_mysql.sql'),path.join('views','views_shell_merge_mysql.sql') \
                ,path.join('triggers','triggers_shell_merge_mysql.sql'),path.join('procedure','procedures_functions_shell_merge_mysql.sql')]
            if self.lang == 1:
                sql_files.append(path.join('db_basic_data_en','basic_data_shell_merge_mysql.sql'))
            else:
                sql_files.append(path.join('db_basic_data','basic_data_shell_merge_mysql.sql'))
            _work_dir = path_join(self.config.work_dir_new,self.config.package_name)
            for i in sql_files:
                copyfile(path_join(self.config.mysql_sql_script_base_dir,i),path_join(_work_dir,path.split(i)[1]))
            with open(path_join(_work_dir,'config.param'),'r',encoding='utf8') as f:
                f.writelines(('mysql_sync_ip=','mysql_sync_port=','mysql_user=','mysql_passwd=','mysql_software_base=','ignore_error=Y','mysql_socket='))
                f.flush()
            #将shell安装脚本copy到安装包中
            copytree(path_join(CURRENT_DIR,'resource'),_work_dir)
        else:
            if  self.check_mysql_alive():
                # 如果mysql进程存在，检查一下运行中的mysql进程是否与配置的打包目录一致
                if not self._checkSeedCorrect():
                    logger.error('current active mysqld process is not the seed database. abort! ')
                    raise IncorrectOSUser()
            else:
                # 如果mysql进程没有运行，这里尝试启动一下
                logger.error('mysql not running , start')
                self._startProcess = self._startMysql()
                self._wait_until_alive()
                if not self.check_mysql_alive():
                    logger.error('mysql not running and start failed, abort it! ')
                    raise MysqlRunningException()
            self._deploy_sql(sql='drop database if exists usmsc;drop database if exists usmschis;drop database if exists activiti;')
            self._install_sql()
            self._stopMysql()

            copytree(self.config.mysql_seed_database_base,path.join(self.config.work_dir_new,self.config.package_name),symlinks=True)
            copyfile(self.config.mysql_install_shell,path.join(self.config.work_dir_new,path.split(self.config.mysql_install_shell)[1]))
            # 删除log目录下，除log.err之外的其它日志文件
            logger.debug(path.join(self.config.work_dir_new,self.config.package_name,'log','*'))
            _logdir = path.join(self.config.work_dir_new,self.config.package_name,'log')
            logger.debug('logdir= %s'%_logdir)
            _dellist = [path.join(_logdir,i) for i in os.listdir(_logdir) if '.err' != path.splitext(i)[1]]
            # 删除data目录下的redo日志文件，节省打包空间
            _datadir = path.join(self.config.work_dir_new,self.config.package_name,'data')
            _dellist.append(path_join(_datadir,'ib_logfile*',path.sep))
            #真正删除的地方
            platform_functool.removeFile(filelist=_dellist)
        #先打一个tar包
        logger.debug('package %s'% self.config.package_name+'.tar')
        platform_functool.tar(self.config.package_name+'.tar',(self.config.package_name,))
        #再打一个gz包，别问为什么，安装脚本里面写死了要处理的是tar包，不是gz包
        logger.debug('package %s'% self.config.package_name+'.tar.gz')
        platform_functool.gz(self.config.package_name+'.tar.gz',(self.config.package_name+'.tar',path.split(self.config.mysql_install_shell)[1]))
        if Config._PACKAGE_TYPE_DB == self.config.package_type:
            #copy到打包目录的shell文件不要了，删掉
            logger.debug('remove %s' % path.split(self.config.mysql_install_shell)[1])
            os.remove(path.split(self.config.mysql_install_shell)[1])
        #tar包用完了，删掉
        logger.debug('remove %s'%self.config.package_name+'.tar')
        os.remove(self.config.package_name+'.tar')
        #工作目录中的打包文件也不用了，删掉
        logger.debug('remove %s'%self.config.package_name)
        rmtree(self.config.package_name)

        #将最后的gz包copy到latest文件夹下，方便进一步处理
        if not os.path.exists(path.join(self.config.work_dir,'latest')):
            os.mkdir(path.join(self.config.work_dir,'latest'))
        platform_functool.removeFile(filelist=(path_join(self.config.work_dir,('latest','*'),path.sep),))
        copyfile(path.join(self.config.work_dir_new,'%s.tar.gz'%self.config.package_name),path.join(self.config.work_dir,'latest','%s.tar.gz'%self.config.package_name))

    # @record_log
    # def _deploy_sql(self,sqlfile=None,sql=None,dbname=None):
    #     cmd = self.config.mysql_software_path + ' ' + '-u' + self.config.mysql_conn_username + ' '
    #     if self.config.mysql_conn_password:
    #         cmd += ' ' + '-p' + self.config.mysql_conn_password
    #     cmd += ' ' + '-P' + str(self.config.mysql_conn_port) + ' ' + '-hlocalhost --protocol=tcp '
    #     if dbname:
    #         cmd += ' ' + '-D' + dbname
    #     if sqlfile:
    #         cmd += ' ' + '-f' + ' ' + '<' + sqlfile
    #     elif sql:
    #         cmd +=  ' -N -e "' + ' ' + sql + '"'
    #     else:
    #         return None
    #     logger.debug('execute %s'%cmd)
    #     res = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')
    #     return res
    #
    # @record_log
    # def _install_sql(self):
    #     sql_files=[path.join('tables','table_shell_merge_mysql.sql'),path.join('views','views_shell_merge_mysql.sql')\
    #                ,path.join('triggers','triggers_shell_merge_mysql.sql'),path.join('procedure','procedures_functions_shell_merge_mysql.sql')]
    #     if self.lang == 1:
    #         sql_files.append(path.join('db_basic_data_en','basic_data_shell_merge_mysql.sql'))
    #     else:
    #         sql_files.append(path.join('db_basic_data','basic_data_shell_merge_mysql.sql'))
    #     res = self._deploy_sql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,'init_db.sql'))
    #     if getattr(res,'stderr'):
    #         logger.error(res.stderr)
    #     for file in sql_files:
    #         logger.info('execute %s'%file)
    #         res = self._deploy_sql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,file),dbname='usmsc')
    #         if getattr(res,'stderr'):
    #             logger.error(res.stderr)
    #
    # def _getOutput(self,cmd):
    #     res = self._deploy_sql(sql=cmd)
    #     logger.debug(getLine(res.stdout))
    #     return getLine(res.stdout)
    #
    # def _getVar(self,varname):
    #     return self._getOutput(cmd='select @@' + varname + ' ; ')
    #
    # def _wait_until_timeout(self,func,timeout=30):
    #     increment = 5
    #     while( timeout > 0 and func()):
    #         timeout -= increment
    #         sleep(increment)
    #
    # @record_log
    # def _wait_until_shutdown(self,timeout=30):
    #     def _isShutdown():
    #         return not platform_functool.portBusy(self.config.mysql_conn_port)
    #     self._wait_until_timeout(_isShutdown,timeout)
    #
    # def check_mysql_alive(self):
    #     res = self._getOutput('select 1;')
    #     logger.debug(res)
    #     if '1' == res :
    #         return True
    #     return False
    #
    # def _wait_until_alive(self):
    #     def _isAlive():
    #         return not self.check_mysql_alive()
    #     self._wait_until_timeout(_isAlive)
    #
    # def _checkSeedCorrect(self):
    #     return self._getVar('datadir').startswith(self.config.mysql_seed_database_base)
    #
    # def _startMysql(self):
    #     cnf = path.join(self.config.mysql_seed_database_base,'my.cnf')
    #     if WIN:
    #         mysqld = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld')
    #         return subprocess.Popen([mysqld,'--defaults-file=' + cnf],shell=True,encoding='utf8')
    #     else:
    #         mysqld_safe = path.join(self.config.mysql_software_path.rpartition(os.path.sep)[0],'mysqld_safe')
    #         return subprocess.Popen([mysqld_safe,'--defaults-file=' + cnf + ' & '],shell=True,encoding='utf8')
    #
    # def _stopMysql(self):
    #     self._deploy_sql(sql=' set global innodb_fast_shutdown=0;')
    #     self._deploy_sql(sql=' shutdown;')
    #     self._wait_until_shutdown()
    #     # 这里记得停掉mysql的启动进程，否则因为子进程不会结束导致程序不能正常退出
    #     if self._startProcess:
    #         self._startProcess.kill()
    #         self._startProcess = None

