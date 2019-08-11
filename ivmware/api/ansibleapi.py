# coding: utf-8
# Author: Dunkle Qiu

import ansible.constants as C
import json
import os
import shutil
import time
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase

from collections import namedtuple
from itmsp.settings import BASE_DIR, LOG_DIR
from iuser.models import ExUser

from itmsp.utils.base import set_log, LOG_LEVEL

ansible_logger = set_log(LOG_LEVEL, filename='ansible.log', logger_name='ansible')


class ResultCallback(CallbackBase):
    """
    自定义log输出
    """

    def v2_runner_on_ok(self, result, **kwargs):
        ansible_logger.info("RUN_OK")
        host = result._host
        print json.dumps({host.name: result._result}, indent=4)

    def v2_runner_on_unreachable(self, result, **kwargs):
        host = result._host
        print "Unreachable"
        print json.dumps({host.name: result._result}, indent=4)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host
        print "Fail"
        print json.dumps({host.name: result._result}, indent=4)
        print "Exception:::::::"
        print result._result['exception']


class Options(object):
    """
    全局options类
    用来替换ansible的OptParser
    """

    def __init__(self, connection=None, remote_user=None, module_path=None, forks=None, private_key_file=None,
                 ask_vault_pass=False, vault_password_files=False, ask_sudo_pass=False, ask_su_pass=False,
                 become_ask_pass=False, ask_pass=False, become=False, become_method=None, become_user=None,
                 become_pass=None, check=False, listhosts=None, listtasks=None, conn_pass=None, listtags=None,
                 host_key_checking=None, debug=True, warning=False,
                 syntax=None, gather_faces='no', diff=False):
        self.connection = connection
        self.remote_user = remote_user
        self.module_path = module_path
        self.forks = forks
        self.private_key_file = private_key_file
        self.conn_pass = conn_pass
        self.become = become
        self.become_method = become_method
        self.become_user = become_user
        self.become_pass = become_pass
        self.listhosts = listhosts
        self.listtasks = listtasks
        self.listtags = listtags
        self.syntax = syntax
        self.diff = diff
        self.gather_faces = gather_faces
        self.debug = debug
        self.warning = warning

        self.check = check
        self.ask_vault_pass = ask_vault_pass
        self.vault_password_files = vault_password_files
        self.ask_sudo_pass = ask_sudo_pass
        self.ask_su_pass = ask_su_pass
        self.become_ask_pass = become_ask_pass
        self.ask_pass = ask_pass
        self.host_key_checking = host_key_checking


# self.results_callback = CallbackBase(display=ansible_logger)
# results_callback = ResultCallback()


