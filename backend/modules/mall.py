# -*- coding: utf-8 -*-
"""连樟甄选商城板块：商品目录、搜索、购物车、下单。"""
from flask import Blueprint, request

from .helpers import api, body, fail, next_id, ok
from . import store
from .auth import current_user

mall_bp = Blueprint("mall", __name__)

_FILE = "products"
_ORDER_FILE = "orders"
_CART_FILE = "carts"

# 商品数据源：前端静态展示的 12 件商品入库
_SEED = [
    {"id": 1, "name": "连樟有机苹果 新鲜采摘 当季水果", "category": "农产品", "price": 39.9, "original": 59.9, "sales": 23000, "image": "image/商城1.png", "badge": "热销"},
    {"id": 2, "name": "连樟高山红茶 礼盒装 250g", "category": "茶叶饮品", "price": 128, "original": 168, "sales": 18000, "image": "image/商城2.png", "badge": "新品"},
    {"id": 3, "name": "手工红糖 传统工艺 500g", "category": "特色美食", "price": 25.8, "original": 35.8, "sales": 35000, "image": "image/商城3.png", "badge": ""},
    {"id": 4, "name": "有机蔬菜套餐 新鲜配送 5斤装", "category": "水果蔬菜", "price": 49.9, "original": 69.9, "sales": 52000, "image": "image/商城4.png", "badge": "特价"},
    {"id": 5, "name": "农家胡萝卜 有机种植 3斤装", "category": "农产品", "price": 15.9, "original": 22.9, "sales": 89000, "image": "image/商城5.png", "badge": ""},
    {"id": 6, "name": "连樟辣椒酱 手工制作 200g", "category": "特色美食", "price": 18.8, "original": 28.8, "sales": 42000, "image": "image/商城6.png", "badge": ""},
    {"id": 7, "name": "土鸡蛋 散养 30枚装", "category": "农产品", "price": 35.9, "original": 45.9, "sales": 67000, "image": "image/商城7.png", "badge": "促销"},
    {"id": 8, "name": "农家大米 东北稻花香 5kg", "category": "农产品", "price": 68, "original": 88, "sales": 31000, "image": "image/商城8.png", "badge": ""},
    {"id": 9, "name": "木雕工艺品 乡村主题 收藏级", "category": "手工艺品", "price": 388, "original": 528, "sales": 5000, "image": "image/商城9.jpg", "badge": "非遗"},
    {"id": 10, "name": "竹编工艺品 传统手艺 收藏级", "category": "手工艺品", "price": 188, "original": 258, "sales": 12000, "image": "image/商城10.webp", "badge": ""},
    {"id": 11, "name": "手工布艺玩偶 连樟特色", "category": "手工艺品", "price": 128, "original": 168, "sales": 9000, "image": "image/商城11.jpg", "badge": "新品"},
    {"id": 12, "name": "手工制作香囊 中药配方", "category": "手工艺品", "price": 68, "original": 98, "sales": 18000, "image": "image/商城12.jpg", "badge": "热销"},
]


def _products():
    items = store.load(_FILE, [])
    if not items:
        store.save(_FILE, _SEED)
        return _SEED
    return items


@mall_bp.route("/products", methods=["GET"])
@api
def products():
    items = _products()
    kw = (request.args.get("q") or "").strip()
    cat = (request.args.get("category") or "").strip()
    if kw:
        items = [p for p in items if kw in p["name"]]
    if cat:
        items = [p for p in items if p["category"] == cat]
    return ok({"list": items, "total": len(items),
               "categories": sorted({p["category"] for p in _products()})})


@mall_bp.route("/products/<int:pid>", methods=["GET"])
@api
def product_detail(pid):
    p = next((p for p in _products() if p["id"] == pid), None)
    if not p:
        return fail("商品不存在", status=404)
    return ok(p)


# ---------- 购物车 ----------
def _cart_key():
    u = current_user()
    return u["username"] if u else request.remote_addr


def _get_cart():
    carts = store.load(_CART_FILE, {})
    return carts.get(_cart_key(), [])


@mall_bp.route("/cart", methods=["GET"])
def get_cart():
    return ok(_get_cart())


@mall_bp.route("/cart/add", methods=["POST"])
@api
def cart_add():
    d = body("product_id", "qty")
    pid = int(d["product_id"])
    qty = max(1, int(d.get("qty", 1)))
    p = next((p for p in _products() if p["id"] == pid), None)
    if not p:
        return fail("商品不存在", status=404)
    store.update(_CART_FILE, {}, lambda carts: carts.setdefault(_cart_key(), []))

    def _add(items):
        row = next((i for i in items if i["product_id"] == pid), None)
        if row:
            row["qty"] += qty
        else:
            items.append({"product_id": pid, "name": p["name"], "price": p["price"],
                          "image": p["image"], "qty": qty})
    store.update(_CART_FILE, {}, lambda carts: (_add(carts.setdefault(_cart_key(), [])), None)[1])
    return ok(_get_cart(), "已加入购物车")


@mall_bp.route("/cart/<int:pid>", methods=["DELETE"])
@api
def cart_remove(pid):
    def _rm(carts):
        carts[_cart_key()] = [i for i in carts.get(_cart_key(), []) if i["product_id"] != pid]
    store.update(_CART_FILE, {}, _rm)
    return ok(_get_cart(), "已移除")


# ---------- 下单 ----------
@mall_bp.route("/order", methods=["POST"])
@api
def order():
    u = current_user()
    if not u:
        return fail("请先登录后下单", status=401)
    cart = _get_cart()
    if not cart:
        return fail("购物车为空")

    total = round(sum(i["price"] * i["qty"] for i in cart), 2)

    def _save(orders):
        oid = next_id(orders)
        orders.append({"id": oid, "user": u["username"], "items": cart,
                       "total": total, "status": "待发货", "created": store.now()})
        return oid

    oid = store.update(_ORDER_FILE, [], _save)
    store.update(_CART_FILE, {}, lambda carts: carts.update({_cart_key(): []}))
    return ok({"order_id": oid, "total": total}, "下单成功")
