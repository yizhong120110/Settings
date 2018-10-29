# -*-coding:utf8 -*-
import sys
import yaml
from . import traceback2
from .tools import py2func, AttrDict
def read_yaml(fn):
    """
    读取yaml文件信息
    得到key:value的字典数据
    """
    yaml_nr = yaml.load(open(fn, 'rb').read())
    return yaml_nr


def _py2func(body, fname):
    #注意func_args此处的逗号一定要加上，在一个参数的情况下，否则会把yaml_zd拆分成7个参数
    return py2func(body, modules=[],
                   func_args=( 'yaml_zd',  ), name=fname)


def proc_dict(yaml_zd, dict):
    """
    对dict中的key value进行处理
    {'PLUGINS': {'global_plugin': {'use_db':'orcl'}}}
    """
    for k, v in dict.items():
        # yaml中出现 return dict(DATABASE = 'hxkh_tj') 时，keys也应该是大写的，否则不能登记，使用方式为settings.DB_CONSTR.DATABASE
        if type(v) == str and 'return ' in v:
            fname = '_'.join(( 'cfg', 'init', k ))
            func = _py2func(v, fname)
            v = func(yaml_zd)
        try:
            keys = v.keys()
        except:
            keys = []
        if keys:
            yaml_zd[k] = proc_dict({}, v)
        else:
            yaml_zd[k] = v
    return AttrDict(yaml_zd)


class Settings(object):
    """
    用户使用register方法将配置项增加到系统中
    """

    def __init__(self):
        self.modules = []
        self._contract = []
        self._dict = {}
        self.default = {'USE_DB': True}
        self.USE_DB = True

    def register_yaml(self, fname):
        """
        fname  ---yaml配置文件的绝对路径+文件名
        """
        yaml_zd = {}
        #读取yaml文件内容获得一个字典数据结构
        try:
            yaml_nr = read_yaml(fname)
        except:
            
            traceback2.print_exc(show_locals=True)
            raise (EnvironmentError, "无法导入配置yaml文件[%s]: %s" % ( fname, e ) )
        if yaml_nr:
            yaml_zd = proc_dict(yaml_zd, yaml_nr)
            #对yaml_zd递归循环字典
            for k in yaml_zd.keys():
                setattr(self, k, getattr(yaml_zd, k))

    def register(self, module):
        """
        module  ---conig.py 和 oaconf.py
        """
        if module in self.modules:
            return
        try:
            mod = __import__(module, {}, {}, [''])
            self.modules.append(module)
        except ImportError as e:
            traceback2.print_exc(show_locals=True)
            raise (EnvironmentError, "无法导入配置模块[%s]: %s" % ( module, e ) )

        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                if setting not in self:
                    setattr(self, setting, setting_value)

        # 更新默认值
        default_dict(self._dict, self.default)

    def __getattr__(self, name):
        if name in self._dict:
            return self._dict[name]
        else:
            return None

    def __setattr__(self, name, val):
        if name in ( 'modules', '_contract', '_dict', 'default' ):
            self.__dict__[name] = val
        else:
            self._dict[name] = val

    def __contains__(self, name):
        return name in self._dict

    def unpack(self, d):
        for k, v in self._dict.items():
            if k == k.upper():
                d[k] = v

    def check(self, *args, **kwargs):
        msg = kwargs.get('msg', '')
        if msg:
            msg = '，' + msg
        for x in args:
            if isinstance(x, str):
                if x.upper() not in self:
                    raise RuntimeError('参数[%s]还未定义' % x.upper() + msg)

    def __str__(self):
        return repr(self.__dict__)


import copy


def default_dict(n, d):
    """ 根据d的字典内容,更新n中没有设定值的字典内容
        d和n有可能有嵌套的字典
    """
    if type(d) is not dict:
        return
        # 先解决子级别缺省值
    for k, v in n.items():
        if type(v) is dict and k in d:
            default_dict(v, d[k])
        # 再解决同级别缺省值
    n_keys = set(n.keys())
    d_keys = set(d.keys())
    diff = d_keys - n_keys
    for k in diff:
        n[k] = copy.deepcopy(d[k])

if __name__ == "__main__":
    settings = Settings()
    settings.register_yaml('main.yaml')
    print(settings.DB_TYPE)
