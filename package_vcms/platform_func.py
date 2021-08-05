import glob
import logging
import os
import shutil
import subprocess
import sys
from abc import ABCMeta

from package_vcms import record_log, utils
from package_vcms.utils import getUnArchiveFileName, outres

logger = logging.getLogger(__file__)
class PlatFormFunc(object,metaclass=ABCMeta):
    def __init__(self):
        self._archive_format = 'gztar'
        self._gz_suffix = '.tar.gz'
        self._tar_suffix = '.tar'
        self._tar_format = 'tar'

    def gz(self,target, ar_root=None, ar_base=None):
        shutil.make_archive(target,format=self._archive_format,root_dir = ar_root or target,base_dir=ar_base)
        return target + self._gz_suffix

    def tar(self,target, ar_root=None, ar_base=None):
        shutil.make_archive(target,format=self._tar_format,root_dir = ar_root or target,base_dir=ar_base)
        return target + self._tar_suffix

    @record_log
    def removeFile(self,filelist=()):
        for file in filelist:
            # r_fs = glob.iglob(file,recursive=False)
            logger.info('remove file %s'%file)
            for r_f in glob.iglob(file,recursive=False):
                logger.info('remove real file %s'%r_f)
                os.remove(r_f)

    @record_log
    def exec_shell(self,cmd,stdout=False):
        _result: subprocess.CompletedProcess = subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')
        if stdout:
            return utils.getLine(_result.stdout) if _result.stdout else None
        return subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')

    def exec_shell_indnpnt(self,cmd):
        _result: subprocess.CompletedProcess = subprocess.run(cmd, shell=True,encoding='utf8')
        if _result.stdout:
            logger.info(utils.getLine(_result.stdout))
        if _result.stderr:
            logger.info(utils.getLine(_result.stderr))
        logger.info(_result.returncode)
        _result.check_returncode()
        assert _result.returncode == 0

class CentOSPlatFormFunc(PlatFormFunc):
    def __init__(self):
        super(CentOSPlatFormFunc, self).__init__()
        self.plat_form='linux'

    # linux使用shutil的库进行打包、压缩太慢了，还是使用原生的更快
    # def gz(self,target,files=()):
    @record_log
    def gz(self,target, ar_root=None, ar_base=None,cmd = None):
        assert not ar_base
        cmd = 'tar -czpf '
        logger.debug('%s,%s'%(getUnArchiveFileName(target),os.path.basename(target)))
        if getUnArchiveFileName(target) == os.path.basename(target):
            target += self._gz_suffix
        return self.tar(target,ar_root,None,cmd)

    # def tar(self,target,files=(),cmd=None):
    @record_log
    def tar(self,target, ar_root=None, ar_base=None,cmd = None):
        assert not ar_base
        if not cmd:
            cmd = 'tar -cpf '
        logger.debug('%s,%s'%(getUnArchiveFileName(target),os.path.basename(target)))
        if getUnArchiveFileName(target) == os.path.basename(target):
            target += self._tar_suffix
        cmd += ' ' + target
        # if not isinstance(files,(tuple,list)):
        #     files = (files,)
        for file in os.listdir(ar_root):
            cmd += ' ' + file
        _oldcwd = os.getcwd()
        os.chdir(os.path.dirname(target))
        res = self.exec_shell(cmd)
        os.chdir(_oldcwd)
        outres(logger,res)
        return target



class WindowsPlatFormFunc(PlatFormFunc):
    def __init__(self):
        super(WindowsPlatFormFunc, self).__init__()
        self.plat_form='windows'
        self._archive_format = 'zip'
        self._gz_suffix = '.zip'


    def tar(self,source,target):
        pass



if sys.platform.startswith('win'):
    platform_functool = WindowsPlatFormFunc()
else:
    platform_functool = CentOSPlatFormFunc()
