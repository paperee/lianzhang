# -*- coding: utf-8 -*-
"""
云上樟源 · 连樟村文旅融合数字平台
Flask 应用入口：注册各板块蓝图，提供前端页面与统一 API。

启动： python backend/app.py   （开发模式）
     亦可: python -m backend.app
"""
import os

from flask import Flask, send_from_directory

from modules.auth import auth_bp
from modules.mall import mall_bp
from modules.study import study_bp
from modules.museum import museum_bp
from modules.community import community_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), "page")

app = Flask(
    __name__,
    static_folder=os.path.join(PAGE_DIR, "assets"),
    static_url_path="/assets",
)
app.config["JSON_AS_ASCII"] = False

# 注册各板块 API 蓝图（前缀 /api/...）
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(mall_bp, url_prefix="/api/mall")
app.register_blueprint(study_bp, url_prefix="/api/study")
app.register_blueprint(museum_bp, url_prefix="/api/museum")
app.register_blueprint(community_bp, url_prefix="/api/community")

# 路由 -> 页面文件
PAGES = [
    ("/", "index.html"),
    ("/home", "index.html"),
    ("/ip-portal", "ip-portal.html"),
    ("/study", "study-script-platform.html"),
    ("/mall", "online-mall.html"),
    ("/museum", "digital-museum.html"),
    ("/community", "interactive-community.html"),
]


def _make_page_handler(filename, route):
    def _page():
        return send_from_directory(PAGE_DIR, filename)

    _page.__name__ = "page_" + route.strip("/").replace("-", "_").replace("/", "_") or "index"
    return _page


for _route, _file in PAGES:
    app.add_url_rule(_route, view_func=_make_page_handler(_file, _route))


# 兼容旧链接 / 静态资源：image/、video/、*.html、lenis.min.js 等
@app.route("/<path:filename>")
def _legacy(filename):
    return send_from_directory(PAGE_DIR, filename)


@app.errorhandler(404)
def _not_found(_e):
    return send_from_directory(PAGE_DIR, "index.html"), 302


if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(BASE_DIR), "data"), exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