class PlayWithUser(object):
    """
    Ansible远程执行类
    """

    def __init__(self, host_list, local_user, remote_user):
        if isinstance(host_list, (str, unicode)):
            self.host_list = host_list + ','
        else:
            self.host_list = None

        self.local_user = local_user
        self.remote_user = remote_user
        self._cache_rsakey()
        # self.private_key_file = self.key_file
        self.results_callback = ResultCallback()
        self.options = Options()
        self._init_ansible()

    def _cache_rsakey(self):
        """
        生成私钥文件，ansible ssh连接调用
        """
        f_path = os.path.join(BASE_DIR, 'cache')
        if not os.path.exists(f_path):
            os.mkdir(f_path, 0755)
        self.key_file = os.path.join(f_path, self.local_user + '.id_rsa')
        f = file(self.key_file, 'w')
        key_str = ExUser.objects.get(username=self.local_user).ssh_key_str
        f.write(key_str)
        f.close()
        os.chmod(self.key_file, 0600)

    # def public_key(self):
    #     """
    #     是否存在public_key公钥文件，否则生成。ansible连接调用
    #     :return:
    #     """
    #     pub_key_path = os.path.join(BASE_DIR, 'cache/ssh')
    #     if not os.path.exists(pub_key_path):
    #         os.mkdir(pub_key_path, 0755)
    #     self.pub_key_file = os.path.join(pub_key_path, self.local_user + '.id_rsa.pub')

    def _init_ansible(self):
        """
        初始化Ansible对象
        """
        # initialize needed objects
        self.options.connection = 'smart'
        self.options.remote_user = self.remote_user
        self.options.forks = 2
        # len_hosts = len(self.host_list.split(','))
        # if self.options.forks == 0 or self.options.forks > len_hosts:
        #     self.options.forks = len_hosts - 1
        #
        # print self.options.forks
        self.options.private_key_file = self.key_file
        self.options.become = False
        self.options.check = False
        self.options.host_key_checking = False

        self.options.ask_vault_pass = False
        self.options.vault_password_files = False
        self.options.ask_sudo_pass = False
        self.options.ask_su_pass = False
        self.options.become_ask_pass = False
        self.options.ask_pass = False
        self.options.host_key_checking = False

        self.variable_manager = VariableManager()

        # create inventory and pass to var manager
        self.loader = DataLoader()
        # self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)
        self.inventory = InventoryManager(loader=self.loader, sources='118.240.13.4,')
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.play_source = None
        self.passwords = None

    def _set_play_source(self, name='Ansible Play', tasks=None, hosts='all', gather_facts='no'):
        """
        封装play_source
        """
        self.play_source = {
            'name': name,
            'hosts': hosts,
            'gather_facts': gather_facts,
            'tasks': tasks
        }

    def _play(self):
        """
        实际执行模块调用
        """
        if not self.play_source:
            print "play_source UNDEFINED"
            return False
        # else:
        #     print self.play_source
        play = Play().load(self.play_source, variable_manager=self.variable_manager, loader=self.loader)
        # actually run it
        tqm = None
        result = -1

        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback,
            )

            result = tqm.run(play)
            self._tqm = tqm
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
            while result is not -1:
                return result

    def test(self):
        """
        连通性测试
        # """
        self._set_play_source(name='Ansible Ping', tasks=[{'action': dict(module='ping')}])
        return self._play()

    def run_playbook(self, playbook='', extra_vars=None):
        """
        执行Playbook脚本
        @param playbook:Playbook文件路径
        @param extra_vars: 传入参数, 同命令行 -e 参数
        """
        if not playbook:
            return False
        if not os.path.isabs(playbook):
            playbook = os.path.join(BASE_DIR, 'playbooks', playbook)
        # 强制每次重新加载PlayBook, 而不是从CACHE读取
        if self.loader._FILE_CACHE.has_key(playbook):
            print "Cleaning CACHE of playbook: " + playbook
            del self.loader._FILE_CACHE[playbook]
        # 加载playbook vars
        if extra_vars:
            self.variable_manager.extra_vars = extra_vars
        # 加载运行PlayBook
        playbook_exc = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=self.options, passwords=self.passwords
        )
        tqm = playbook_exc._tqm
        tqm._stdout_callback = self.results_callback
        result = playbook_exc.run()
        self.variable_manager.extra_vars = {}
        return result

    def play_impl_templ(self, src, dest, extra_vars=None, attrs=None):
        """
        实例化Jinja2模板
        @param src: 模板文件
        @param dest: 目标文件
        @param extra_vars: 参数
        @param attrs: 文件属性: owner, group, mode
        """
        if not os.path.isabs(src):
            src = os.path.join(BASE_DIR, 'playbooks', src)
        templ_args = dict(src=src, dest=dest, backup=True)
        if attrs and isinstance(attrs, dict):
            for key in ['owner', 'group', 'mode']:
                if attrs.has_key(key):
                    templ_args[key] = attrs[key]
        if extra_vars:
            self.variable_manager.extra_vars = extra_vars
        self._set_play_source(
            name='Ansible Template',
            tasks=[
                {'action': dict(module='template', args=templ_args)}
            ])
        result = self._play()
        self.variable_manager.extra_vars = {}
        return result


