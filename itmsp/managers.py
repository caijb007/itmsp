# coding: utf-8
# Author: Dunkle Qiu

from django.db import models


class ParamManager(models.Manager):
    def get_queryset(self):
        return super(ParamManager, self).get_queryset().filter(setting_type='PARAM')

    def get_param(self, app, name, default_value='', default_value_display='', **default_ext_attr):
        """
        根据应用名、参数名获取参数, 如获取失败，自动添加由default_value指定的参数项
        """
        param = self.filter(app=app, name=name)
        if param.count() == 1:
            return param[0]
        elif default_value:
            return self.create(setting_type='PARAM', app=app, name=name, value=default_value,
                               display=default_value_display, ext_attr=default_ext_attr)
        else:
            return None

    def get_param_serialized(self, app, name):
        param = self.get_param(app, name)
        if param:
            data = {
                'app': app,
                'name': name,
                'value': param.value,
                'display': param.display,
                'ext_attr': param.ext_attr
            }
            return data
        else:
            return {}

    def set_param(self, app, name, value, display='', **ext_attr):
        """
        设置应用参数
        """
        try:
            new = False
            param = self.get_param(app, name)
            if param:
                param.value = value
            else:
                param = self.get_param(app, name, value)
                new = True
            if display:
                param.display = display
            if ext_attr:
                obj_ext_attr = param.ext_attr
                obj_ext_attr.update(ext_attr)
                param.ext_attr = obj_ext_attr
            param.save()
            return new
        except:
            return False


class OptionManager(models.Manager):
    def get_queryset(self):
        return super(OptionManager, self).get_queryset().filter(setting_type='OPTION')

    def get_app(self):
        """
        获取应用名
        """
        apps = []
        for opt in self.all():
            apps.append(opt.app)
        apps = list(set(apps))
        return apps

    def get_name(self, app):
        """
        根据应用名获取表单名
        """
        opt_set = self.filter(app=app)
        names = []
        for opt in opt_set:
            names.append(opt.name)
        names = list(set(names))
        return names

    def get_options(self, app, name, **ext_attr):
        """
        根据应用名、表单名获取动态表单选项
        """
        opt_set = self.filter(app=app, name=name)
        for k, v in ext_attr.items():
            map_q = "%s%%%s" % (k, str(v))
            opt_set = opt_set.filter(ext_attr__map=map_q)
        return opt_set

    def get_options_serialized(self, app, name, **ext_attr):
        options = []
        opt_set = self.get_options(app, name, **ext_attr)
        for opt in opt_set:
            opt_ext_attr = opt.ext_attr
            opt_ext_attr.update({'value': opt.value, 'display': opt.display})
            options.append(opt_ext_attr)
        data = {'app': app, 'name': name, 'options': options, 'ext_attr': ext_attr}
        return data

    def add_option(self, app, name, value, display='', **ext_attr):
        """
        在指定的表单下，添加选项。
        """
        opt_set = self.get_options(app, name).filter(value=value)
        if opt_set.exists():
            raise Exception(u"表单值已经存在")
        self.create(setting_type='OPTION', app=app, name=name, value=value, display=display,
                    ext_attr=ext_attr)
        return True

    def update_option(self, app, name, value, display='', **ext_attr):
        """
        修改指定的表单选项
        注：value不可修改，只支持增删
        """
        try:
            option = self.get_options(app, name).get(value=value)
            if display:
                option.display = display
            if ext_attr:
                obj_ext_attr = option.ext_attr
                obj_ext_attr.update(ext_attr)
                option.ext_attr = obj_ext_attr
            option.save()
            return True
        except:
            return False

    def delete_options(self, app, name, *values):
        """
        删除指定的动态表单选项
        """
        opt_set = self.get_options(app, name).filter(value__in=values)
        count = opt_set.count()
        try:
            opt_set.delete()
            return count
        except:
            return 0
