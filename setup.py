#!/usr/bin/python
# coding: utf-8

import os
import socket
import sys
import time

import django
from django.core.management import call_command

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'itmsp.settings'
setup = django.setup()

from iuser.models import ExUser
from itmsp.settings import FUNC_APPS

socket.setdefaulttimeout(2)


class Setup(object):
    """
    安装jumpserver向导
    """

    def __init__(self):
        self.admin_user = 'admin'
        self.admin_pass = 'admin'
        self.admin_email = 'admin@admin.org'

    @staticmethod
    def _migrate():
        os.chdir(BASE_DIR)
        os.system('python manage.py makemigrations')
        os.system('python manage.py migrate')

    def _create_admin(self):
        ExUser.objects.create_superuser(self.admin_user, email=self.admin_email, password=self.admin_pass,
                                        name=u'超级管理员')

    @staticmethod
    def _celery_start():
        os.system('celery worker -A itmsp  &')

    @staticmethod
    def _db_initial_params():
        call_command('loaddata', os.path.join(BASE_DIR, 'itmsp/utils/basegroup.json'))
        call_command('loaddata', os.path.join(BASE_DIR, 'itmsp/utils/iworkflow.json'))
        call_command('loaddata', os.path.join(BASE_DIR, 'itmsp/utils/iconfig.json'))
        call_command('loaddata', os.path.join(BASE_DIR, 'itmsp/utils/iservermenu.json'))

    @staticmethod
    def _run_service():
        os.system('sh %s start' % os.path.join(BASE_DIR, 'service.sh'))
        print "initial itmsp success!"

    def start(self):
        print "start to setup itmsp..."
        self._migrate()
        # time.sleep(10)
        self._create_admin()
        self._db_initial_params()
        # self._celery_start()
        # self._run_service()


if __name__ == '__main__':
    setup = Setup()
    setup.start()