class PlayWithAdmin(PlayWithUser):
    """
    Ansible远程执行类(管理员)
    """

    def __init__(self, host_list, local_user, remote_user):
        super(PlayWithAdmin, self).__init__(host_list, local_user, remote_user)

        self.options.become = True
        self.options.become_method = 'sudo'
        self.options.become_user = 'root'

    def play_authorized_key(self, target_user, pubkey_str, state="present"):
        self._set_play_source(name='play_authorized_key', tasks=[
            {'action': dict(module='authorized_key', args=dict(user=target_user, key=pubkey_str, state=state))}
        ])
        return self._play()

    def play_authorized_user(self, target_user, local_user=None):
        """
        推送用户密钥/公钥
        @param target_user: 服务器目标用户
        @param local_user: 系统本地用户
        """
        if not local_user:
            local_user = self.local_user
        try:
            pubkey_str = ExUser.objects.get(username=local_user).ssh_pubkey_str
        except:
            print "Could NOT find user: " + local_user
            return False
        return self.play_authorized_key(target_user, pubkey_str)

    def play_file(self, path, **kwargs):
        """
        修改文件属性
        @param path: 文件全路径
        @param kwargs: 其他参数 owner, group, mode, state, recurse
        """
        file_args = dict(path=path, **kwargs)
        self._set_play_source(name='change file attr', tasks=[
            {'action': dict(module='file', args=file_args)}
        ])
        return self._play()

    def play_add_user(self, username, **kwargs):
        """
        添加用户
        @param username: 用户名
        @param kwargs: 其他参数 comment, uid, non_unique, seuser, group, groups, append, shell, home, skeleton,
                password, state, createhome, move_home, system, force, login_class, remove, generate_ssh_key,
                ssh_key_bits, ssh_key_type, ssh_key_file, ssh_key_comment, ssh_key_passphrase, update_password, expires
        """
        user_args = dict(name=username, **kwargs)
        self._set_play_source(name='add user', tasks=[
            {'action': dict(module='user', args=user_args)}
        ])
        return self._play()

    def play_add_group(self, groupname, **kwargs):
        """
        添加用户组
        @param groupname: 用户组名
        @param kwargs: 其他参数 gid, state, system
        """
        group_args = dict(name=groupname, **kwargs)
        self._set_play_source(
            name='add usergroup',
            tasks=[
                {'action': dict(module='group', args=group_args)}
            ])
        return self._play()

    def play_restart_service(self, *args):
        """
        按参数列表依次重启系统服务
        @param args:
        @type args: str
        """
        tasks = [{'action': dict(module='service', args=dict(name=service, state='restarted'))}
                 for service in args]
        self._set_play_source(name='restart server', tasks=tasks)
        return self._play()


