from git.repo.base import Repo

from package_vcms import Config, SvnDownloadException


class Mgit():
    def __init__(self,config:Config):
        self.configs = config
        self.repo = None
    def clone(self):
        self.repo = Repo.clone_from(self.configs.repo_url,self.configs.work_dir_new,multi_options=[' --depth 1 '])
        if not self.repo.bare:
            raise SvnDownloadException()
        assert self.repo.bare