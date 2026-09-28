# -*- coding: utf-8 -*-
"""各 API 板块共用的响应与请求工具。"""
from functools import wraps

from flask import jsonify, request

from . import store


def ok(data=None, msg="ok"):
    return jsonify({"code": 0, "msg": msg, "data": data})


def fail(msg, code=1, status=400):
    return jsonify({"code": code, "msg": msg, "data": None}), status


def body(*fields, required=True):
    """从 JSON 请求体取字段，返回 {field: value}；缺字段时抛 ValueError。"""
    data = request.get_json(silent=True) or {}
    out = {}
    missing = [f for f in fields if f not in data or data[f] in (None, "")]
    if missing and required:
        raise ValueError("缺少参数: " + ", ".join(missing))
    for f in fields:
        if f in data:
            out[f] = data[f]
    return out


def api(fn):
    """把 ValueError 转成 400 响应的小装饰器。"""

    @wraps(fn)
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except ValueError as e:
            return fail(str(e))
        except PermissionError as e:
            return fail(str(e), status=401)
        except Exception as e:  # noqa: BLE001
            return fail("服务器内部错误: %s" % e, code=500, status=500)

    return wrapper


def next_id(items):
    return (max((int(i.get("id", 0)) for i in items), default=0) + 1) if items else 1
