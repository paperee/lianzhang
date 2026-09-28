# -*- coding: utf-8 -*-
"""端到端验收：通过真实 HTTP 走一遍注册→购物→预约→发帖→留言流程。"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"


def call(method, path, data=None, token=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.urlopen(req, body)
    return json.loads(r.read().decode())


d = call("POST", "/api/auth/register", {"username": "验收员", "password": "pass123", "phone": "13900000000", "type": "social"})
token = d["data"]["token"]
print("注册:", d["msg"])

call("POST", "/api/mall/cart/add", {"product_id": 1, "qty": 1}, token)
call("POST", "/api/mall/cart/add", {"product_id": 7, "qty": 2}, token)
d = call("POST", "/api/mall/order", None, token)
print("下单:", d["msg"], "订单号", d["data"]["order_id"], "合计", d["data"]["total"])

d = call("POST", "/api/study/book", {"type": "剧本杀", "name": "连樟秘境", "date": "2025-07-15", "people": 6}, token)
bid = d["data"]["booking_id"]
print("预约:", d["msg"], "编号", bid)

d = call("POST", "/api/community/posts", {"title": "验收测试帖", "content": "后端联通性验证", "type": "体验"}, token)
pid = d["data"]["post_id"]
call("POST", "/api/community/posts/%d/like" % pid, {}, token)
call("POST", "/api/community/posts/%d/comments" % pid, {"content": "测试评论"}, token)
d = call("GET", "/api/community/posts/%d/comments" % pid)
print("社区: 点赞/评论正常, 评论数 =", d["data"]["total"])

call("POST", "/api/museum/messages", {"name": "验收员", "content": "博物馆很棒"})
d = call("POST", "/api/museum/stories/1/like")
print("博物馆: 留言/点赞正常, 李大爷赞数 =", d["data"]["likes"])

d = call("DELETE", "/api/study/bookings/%d" % bid, None, token)
print("取消预约:", d["msg"])
print("\n端到端验收完成")
