# coding: utf-8
# Author: ld
import os
from django.utils import timezone
from traceback import format_exc
from iuser.models import ExUser
from itmsp.utils.base import logger, ping
from itmsp.settings import BASE_DIR
from itmsp.utils.ssh import ssh_connect, get_rsakey_from_string, ssh_logger


class SshExecutor(object):
    def __init__(self, hostname=None, conn_user=None, auth_type=None, local_user=None, conn_pass=None):
        # 获取平台定义常量
        self.hostname = hostname
        self.conn_user = conn_user
        self.local_user = local_user
        self.conn_pass = conn_pass
        self.auth_type = auth_type
        pkey = None

        if self.auth_type == 'pubkey':
            pkey_str = ExUser.objects.get(username=self.local_user).ssh_key_str
            pkey = get_rsakey_from_string(pkey_str)
            self.client = ssh_connect(self.hostname, self.conn_user, pkey=pkey)
        elif self.auth_type == 'password':
            # 使用密码连接SSH
            print("密码认证")
            self.client = ssh_connect(self.hostname, self.conn_user, password=self.conn_pass)
        else:
            raise Exception(u"无效的认证方式")

    def _exec(self, cmd):
        stdin, stdout, stderr = self.client.exec_command(cmd)
        output_str = stdout.read()
        if output_str:
            ssh_logger.info("{0}-SSH Output:\n{1}".format(self.hostname, output_str))
            return True, output_str
        err_str = stderr.read()
        if err_str:
            ssh_logger.warning("{0}-SSH Error:\n{1}".format(self.hostname, err_str))
            return False, err_str

    def upload_scripts(self, file_list, remote_dir='/tmp/opsap/ovm/scripts', mod='755'):
        """
        上传可执行脚本至远程服务器
        """
        assert isinstance(file_list, list)
        sftp_client = self.client.open_sftp()
        # 创建远程文件夹
        stdin, stdout, stderr = self.client.exec_command('mkdir -p ' + remote_dir)
        stdout.read()
        # 上传文件
        for filename in file_list:
            remote_file = os.path.join(remote_dir, os.path.basename(filename))
            sftp_client.put(os.path.join(BASE_DIR, filename), remote_file)
            self._exec("chmod {0} {1}".format(mod, remote_file))
        sftp_client.close()

    def add_disk_to_vg(self, vg_name, disk_path):
        scripts_list = [
            '../scripts/disk_into_vg.sh',
            '../scripts/fdisk_add_lvm.sh',
            '../scripts/lvm_create_fs.sh',
        ]
        remote_dir = '/tmp/opsap/scripts/'
        self.upload_scripts(scripts_list, remote_dir=remote_dir)
        cmd = 'sudo -s {0} {1} {2} > {log}'.format(
            "sh " + os.path.join(remote_dir, 'disk_into_vg.sh'), vg_name, disk_path,
            log=os.path.join(remote_dir, 'disk_into_vg_%s.log' % timezone.now().strftime('%Y%m%d%H%M'))
        )
        return self._exec(cmd)

    def install_stuff(self, install_dir, medium_path, script_path):
        tar_file = os.path.basename(medium_path)
        log_file = "/home/logs/install.log"
        mkdir, str_mkdir = self._exec("sudo mkdir -p {dir}".format(dir=install_dir))
        self._exec("sudo mkdir -p {dir}".format(dir=install_dir))
        wget, str_wget = self._exec(
            "cd {dir}; sudo wget {medium_path} >> {log} 2>&1".format(dir=install_dir, medium_path=medium_path,
                                                                     log=log_file))
        tar, str_tar = self._exec(
            "cd {dir}; tar xvf {file} >> {log} 2>&1".format(dir=install_dir, file=tar_file, log=log_file))
        install, str_install = self._exec(
            "cd {dir}; sudo -s {setup} >> {log} 2>&1".format(dir=install_dir, setup=script_path, log=log_file))

        if mkdir and wget and tar and install:
            # if wget and tar and install:
            return 0
        else:
            return 1
