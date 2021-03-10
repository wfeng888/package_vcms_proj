import logging
import os
import subprocess
from abc import ABCMeta, abstractmethod
from os import path
from shutil import copyfile, copytree, rmtree

from package_vcms import STAGE_DOWNLOAD_REPO, MergeSqlFileException, CURRENT_DIR, MysqlRunningException, \
    IncorrectOSUser, STAGE_INIT_SEEDDB, record_log
from package_vcms.database_oper import MysqlOper
from package_vcms.git_tools import Mgit
from package_vcms.merge import merge_sql
from package_vcms.platform_func import platform_functool
from package_vcms.utils import path_join

logger = logging.getLogger(__file__)

class Build(object,metaclass=ABCMeta):

    _PACKAGE_TYPE_DB='DB'
    _PACKAGE_TYPE_SYNC='SYNC'

    def __init__(self,pconfig):
        self.config = pconfig

    @abstractmethod
    def buildPackege(self):
        pass

    @abstractmethod
    def buildSyncPackage(self):
        pass

    @record_log
    def build(self):
        if Build._PACKAGE_TYPE_SYNC == self.config.package_type:
            self.buildSyncPackage()
        else:
            self.buildPackege()

    @record_log
    def downloadRepo(self):
        #看看是否要拉取repo代码
        if not (self.config.stage & STAGE_DOWNLOAD_REPO):
            self.config.repo_basedir = path.join(self.config.work_dir_new,'repo')
            _mgit = Mgit(self.config)
            _mgit.clone()
            self.config.download_repo = True