class PlayWithAdminUsingPass(PlayWithAdmin):
    def __init__(self, host_list, conn_user, conn_pass, local_user, become_pass=None):
        super(PlayWithAdminUsingPass, self).__init__(host_list, local_user, conn_user)
        # PlayWithUser.__init__(self, host_list, 'admin', conn_user)
        self.passwords = dict(conn_pass=conn_pass, become_pass=become_pass)

    def deploy_key(self, target_user, local_user):
        self.play_authorized_user(target_user, local_user)
        # 添加sudo权限(sudo免密码)
        action1_args = dict(dest="/etc/sudoers", state="present", regexp="^{} ALL\=".format(target_user),
                            validate="visudo -cf %s", backup=True,
                            line="{} ALL=(ALL) NOPASSWD:ALL".format(target_user))

        # 禁用tty提示
        action2_args = dict(dest="/etc/sudoers", state="present", regexp="^Defaults.*?requiretty",
                            validate="visudo -cf %s", backup=True,
                            line="# Defaults  requiretty")

        self._set_play_source(
            name='add sudu permissions',
            tasks=[
                dict(action=dict(module='lineinfile', args=action1_args)),
                dict(action=dict(module='lineinfile', args=action2_args))
            ])
        return self._play()

    # def host_info(self, fact_filename):
    #     """获取目标主机信息, 存储为json格式文件作为缓存"""
    #     fact_cache = os.path.join(BASE_DIR, 'cache')
    #     file_path = fact_cache + os.sep + fact_filename
    #     setup_args = dict(
    #
    #     )
    #     self._set_play_source(
    #         name='get hosts info',
    #         tasks=[
    #             dict(action=dict(module='ping')),
    #             dict(action=dict(module='setup', args=setup_args), register='destHostInfo'),
    #             dict(action=dict(module='copy', args=dict(
    #                 content="{{destHostInfo}}",
    #                 dest=file_path
    #             )))
    #         ])
    #     return self._play()

    def run_script(self, script_file, script_out_cache):
        """
        在目标主机执行脚本
        """
        tasks = [
            dict(action=dict(module='script', args=script_file), register='script_out'),
            dict(action=dict(module='copy', args=dict(
                content="{{script_out}}",
                dest=script_out_cache
            )))
        ]
        self._set_play_source(
            name="Run Custom Script",
            tasks=tasks
        )
        return self._play()

    # def fstype_disk(self, disk_path, file_type):
    #     """
    #     格式化磁盘
    #     """
    #     tasks = [
    #         dict(action=dict(module='script', args=script_file), register='script_out'),
    #         dict(action=dict(module='copy', args=dict(
    #             content="{{script_out}}",
    #             dest=script_out_cache
    #         )))
    #     ]
    #     self._set_play_source(
    #         name="Run Custom Script",
    #         tasks=tasks
    #     )
    #     return self._play()

    def resize_vg(self, vg_name, disk_path):
        """
        删除vg
        """
        tasks = [
            dict(action=dict(module='lvg', args=dict(
                vg=vg_name,
                # state='absent',
                pvs=disk_path,
                pesize=32
            ))),
        ]
        self._set_play_source(
            name="Run Custom Script",
            tasks=tasks
        )
        return self._play()

    def install_soft(self, softname=None, medium_path=None, package_manage=None, package_name=None, support_os=None):
        """
        安装软件
        """
        tasks = None
        if package_manage == 'yum':
            if package_name:
                tasks = [
                    dict(action=dict(module='yum', args=dict(
                        name=package_name,
                        state='latest'
                    )))
                ]
            else:
                tasks = [
                    dict(action=dict(module='yum', args=dict(
                        name=medium_path,
                        state='present'
                    )))
                ]
        elif package_manage == "apt":
            tasks = [
                dict(action=dict(module='apt', args=dict(
                    name=package_name,
                    state='latest'
                )))
            ]
        self._set_play_source(
            name="Installing soft " + softname,
            tasks=tasks
        )
        return self._play()

    def create_dir(self, dir_paths):
        """
        创建文件夹
        :param dir_path:  要创建的目录列表
        :return: 目录及创建状态
        """
        result = dict()
        if not isinstance(dir_paths, list):
            dir_paths = [dir_paths]
        for path in dir_paths:
            tasks = [
                dict(action=dict(module='file', args=dict(
                    path=path,
                    state='directory'
                ))),
            ]
            self._set_play_source(
                name="Created " + path,
                tasks=tasks
            )
            result[path] = self._play()
        return result

    def shell_cmd(self, ins_dir, log_dir, medium_path, script_path, order_id):
        """
        运行命令
        """
        result = dict()
        log_file = str(order_id) + '_' + str(time.time())
        log_path = log_dir + log_file
        tar_file = os.path.basename(medium_path)
        tasks_wget = [
            dict(action=dict(module='shell',
                             args="cd {ins_dir}; sudo wget {medium_path} >> {log_path} 2>&1".format(ins_dir=ins_dir,
                                                                                                    medium_path=medium_path,
                                                                                                    log_path=log_path))),
            dict(action=dict(module='shell',
                             args="cd {ins_dir}; tar xvf {tar_file} >> {log_path} 2>&1".format(ins_dir=ins_dir,
                                                                                               tar_file=tar_file,
                                                                                               log_path=log_path))),
            dict(action=dict(module='shell',
                             args="cd {ins_dir}; sudo -s {script_path} >> {log_path} 2>&1".format(ins_dir=ins_dir,
                                                                                                  script_path=script_path,
                                                                                                  log_path=log_path))),
        ]
        self._set_play_source(
            name="shell",
            tasks=tasks_wget
        )
        self._play()
        return result

    def parted(self, device):
        """
        分区
        """
        flags = ['lvm']  # 默认lvm分区
        tasks_parted = [
            dict(action=dict(
                module="parted",
                args=dict(
                    device=device,
                    number=2,
                    flags=flags,
                    state="present",
                )
            ))
        ]
        self._set_play_source(
            name="parted",
            tasks=tasks_parted
        )

        return self._play()
