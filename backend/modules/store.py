# -*- coding: utf-8 -*-
"""轻量 JSON 数据层：所有板块共用，数据落盘到 /data/*.json，带线程锁。"""
import json
import os
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # backend/modules
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))       # 项目根
DATA_DIR = os.path.join(PROJECT_DIR, "data")
_locks = {}
_reg = threading.Lock()


def _lock(name):
    with _reg:
        if name not in _locks:
            _locks[name] = threading.RLock()
        return _locks[name]


def _path(name):
    return os.path.join(DATA_DIR, name + ".json")


def load(name, default):
    p = _path(name)
    with _lock(name):
        if not os.path.exists(p):
            return default
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default


def save(name, data):
    p = _path(name)
    with _lock(name):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)


def update(name, default, fn):
    """原子读改写：fn(data) 原地修改后落盘，返回 fn 的结果。"""
    with _lock(name):
        data = load(name, default)
        result = fn(data)
        save(name, data)
        return result


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