class BuildMysql(Build):
    _INSTALL_SCRIPT='install_mysql_57.sh'
    _SYNC_INSTALL_SCRIPT='install.sh'
    _SYNC_CHECK_SCRIPT='check.sh'
    _SYNC_PREDEFINE_SCRIPT='predefine.sh'
    _SYNC_SET_PARAM='set_param.sh'
    def __init__(self,pconfig):
        super(BuildMysql, self).__init__(pconfig)
        #self.lang
        # 1 en
        # 0 zh
        self._lang = 1 if self.config.database_lang and self.config.database_lang.lower() == 'en' else 0
        self._startProcess = None
        self._mysqlOper = MysqlOper(pconfig)
        self._sqlScriptsList:list = None

    @record_log
    def downloadRepo(self):
        super(BuildMysql, self).downloadRepo()
        if self.config.download_repo:
            self.config.mysql_sql_script_base_dir = path_join(self.config.repo_basedir,('mysql','scimdb_objects'))


    @record_log
    def _mergeSql(self):
        if not merge_sql(self.config.mysql_sql_script_base_dir,self._lang):
            logger.error('MergeSqlFileException')
            raise MergeSqlFileException()

    @record_log
    def _initDB(self):
        if (not self.config.stage & STAGE_INIT_SEEDDB):
            #将mysql软件gz包解压到work_new目录，并在其中创建data、var、log目录
            subprocess.run()
            #生成my.cnf配置文件
            #初始化数据库，initialize_insecure、创建用户
            #使用新值重置config中的配置变量
            pass


    @record_log
    def _getSQLScripts(self):
        self._sqlScriptsList = ['init_db.sql', \
                                path.join('tables','table_shell_merge_mysql.sql'), \
                                path.join('views','views_shell_merge_mysql.sql') , \
                                path.join('triggers','triggers_shell_merge_mysql.sql'), \
                                path.join('procedure','procedures_functions_shell_merge_mysql.sql') \
                                ]
        if self._lang == 1:
            self._sqlScriptsList.append(path.join('db_basic_data_en','basic_data_shell_merge_mysql.sql'))
        else:
            self._sqlScriptsList.append(path.join('db_basic_data','basic_data_shell_merge_mysql.sql'))

    @record_log
    def _prepare(self):
        os.chdir(self.config.work_dir_new)
        self.downloadRepo()
        self._mergeSql()
        self._getSQLScripts()
        self._initDB()

    @record_log
    def buildSyncPackage(self):
        logger.info('buil')
        self._prepare()
        os.mkdir(self.config.package_dir)
        for i in self._sqlScriptsList:
            copyfile(path_join(self.config.mysql_sql_script_base_dir,i),path_join(self.config.package_dir,path.split(i)[1]))
        #生成一个安装配置文件,这个给shell脚本使用
        with open(path_join(self.config.package_dir,'config.param'),'xt',encoding='utf8') as f:
            for i in ('mysql_sync_ip=','mysql_sync_port=','mysql_user=','mysql_passwd=','mysql_software_base=','ignore_error=Y','mysql_socket='):
                f.write(i+'\n')
            f.flush()
        #生成一个安装配置文件,这个给python脚本使用
        with open(path_join(self.config.package_dir,'config.ini'),'xt',encoding='utf8') as f:
            for i in ('[install]','mysql_sync_ip=','mysql_sync_port=','mysql_user=','mysql_passwd=','mysql_software_base=','ignore_error=Y','mysql_socket='):
                f.write(i+'\n')
            f.flush()
        #将shell安装脚本copy到安装包中
        for i in [BuildMysql._SYNC_CHECK_SCRIPT,BuildMysql._SYNC_INSTALL_SCRIPT,BuildMysql._SYNC_PREDEFINE_SCRIPT, \
                                 BuildMysql._SYNC_SET_PARAM]:
            copyfile(path.join(CURRENT_DIR,'resource',i),path.join(self.config.package_dir,i))
        #切换到打包目录
        os.chdir(self.config.work_dir_new)
        #直接打一个gz包
        logger.debug('package %s'% self.config.package_name+'.tar.gz')
        platform_functool.gz(self.config.package_name+'.tar.gz',(self.config.package_name,))
        #工作目录中的打包文件不用了，删掉
        logger.debug('remove %s'%self.config.package_name)
        rmtree(self.config.package_name)

    @record_log
    def _checkSeedCorrect(self):
        return self._mysqlOper.getVar('datadir').startswith(self.config.mysql_seed_database_base)


    @record_log
    def _installSql(self):
        for file in self._sqlScriptsList:
            logger.info('execute %s'%file)
            res = self._mysqlOper.execSql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,file),dbname= None if file == 'init_db.sql' else 'usmsc' )
            if getattr(res,'stderr'):
                logger.error(res.stderr)


    @record_log
    def buildPackege(self):
        self._prepare()
        if self._mysqlOper.isShutdown():
            # 如果mysql进程没有运行，这里尝试启动一下
            logger.error('mysql not running , start')
            self._startProcess = self._mysqlOper.startService()
            self._mysqlOper.waitUntilAlive()
            if not self._mysqlOper.isAlive():
                logger.error('mysql not running and start failed, abort it! ')
                raise MysqlRunningException()
        #检查一下运行中的mysql进程是否与配置的打包目录一致
        if not self._checkSeedCorrect():
            logger.error('current active mysqld process is not the seed database. abort! ')
            raise IncorrectOSUser()
        logger.info('drop exists database. ')
        self._mysqlOper.execSql(sql='drop database if exists usmsc;drop database if exists usmschis;drop database if exists activiti;')
        logger.info('install scripts. ')
        self._installSql()
        logger.info('stop mysql process. ')
        self._mysqlOper.stopService()
        logger.info('copy packaing file. ')
        copytree(self.config.mysql_seed_database_base,self.config.package_dir,symlinks=True)
        copyfile(path.join(CURRENT_DIR,'resource',BuildMysql._INSTALL_SCRIPT),path.join(self.config.work_dir_new,BuildMysql._INSTALL_SCRIPT))
        # 删除log目录下，除log.err之外的其它日志文件
        logger.debug(path.join(self.config.package_dir,'log','*'))
        _logdir = path.join(self.config.package_dir,'log')
        logger.debug('logdir= %s'%_logdir)
        _dellist = [path.join(_logdir,i) for i in os.listdir(_logdir) if '.err' != path.splitext(i)[1]]
        # 删除data目录下的redo日志文件，节省打包空间
        _datadir = path.join(self.config.package_dir,'data')
        _dellist.append(path_join(_datadir,'ib_logfile*',path.sep))
        #真正删除的地方
        platform_functool.removeFile(filelist=_dellist)
        #切换到打包目录
        os.chdir(self.config.work_dir_new)
        logger.info('start packaging. ')
        #先打一个tar包
        logger.debug('package %s'% self.config.package_name+'.tar')
        platform_functool.tar(self.config.package_name+'.tar',(self.config.package_name,))
        #再打一个gz包，别问为什么package_type，安装脚本里面写死了要处理的是tar包，不是gz包
        logger.debug('package %s'% self.config.package_name+'.tar.gz')
        platform_functool.gz(self.config.package_name+'.tar.gz',(self.config.package_name+'.tar',BuildMysql._INSTALL_SCRIPT))
        logger.info('finish packaging. ')
        logger.info('purge garbage. ')
        #tar包用完了，删掉
        logger.debug('remove %s'%self.config.package_name+'.tar')
        os.remove(self.config.package_name+'.tar')
        #工作目录中的打包文件也不用了，删掉
        logger.debug('remove %s'%self.config.package_name)
        rmtree(self.config.package_name)
        #shell也不要了
        os.remove(BuildMysql._INSTALL_SCRIPT)
