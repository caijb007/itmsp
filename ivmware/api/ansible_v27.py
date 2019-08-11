# coding: utf-8
# Author: ld

import os
import json
import shutil
import ansible.constants as C
from ansible.playbook.play import Play
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from itmsp.utils.base import set_log, LOG_LEVEL
from itmsp.settings import BASE_DIR
from iuser.models import ExUser

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

    def __init__(self,
                 connection='local',
                 module_path=None,
                 forks=None,
                 remote_user=None,
                 conn_pass=None,
                 become=False,
                 become_method=None,
                 become_user=None,
                 become_pass=None,
                 check=False,
                 diff=False,
                 gather_facts=None,
                 private_key_file=None,
                 ssh_args=None,
                 host_key_checking=None,
                 listhosts=None,
                 listtasks=None,
                 listtags=None,
                 syntax=None
                 ):
        self.connection = connection
        self.module_path = module_path
        self.forks = forks
        self.remote_user = remote_user
        self.conn_pass = conn_pass
        self.become = become
        self.become_method = become_method
        self.become_user = become_user
        self.become_pass = become_pass
        self.check = check
        self.diff = diff
        self.gather_facts = gather_facts
        self.paivate_key_file = private_key_file
        self.ssh_args = ssh_args
        self.host_key_checking = host_key_checking
        self.listhosts = listhosts
        self.listtasks = listtags
        self.listtasks = listtasks
        self.syntax = syntax


class AnsibleBase(object):
    def __init__(self, host_list, local_user, remote_user):
        if isinstance(host_list, (str, unicode)):
            self.host_list = host_list + ','
        else:
            self.host_list = None
        self.local_user = local_user
        self.remote_user = remote_user
        self.passwords = None
        self._cache_rsakey()
        self.options = Options()
        self.options.connection = 'smart'
        self.gather_faces = 'no'
        self.options.forks = 100
        self.options.check = False
        self.options.remote_user = remote_user

        self.options.private_key_file = self.key_file
        # self.options.host_key_checking = False
        C.HOST_KEY_CHECKING = False

        self.loader = DataLoader()
        self.results_callback = ResultCallback()
        self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

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

    def _build_play_source(self, name='Ansible Play', tasks=None, hosts='all', gather_facts='no'):
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
        play = Play().load(self.play_source, variable_manager=self.variable_manager, loader=self.loader)
        tqm = None
        result = -1
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback
            )
            result = tqm.run(play)
            self._tqm = tqm
        finally:
            if tqm is not None:
                tqm.cleanup()
            return result
            # shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

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
            options=self.options,
            passwords=self.passwords
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
        self._build_play_source(
            name='Ansible Template',
            tasks=[
                {'action': dict(module='template', args=templ_args)}
            ])
        result = self._play()
        self.variable_manager.extra_vars = {}
        return result


class AnsiblePlay(AnsibleBase):
    """
    Ansible远程执行类(管理员)
    """

    def __init__(self, host_list, local_user, remote_user, conn_pass=None, become_pass=None):
        super(AnsiblePlay, self).__init__(host_list, local_user, remote_user)
        if become_pass:
            self.options.become = True
            self.options.become_user = 'root'
            self.options.become_method = 'sudo'
        self.passwords = dict(conn_pass=conn_pass, become_pass=become_pass)

    def test(self):
        """
        连通性测试
        # """
        self._build_play_source(name='Ansible Ping', tasks=[{'action': dict(module='ping')}])
        return self._play()

    def play_authorized_key(self, target_user, pubkey_str, state="present"):
        self._build_play_source(
            name='',
            tasks=[
                {'action': dict(module='authorized_key', args=dict(user=target_user, key=pubkey_str, state=state))}
            ])
        return self._play()

    def play_authorized_user(self, target_user, local_user=None):
        """
        推送用户密钥
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
        self._build_play_source(name='change file attr',
                                tasks=[
                                    {'action': dict(module='file', args=file_args)}
                                ])
        return self._play()

    def play_add_user(self, username, **kwargs):
        """
        添加用户
        @param username: 用户组名
        @param kwargs: 其他参数 comment, uid, non_unique, seuser, group, groups, append, shell, home, skeleton,
                password, state, createhome, move_home, system, force, login_class, remove, generate_ssh_key,
                ssh_key_bits, ssh_key_type, ssh_key_file, ssh_key_comment, ssh_key_passphrase, update_password, expires
        """
        user_args = dict(name=username, **kwargs)
        self._build_play_source(name='add user',
                                tasks=[
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
        self._build_play_source(name='add usergroup',
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
        self._build_play_source(name='restart server', tasks=tasks)
        return self._play()

    def deploy_key(self, target_user):
        self.play_authorized_user(target_user)
        # 添加sudo权限
        action_args = dict(dest="/etc/sudoers", state="present", regexp="^{} ALL\=".format(target_user),
                           validate="visudo -cf %s", backup=True,
                           line="{} ALL=(ALL) NOPASSWD:ALL".format(target_user))
        self._build_play_source(name='add sudu permissions',
                                tasks=[
                                    {'action': dict(module='lineinfile', args=action_args)}
                                ])
        return self._play()
