# -*- coding: utf-8 -*-
"""研学与剧本杀板块：课程/剧本目录、预约下单、预约查询。"""
from flask import Blueprint, request

from .helpers import api, body, fail, next_id, ok
from . import store
from .auth import current_user, require_login

study_bp = Blueprint("study", __name__)

_FILE = "bookings"

COURSES = [
    {"id": 1, "type": "study", "name": "自然生态研学之旅", "duration": "1天", "icon": "fa-leaf",
     "desc": "走进连樟村的绿水青山，认识乡村生态系统，在自然课堂中学习生态保护知识。"},
]

SCRIPTS = [
    {"id": 1, "type": "script", "name": "连樟秘境", "players": "6-8人", "hours": "3-4小时", "score": 4.8, "icon": "fa-mountain",
     "desc": "以连樟村山水为舞台的大型实景剧本杀，在秘境探索中揭开村庄的古老传说。"},
]


@study_bp.route("/courses", methods=["GET"])
@api
def courses():
    t = (request.args.get("type") or "").strip()
    items = COURSES + SCRIPTS
    if t in ("study", "script"):
        items = [c for c in items if c["type"] == t]
    return ok({"list": items, "total": len(items)})


@study_bp.route("/book", methods=["POST"])
@api
def book():
    require_login()
    d = body("type", "name", "date", "people")
    if d["type"] not in ("研学", "剧本杀"):
        return fail("type 必须是 研学 或 剧本杀")
    if not (1 <= int(d["people"]) <= 20):
        return fail("预约人数需在 1-20 人之间")
    if not any(c["name"] == d["name"] and {"study": "研学", "script": "剧本杀"}[c["type"]] == d["type"]
               for c in COURSES + SCRIPTS):
        return fail("项目不存在")

    def _do(items):
        bid = next_id(items)
        items.append({"id": bid, "user": current_user()["username"], "type": d["type"],
                      "name": d["name"], "date": d["date"], "people": int(d["people"]),
                      "phone": d.get("phone", ""), "note": d.get("note", ""),
                      "status": "已预约", "created": store.now()})
        return bid

    bid = store.update(_FILE, [], _do)
    return ok({"booking_id": bid}, "预约成功")


@study_bp.route("/bookings", methods=["GET"])
@api
def bookings():
    u = current_user()
    if not u:
        return fail("请先登录", status=401)
    items = [b for b in store.load(_FILE, []) if b["user"] == u["username"]]
    return ok({"list": items, "total": len(items)})


@study_bp.route("/bookings/<int:bid>", methods=["DELETE"])
@api
def cancel(bid):
    u = current_user()
    if not u:
        return fail("请先登录", status=401)

    def _do(items):
        b = next((b for b in items if b["id"] == bid and b["user"] == u["username"]), None)
        if not b:
            return False
        b["status"] = "已取消"
        return True

    ok_ = store.update(_FILE, [], _do)
    if not ok_:
        return fail("预约不存在", status=404)
    return ok(msg="已取消预约")
