"""Strict ASCII readers for the declared OpenFOAM benchmark subset.

No directives, substitutions, regular-expression keys or dynamic code. This is
not a general OpenFOAM parser; unsupported syntax is a reported contract error.
"""
import math
from pathlib import Path
import re


class FoamError(ValueError):
    pass


def tokens(text):
    text=re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    if any(c in text for c in ('#','$','`')):
        raise FoamError('不支持 include、宏替换或动态代码')
    return re.findall(r'"[^"\n]*"|[{}();\[\]]|[^\s{}();\[\]]+',text)


class Reader:
    def __init__(self, text):
        self.items=tokens(text);self.index=0
    def take(self):
        if self.index>=len(self.items):raise FoamError('文件意外结束')
        value=self.items[self.index];self.index+=1;return value
    def peek(self):
        return self.items[self.index] if self.index<len(self.items) else None
    def value(self):
        token=self.take()
        if token=='{':return self.mapping('}')
        if token in ('(','['):
            end=')' if token=='(' else ']';items=[]
            while self.peek()!=end:items.append(self.value())
            self.take();return items
        if token in ('}',')',']',';'):raise FoamError('括号或分号位置无效')
        return token.strip('"')
    def mapping(self, end=None):
        result={}
        while self.peek()!=end:
            key=self.take().strip('"')
            if key in result or key in '{}();[]':raise FoamError('重复字段或不支持的键：'+key)
            if self.peek()=='{':
                self.take();result[key]=self.mapping('}')
                if self.peek()==';':self.take()
            else:
                values=[]
                while self.peek()!=';':
                    if self.peek() in (None,'}'):raise FoamError('字段缺少分号：'+key)
                    values.append(self.value())
                self.take();result[key]=values
        if end:self.take()
        return result


def dictionary(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>16*1024*1024:
        raise FoamError('需要包内正规文件，单文件不超过 16 MiB')
    try:
        data=Reader(p.read_text(encoding='utf-8')).mapping()
    except (UnicodeError,RecursionError) as e:raise FoamError('编码或嵌套深度无效') from e
    header=data.get('FoamFile',{})
    if header.get('format')!=['ascii']:raise FoamError('只支持 ASCII 场文件')
    return data


def number(value):
    result=float(value)
    if not math.isfinite(result):raise FoamError('数值必须有限')
    return result


def integer(value):
    result=int(value)
    if str(result)!=str(value) or result<0:raise FoamError('需要非负整数')
    return result


def counted(path, kind):
    r=Reader(Path(path).read_text())
    if r.take()!='FoamFile' or r.take()!='{':raise FoamError('缺少 FoamFile 头')
    if r.mapping('}').get('format')!=['ascii']:raise FoamError('只支持 ASCII 网格')
    count=integer(r.take());body=r.value()
    if not isinstance(body,list) or r.peek() is not None:raise FoamError('计数列表格式无效')
    if kind=='faces':
        if len(body)!=2*count:raise FoamError('面数量不匹配')
        result=[]
        for n,ids in zip(body[::2],body[1::2]):
            if not isinstance(ids,list) or len(ids)!=integer(n):raise FoamError('面顶点数不匹配')
            result.append([integer(x) for x in ids])
    elif kind=='boundary':
        if len(body)!=2*count:raise FoamError('patch 数量不匹配')
        result={}
        for name,item in zip(body[::2],body[1::2]):
            if not isinstance(name,str) or not isinstance(item,dict) or name in result:raise FoamError('patch 定义无效')
            result[name]=item
    elif kind=='points':
        if len(body)!=count or any(not isinstance(row,list) or len(row)!=3 for row in body):raise FoamError('顶点列表无效')
        result=[tuple(number(x) for x in row) for row in body]
    else:
        if len(body)!=count:raise FoamError('标签列表数量不匹配')
        result=[integer(x) for x in body]
    return result


def field_values(value, count, vector=False):
    def cast(x):
        if vector:
            if not isinstance(x,list) or len(x)!=3:raise FoamError('需要三分量向量')
            return tuple(number(v) for v in x)
        return number(x)
    if value and value[0]=='uniform' and len(value)==2:
        return [cast(value[1])]*count
    if len(value)==4 and value[0]=='nonuniform' and value[1]==('List<vector>' if vector else 'List<scalar>'):
        if integer(value[2])!=count or not isinstance(value[3],list) or len(value[3])!=count:raise FoamError('场数据长度与网格不符')
        return [cast(x) for x in value[3]]
    raise FoamError('需要 uniform 或有明确计数的 nonuniform 场')
