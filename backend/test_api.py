# -*- coding: utf-8 -*-
"""API 冒烟测试：不启动服务器，直接以 test client 走一遍核心流程。"""
import os
import sys
import tempfile
import shutil

# 隔离数据目录
_tmp = tempfile.mkdtemp()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import store as _store  # noqa: E402
_store.DATA_DIR = _tmp
_store.DATA_DIR = _tmp  # store.py 内通过模块级常量引用，统一替换

from app import app  # noqa: E402

c = app.test_client()
PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(extra) if extra else ""))


def j(r):
    return r.get_json(silent=True) or {}


# --- 页面 ---
for path in ["/", "/ip-portal", "/study", "/mall", "/museum", "/community"]:
    r = c.get(path)
    check("page " + path, r.status_code == 200 and b"</html>" in r.data)

# --- 认证 ---
r = c.post("/api/auth/register", json={"username": "小明", "password": "123456", "phone": "13800000000", "type": "student"})
check("register", r.status_code == 200 and j(r)["code"] == 0, j(r))
token = j(r)["data"]["token"]
H = {"Authorization": "Bearer " + token}

r = c.post("/api/auth/login", json={"username": "小明", "password": "wrong"})
check("login wrong pwd rejected", j(r).get("code") == 1)
r = c.post("/api/auth/login", json={"username": "小明", "password": "123456"})
check("login ok", j(r)["code"] == 0)
r = c.get("/api/auth/me", headers=H)
check("me", j(r)["data"]["username"] == "小明")

# --- 商城 ---
r = c.get("/api/mall/products")
check("products", j(r)["data"]["total"] == 12)
r = c.get("/api/mall/products?q=红茶")
check("search 红茶", j(r)["data"]["total"] == 1)
r = c.post("/api/mall/cart/add", json={"product_id": 2, "qty": 2})
check("cart add", r.status_code == 200)
r = c.get("/api/mall/cart")
check("cart get", j(r)["data"][0]["qty"] == 2)
r = c.post("/api/mall/order")
check("order requires login", j(r).get("code") == 1)
r = c.post("/api/auth/login", headers=H, json={"username": "小明", "password": "123456"})
check("login merges guest cart", j(r)["code"] == 0)
r = c.post("/api/mall/order", headers=H)
check("order", j(r)["code"] == 0 and j(r)["data"]["total"] == 256.0, j(r))
r = c.get("/api/mall/cart")
check("cart emptied after order", j(r)["data"] == [])

# --- 研学/剧本杀 ---
r = c.get("/api/study/courses?type=script")
check("scripts", j(r)["data"]["total"] == 1)
r = c.get("/api/study/courses?type=study")
check("courses", j(r)["data"]["total"] == 1)
r = c.post("/api/study/book", json={"type": "研学", "name": "自然生态研学之旅", "date": "2025-07-01", "people": 3})
check("book requires login", j(r).get("code") == 1)
r = c.post("/api/study/book", headers=H, json={"type": "剧本杀", "name": "连樟秘境", "date": "2025-07-01", "people": 8, "phone": "13800000000"})
check("book", j(r)["code"] == 0, j(r))
bid = j(r)["data"]["booking_id"]
r = c.get("/api/study/bookings", headers=H)
check("bookings", j(r)["data"]["total"] == 1)
r = c.delete(f"/api/study/bookings/{bid}", headers=H)
check("cancel booking", j(r)["code"] == 0)

# --- 博物馆 ---
r = c.get("/api/museum/heritage")
check("heritage", j(r)["data"]["total"] == 3)
r = c.post("/api/museum/stories/1/like")
check("story like", j(r)["data"]["likes"] == 1)
r = c.post("/api/museum/messages", json={"name": "游客", "content": "连樟村真美！"})
check("message", j(r)["code"] == 0)
r = c.get("/api/museum/messages")
check("messages list", j(r)["data"]["total"] == 1)

# --- 社区 ---
r = c.get("/api/community/posts")
check("posts seeded", j(r)["data"]["total"] == 3)
r = c.post("/api/community/posts", headers=H, json={"title": "我的第一篇", "content": "内容...", "type": "游记"})
check("post create", j(r)["code"] == 0, j(r))
pid = j(r)["data"]["post_id"]
r = c.post(f"/api/community/posts/{pid}/like")
check("post like", j(r)["data"]["likes"] == 1)
r = c.post(f"/api/community/posts/{pid}/comments", json={"content": "好文章"})
check("comment", j(r)["code"] == 0)
r = c.get(f"/api/community/posts/{pid}/comments")
check("comments list", j(r)["data"]["total"] == 1)
r = c.get("/api/community/activities")
check("activities", j(r)["data"]["total"] == 3)
r = c.post("/api/community/questions", headers=H, json={"title": "怎么去连樟村？"})
check("question", j(r)["code"] == 0)

shutil.rmtree(_tmp, ignore_errors=True)
print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
