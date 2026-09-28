# -*- coding: utf-8 -*-
"""互动社区板块：内容流（发帖/点赞/评论）、话题活动、问答论坛。"""
from flask import Blueprint, request

from .helpers import api, body, fail, next_id, ok
from . import store
from .auth import current_user, require_login

community_bp = Blueprint("community", __name__)

_POSTS = "posts"
_COMMENTS = "comments"
_QUESTIONS = "questions"

ACTIVITIES = [
    {"id": 1, "badge": "进行中", "icon": "fa-camera-retro", "title": "「最美连樟」摄影大赛",
     "desc": "用镜头记录连樟村的四时晨昏、烟火人情，优秀作品将在数字博物馆展出。",
     "joined": 328, "deadline": "剩余15天"},
    {"id": 2, "badge": "热门", "icon": "fa-pen-fancy", "title": "连樟体验分享活动",
     "desc": "分享你在连樟村的研学、游览、美食体验，优质笔记将获得官方流量推荐。",
     "joined": 256, "deadline": "长期活动"},
    {"id": 3, "badge": "即将开始", "icon": "fa-book-open", "title": "「我的连樟故事」征文比赛",
     "desc": "写下你与连樟村的故事，文体不限，一等奖可获连樟甄选大礼包。",
     "joined": 0, "deadline": "6月1日开启"},
]


@community_bp.route("/activities", methods=["GET"])
@api
def activities():
    return ok({"list": ACTIVITIES, "total": len(ACTIVITIES)})


# ---------- 内容流 ----------
@community_bp.route("/posts", methods=["GET"])
@api
def posts():
    items = store.load(_POSTS, _SEED_POSTS)
    if not store.load(_POSTS, None) and not items:
        store.save(_POSTS, _SEED_POSTS)
    t = (request.args.get("type") or "").strip()
    if t and t != "all":
        items = [p for p in items if p["type"] == t]
    items = sorted(items, key=lambda p: p["id"], reverse=True)
    return ok({"list": items, "total": len(items)})


@community_bp.route("/posts", methods=["POST"])
@api
def create_post():
    require_login()
    d = body("title", "content")
    t = d.get("type", "体验")
    if t not in ("游记", "摄影", "攻略", "体验"):
        return fail("内容类型不合法")

    def _do(items):
        pid = next_id(items)
        items.append({"id": pid, "author": current_user()["username"],
                      "title": d["title"], "content": d["content"], "type": t,
                      "likes": 0, "comments": 0, "created": store.now()})
        return pid

    pid = store.update(_POSTS, [], _do)
    return ok({"post_id": pid}, "发布成功")


@community_bp.route("/posts/<int:pid>/like", methods=["POST"])
@api
def like(pid):
    def _do(items):
        p = next((p for p in items if p["id"] == pid), None)
        if not p:
            return None
        p["likes"] += 1
        return p["likes"]

    n = store.update(_POSTS, [], _do)
    if n is None:
        return fail("内容不存在", status=404)
    return ok({"likes": n})


@community_bp.route("/posts/<int:pid>/comments", methods=["GET"])
@api
def list_comments(pid):
    items = [c for c in store.load(_COMMENTS, []) if c["post_id"] == pid]
    return ok({"list": items, "total": len(items)})


@community_bp.route("/posts/<int:pid>/comments", methods=["POST"])
@api
def add_comment(pid):
    d = body("content")
    if pid not in [p["id"] for p in store.load(_POSTS, [])]:
        return fail("内容不存在", status=404)
    author = current_user()["username"] if current_user() else "游客"

    def _do(items):
        cid = next_id(items)
        items.append({"id": cid, "post_id": pid, "author": author,
                      "content": d["content"], "created": store.now()})
        return cid

    cid = store.update(_COMMENTS, [], _do)
    store.update(_POSTS, [], lambda posts: [p.update(comments=p.get("comments", 0) + 1)
                                            for p in posts if p["id"] == pid])
    return ok({"comment_id": cid}, "评论成功")


# ---------- 问答论坛 ----------
@community_bp.route("/questions", methods=["GET"])
@api
def questions():
    items = store.load(_QUESTIONS, _SEED_QUESTIONS)
    if not items:
        store.save(_QUESTIONS, _SEED_QUESTIONS)
    return ok({"list": items, "total": len(items)})


@community_bp.route("/questions", methods=["POST"])
@api
def ask():
    require_login()
    d = body("title")
    user = current_user()["username"]

    def _do(items):
        qid = next_id(items)
        items.insert(0, {"id": qid, "title": d["title"], "asker": user,
                         "answers": 0, "views": 0, "created": store.now()})
        return qid

    qid = store.update(_QUESTIONS, [], _do)
    return ok({"question_id": qid}, "提问成功")


_SEED_POSTS = [
    {"id": 1, "author": "张小明", "type": "游记", "title": "连樟村一日游：感受乡村振兴的魅力",
     "content": "今天终于来到了心心念念的连樟村！青山绿水，空气清新。我们先去了村史馆了解村庄的历史，然后体验了采茶，还品尝了地道的农家菜...",
     "likes": 328, "comments": 56, "created": "2025-06-01 10:00:00"},
    {"id": 2, "author": "李摄影师", "type": "摄影", "title": "连樟村四季风光摄影作品集",
     "content": "用镜头记录连樟村的四季变化，春天的茶园、夏天的荷塘、秋天的稻田、冬天的雪景，每一个季节都有独特的美。",
     "likes": 256, "comments": 42, "created": "2025-06-01 07:00:00"},
    {"id": 3, "author": "王导游", "type": "攻略", "title": "连樟村超详细游玩攻略，建议收藏！",
     "content": "作为本地导游，我为大家整理了一份超详细的游玩攻略，包含交通指南、住宿推荐、美食攻略、景点介绍、最佳游玩时间等...",
     "likes": 512, "comments": 89, "created": "2025-05-31 18:00:00"},
]

_SEED_QUESTIONS = [
    {"id": 1, "title": "连樟村最佳旅游时间是什么时候？", "asker": "旅游爱好者",
     "answers": 12, "views": 156, "created": "2025-06-01 09:00:00"},
    {"id": 2, "title": "连樟村有哪些必体验的研学课程？", "asker": "家长",
     "answers": 8, "views": 203, "created": "2025-06-01 07:00:00"},
]
