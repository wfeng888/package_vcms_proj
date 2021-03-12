import logging
import os
from configparser import ConfigParser
from os import path
from shutil import copyfile, rmtree

from package_vcms import Config, CURRENT_DIR
from package_vcms.build_package import BuildMysql
from package_vcms.platform_func import platform_functool
from package_vcms.utils import formatDate, formatDateTime, none_null_stringNone

logger = logging.getLogger(__file__)

class Packaging():
    def __init__(self):
        self.cp = ConfigParser(allow_no_value=True)
        self.cp.read(path.join(CURRENT_DIR, 'conf/config.ini'), encoding='utf-8')
        self.config = Config()
        self.config.setData(self.cp)
        if not self.config.work_dir:
            self.config.work_dir = CURRENT_DIR
        if not none_null_stringNone(self.config.log_level) and logging._nameToLevel.get(self.config.log_level.upper(),None):
            logging.getLogger().setLevel(logging._nameToLevel[self.config.log_level.upper()])
        logger.info(msg=self.config)
        # if not self.config.check():
        #     raise  ConfigFileException()

    def prepare(self):
        if not os.path.exists(self.config.work_dir):
            os.mkdir(self.config.work_dir)
        self.config.work_dir_new = path.join(self.config.work_dir,formatDateTime())
        os.mkdir(self.config.work_dir_new)
        self.config.package_name = self.config.mysql_packaging_name.format(platform=platform_functool.plat_form,date=formatDate(), \
                                                                lang='en' if self.config.database_lang and self.config.database_lang.lower()=='en' else 'cn', \
                                                                type=self.config.package_type)
        self.config.package_dir = path.join(self.config.work_dir_new,self.config.package_name)


    def packaging(self):
        self.prepare()
        _build = BuildMysql(self.config,self.cp)
        _build.build()
        #将最后的gz包copy到latest文件夹下，方便进一步处理
        logger.info('copy package to lastest. ')
        if  os.path.exists(path.join(self.config.work_dir,'latest')):
            rmtree(path.join(self.config.work_dir,'latest'))
        os.mkdir(path.join(self.config.work_dir,'latest'))
        copyfile(self.config.gz_package_path,path.join(self.config.work_dir,'latest',path.basename(self.config.gz_package_path)))



if '__main__' == __name__:
    Packaging().packaging()