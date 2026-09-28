# -*- coding: utf-8 -*-
"""数字博物馆板块：村民故事留言、非遗条目、参观留言簿。"""
from flask import Blueprint, request

from .helpers import api, body, fail, next_id, ok
from . import store

museum_bp = Blueprint("museum", __name__)

_STORIES = "stories"
_MESSAGES = "messages"

HERITAGE = [
    {"id": 1, "title": "连樟红茶制作技艺", "image": "image/商城2.png",
     "desc": "传承百年的制茶工艺，每一片茶叶都凝聚着茶农的智慧和汗水。",
     "tags": ["传统技艺", "茶文化", "手工制作"]},
    {"id": 2, "title": "传统竹编工艺", "image": "image/商城10.webp",
     "desc": "巧手编织，化竹为器，展现乡村工匠的精湛技艺。",
     "tags": ["手工艺", "竹文化", "实用艺术"]},
    {"id": 3, "title": "连樟黄糍制作技艺", "image": "image/非遗.jpg",
     "desc": "源自客家传统，用糯米与黄栀子制作的金黄色糍粑，软糯香甜，是连樟村节庆必备的传统美食。",
     "tags": ["客家美食", "传统手工", "节庆食品"]},
]

STORIES = [
    {"id": 1, "name": "李大爷", "role": "连樟村老村民", "icon": "fa-user",
     "story": "我在这片土地上生活了70年，见证了连樟村从贫穷落后到乡村振兴的巨大变化..."},
    {"id": 2, "name": "王阿姨", "role": "非遗传承人", "icon": "fa-user",
     "story": "这门手艺是我奶奶传给我的，现在我要把它传给下一代，让传统文化继续发扬光大..."},
    {"id": 3, "name": "陈老师", "role": "乡村教师", "icon": "fa-user-graduate",
     "story": "虽然条件艰苦，但看到孩子们渴望知识的眼神，我就觉得一切都值得。教育是改变命运的力量..."},
]


@museum_bp.route("/heritage", methods=["GET"])
@api
def heritage():
    return ok({"list": HERITAGE, "total": len(HERITAGE)})


@museum_bp.route("/stories", methods=["GET"])
@api
def stories():
    items = store.load(_STORIES, STORIES)
    return ok({"list": items, "total": len(items)})


@museum_bp.route("/stories/<int:sid>/like", methods=["POST"])
@api
def like_story(sid):
    def _do(items):
        s = next((s for s in items if s["id"] == sid), None)
        if not s:
            return None
        s["likes"] = s.get("likes", 0) + 1
        return s["likes"]

    n = store.update(_STORIES, STORIES, _do)
    if n is None:
        return fail("故事不存在", status=404)
    return ok({"likes": n}, "感谢点赞")


@museum_bp.route("/messages", methods=["GET"])
@api
def list_messages():
    items = store.load(_MESSAGES, [])
    page = max(1, int(request.args.get("page", 1)))
    size = 20
    seg = items[(page - 1) * size: page * size]
    return ok({"list": seg, "total": len(items), "page": page})


@museum_bp.route("/messages", methods=["POST"])
@api
def add_message():
    d = body("name", "content")
    if len(d["content"]) > 200:
        return fail("留言最多 200 字")

    def _do(items):
        items.insert(0, {"id": next_id(items), "name": d["name"],
                         "content": d["content"], "created": store.now()})
    store.update(_MESSAGES, [], _do)
    return ok(msg="留言成功，感谢您的到访")
