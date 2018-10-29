# -*- coding: utf-8 -*-
""" 尚捷科技 """
"""
定义函数工具
"""
import textwrap
import io as cStringIO

def py2func(code, modules=[], func_args=(), name='<string>'):
    """
        将字符串形式的代码块编译到系统环境中，并返回函数实例
    """
    code = textwrap.dedent(code.replace('\r', '')) # 转换为标准linux格式
    clines = code.split('\n')
    cs = ["def func( " + ' , '.join(func_args) + " ):"]
    cs.extend(['    try:'])
    cs.extend(['        ' + x for x in modules + clines])
    cs.extend(['        pass'])  # 防止纯回车，导致出错
    cs.extend(['    except:'])
    cs.extend(['        import sys ,traceback'])
    cs.extend(['        exc = sys.exc_info()'])
    cs.extend(['        traceback.print_exception( *exc )'])      # 输出错误信息
    cs.extend(["        print('错误信息中提示的func中的line值比实际多3')"])
    cs.extend(['        raise'])
    funcbody = '\n'.join(cs).strip()
    #print('======================\n',funcbody,'\n======================')
    # compile 编译源到代码或AST对象
    c = compile(funcbody, name, 'exec')
    exec(c, globals())
    return func


class Stack(list):
    def push(self, *args):
        if len(args) == 1:
            args = args[0]
        self.insert(0, args)

    def pop(self):
        if len(self):
            return list.pop(self, 0)
        else:
            raise StackEmpty()

    def top(self):
        if len(self):
            return self[0]
        else:
            raise StackEmpty()

    def depth(self):
        return len(self)

    def is_empty(self):
        return self.depth() == 0


class StackEmpty(Exception):
    def __init__(self):
        self.args = ( 'empty stack', )


import copy


class AttrDict(object):
    # 可使用属性访问内容的字典类
    def __init__(self, initd=None, nocopy=True, kword=None, strict=False):
        """
            initd       初始字典
            nocopy      是否复制初始字典（默认不复制以提高效率）
            kword       关键字，关键字保证数据的存在，并控制内容
            strict      是否严格处理，当为True时，不允许获取不存在的数据，否则返回None
        """
        self._stack = []
        if nocopy:
            self._dict = initd or {}
        else:
            self._dict = copy.deepcopy(initd or {})
        self.Keyword = kword
        self.strict = strict

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def __getattr__(self, key):
        try:
            return self.__dict__['_dict'][key]
        except KeyError:
            try:
                if self.Keyword and type(key) is str:
                    attr = getattr(self.Keyword, key)
                    return attr.default
                else:
                    raise AttributeError()
            except AttributeError:
                if self.__dict__['strict']:
                    raise KeyError(key)
                else:
                    return None

    def __setattr__(self, key, value):
        if key == '_dict':
            self.__dict__['_dict'] = value
            return
        if key == '_stack':
            self.__dict__['_stack'] = value
            return
        if key == 'Keyword':
            self.__dict__['Keyword'] = value
            return
        if key == 'strict':
            self.__dict__['strict'] = value
            return
        try:
            if self.Keyword and type(key) is str:
                attr = getattr(self.Keyword, key)
                self._dict[key] = attr.validate(key, value)
            else:
                self._dict[key] = value
        except AttributeError:
            self._dict[key] = value

    def __delattr__(self, key):
        if self._dict.get(key, None):
            del self._dict[key]

    def __copy__(self, memo):
        return self.to_dict()

    __deepcopy__ = __copy__

    def to_dict(self):
        d = copy.deepcopy(self._dict)
        return d

    def from_dict(self, d, nocopy=False):
        if type(d) is not dict:
            d = {}
        if nocopy:
            self._dict = d
        else:
            self._dict = copy.deepcopy(d)

    def get(self, key, *args):
        if type(key) is str:
            keys = key.split('.')
        else:
            keys = [key]
        dict1 = self._dict
        li = []
        for k1 in keys:
            if type(dict1) == AttrDict:
                dict1 = dict1._dict
            try:
                dict1 = getattr(dict1, k1)
            except:
                try:
                    dict1 = dict1[k1]
                except:
                    if args:
                        return args[0]
                    else:
                        raise KeyError('无法在对象[%s]中找到[%s]的值' % ( '.'.join(li), k1 ))
            li.append(k1)

        return dict1

    def push(self):
        self._stack.append(copy.deepcopy(self._dict))

    def pop(self):
        self._dict = self._stack.pop()

    def clear(self):
        self._dict.clear()

    def update(self, dic):
        self._dict.update(dic)

    def __str__(self):
        s = cStringIO.StringIO()
        s.write('AttrDict{\n')
        keys = self.keys()
        for key in sorted(keys):
            value = self._dict[key]
            r = repr(value)
            r = '\n'.join(textwrap.wrap(r))
            s.write('%s:%s\n' % ( key, r ))
        s.write('}\n')
        return s.getvalue()

    __repr__ = __str__

    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, arg):
        self.from_dict(arg)
