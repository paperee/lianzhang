# -*- coding: utf-8 -*-
"""用户认证板块：注册 / 登录 / 会话 Token。供全站登录态与预约、发帖等使用。"""
import hashlib
import secrets

from flask import Blueprint, g, request

from .helpers import api, body, fail, ok
from . import store

auth_bp = Blueprint("auth", __name__)
_FILE = "users"
_SALT = "yunszhangyuan"

# token -> 用户名 的会话表（内存态，重启后需重新登录）
_sessions = {}


def _hash(pwd):
    return hashlib.sha256((_SALT + pwd).encode("utf-8")).hexdigest()


def _public(user):
    return {"id": user["id"], "username": user["username"],
            "phone": user.get("phone", ""), "type": user.get("type", "student")}


@auth_bp.before_app_request
def _load_user():
    """从 Header 解析 token，挂载 g.user。"""
    g.user = None
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        username = _sessions.get(token)
        if username:
            users = store.load(_FILE, [])
            g.user = next((u for u in users if u["username"] == username), None)
            g.token = token


def current_user():
    return g.get("user")


def require_login():
    if not current_user():
        raise PermissionError("请先登录")


@auth_bp.route("/register", methods=["POST"])
@api
def register():
    d = body("username", "password", "phone", "type")
    if len(d["password"]) < 6:
        return fail("密码至少 6 位")

    def _do(users):
        if any(u["username"] == d["username"] for u in users):
            return None
        users.append({
            "id": (max((u["id"] for u in users), default=0) + 1),
            "username": d["username"],
            "phone": d.get("phone", ""),
            "type": d.get("type", "student"),
            "password": _hash(d["password"]),
        })
        return d["username"]

    name = store.update(_FILE, [], _do)
    if name is None:
        return fail("用户名已被注册")
    _merge_guest_cart(name)
    return login_ok(name, "注册成功")


def login_ok(username, msg):
    token = secrets.token_hex(16)
    _sessions[token] = username
    users = store.load(_FILE, [])
    user = next(u for u in users if u["username"] == username)
    return ok({"token": token, "user": _public(user)}, msg)


def _merge_guest_cart(username):
    """登录/注册时把游客购物车合并到用户名下。"""
    from flask import request
    guest = request.remote_addr

    def _do(carts):
        items = carts.pop(guest, None)
        if not items:
            return
        mine = carts.setdefault(username, [])
        for it in items:
            row = next((r for r in mine if r["product_id"] == it["product_id"]), None)
            if row:
                row["qty"] += it["qty"]
            else:
                mine.append(it)
    store.update("carts", {}, _do)


@auth_bp.route("/login", methods=["POST"])
@api
def login():
    d = body("username", "password")
    users = store.load(_FILE, [])
    user = next((u for u in users if u["username"] == d["username"]), None)
    if not user or user["password"] != _hash(d["password"]):
        return fail("用户名或密码错误", status=401)
    _merge_guest_cart(user["username"])
    return login_ok(user["username"], "登录成功")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    _sessions.pop(token, None)
    return ok(msg="已退出登录")


@auth_bp.route("/me", methods=["GET"])
@api
def me():
    u = current_user()
    if not u:
        return fail("未登录", status=401)
    return ok(_public(u))
