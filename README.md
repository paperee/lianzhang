# 云上樟源 · 连樟村文旅融合数字平台

> 连樟村线上门户 — 沉浸式 IP 形象 / 研学与剧本杀 / 连樟甄选商城 / 数字博物馆 / 互动社区

---

## 功能概览

| 板块           | 路由         | 核心能力                                              |
| -------------- | ------------ | ----------------------------------------------------- |
| 首页           | `/`          | 视频 Hero、全屏滚动叙事、五大板块导览、Lenis 平滑滚动 |
| 沉浸式 IP 门户 | `/ip-portal` | 樟樟公仔等 IP 形象展示                                |
| 研学与剧本杀   | `/study`     | 课程列表、预约 / 取消预约、我的预约                   |
| 连樟甄选商城   | `/mall`      | 12 款精选商品、分类筛选、搜索、购物车、下单           |
| 数字博物馆     | `/museum`    | 村民故事、非遗展示、留言簿、点赞                      |
| 互动社区       | `/community` | 帖子发布 / 点赞 / 评论、活动、问答                    |

全站共享登录态（`Authorization: Bearer <token>`），未登录可浏览，预约 / 购物车 / 发帖等需登录。

---

## 目录结构

```
云上樟源/
├── backend/                        # Python Flask 后端
│   ├── app.py                      # 应用入口（页面路由 + API 蓝图注册 + 静态托管）
│   ├── test_api.py                 # API 冒烟测试（test client 直测，无需启动服务）
│   ├── cdp_tape.py                 # CDP 录制辅助脚本
│   ├── e2e_check.py                # 端到端检查脚本
│   └── modules/
│       ├── __init__.py
│       ├── store.py                # 轻量 JSON 数据层（线程锁 + 原子落盘 + 读改写）
│       ├── helpers.py              # 统一响应 {code,msg,data} / 参数校验 / 异常装饰器
│       ├── auth.py                 # 认证（注册 / 登录 / 会话 Token / g.user 挂载）
│       ├── mall.py                 # 商城（商品 / 搜索 / 购物车 / 订单，12 款种子商品）
│       ├── study.py                # 研学（课程 / 预约 / 取消 / 我的预约）
│       ├── museum.py               # 博物馆（村民故事 / 非遗 / 留言簿 / 点赞）
│       └── community.py            # 社区（帖子 / 点赞 / 评论 / 活动 / 问答）
├── page/                           # 前端静态页面
│   ├── index.html                  # 首页（视频 Hero + 五大板块叙事）
│   ├── ip-portal.html              # 沉浸式 IP 门户
│   ├── study-script-platform.html  # 研学与剧本杀
│   ├── online-mall.html            # 连樟甄选商城
│   ├── digital-museum.html         # 数字博物馆
│   ├── interactive-community.html  # 互动社区
│   ├── lenis.min.js                # 平滑滚动库（本地托管）
│   ├── assets/
│   │   ├── css/site.css            # 共享设计系统（纸色×松绿×陶土 / Noto Serif SC + Marcellus）
│   │   └── js/site.js              # 共享脚本（YZY API 封装 / 登录态 / 导航 / 入场动效 / Toast）
│   ├── image/                      # 图片素材（IP、商城、首页、非遗等）
│   └── video/
│       └── lianzhang-scenery.mp4   # 首页 Hero 背景视频
├── data/                           # 运行时 JSON 数据（首次请求自动生成，.gitignore 建议忽略）
│   ├── users.json
│   ├── products.json
│   ├── carts.json
│   └── orders.json
├── requirements.txt                # Python 依赖（Flask ≥ 3.0）
├── package.json
└── README.md
```

---

## 技术栈

| 层   | 技术                                                                               |
| ---- | ---------------------------------------------------------------------------------- |
| 后端 | Python 3 · Flask 3.x · 原生 JSON 文件存储（无 ORM / 无数据库）                     |
| 前端 | 原生 HTML / CSS / JS · 响应式布局 · IntersectionObserver 入场动效 · Lenis 平滑滚动 |
| 设计 | 纸色 `#f5f3ec` × 松绿 `#3f4a24` × 陶土 `#b9823f` · Noto Serif SC + Marcellus 字体  |
| 测试 | `backend/test_api.py`（Flask test client，隔离临时数据目录）                       |

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务（同时托管前端页面与 API）
python backend/app.py
# => http://127.0.0.1:5000

# 3. 运行 API 冒烟测试（无需启动服务，test client 直测）
python backend/test_api.py
```

> Flask `debug=True`，修改后端代码自动重载；前端为静态文件，刷新即生效。

---

## 页面路由

| 路由          | 页面文件                          | 说明           |
| ------------- | --------------------------------- | -------------- |
| `/` · `/home` | `page/index.html`                 | 首页           |
| `/ip-portal`  | `page/ip-portal.html`             | 沉浸式 IP 门户 |
| `/study`      | `page/study-script-platform.html` | 研学与剧本杀   |
| `/mall`       | `page/online-mall.html`           | 连樟甄选商城   |
| `/museum`     | `page/digital-museum.html`        | 数字博物馆     |
| `/community`  | `page/interactive-community.html` | 互动社区       |

旧链接（如 `/online-mall.html`、`/image/...`、`/video/...`、`lenis.min.js`）由 `app.py` 的 `/_legacy` 兼容托管；未匹配路由 302 回首页。

---

## API 一览

统一返回 `{"code": 0, "msg": "ok", "data": ...}`，`code=0` 成功、非 0 失败。需登录的接口在请求头携带 `Authorization: Bearer <token>`。

### 认证 `/api/auth`

| 方法 | 路径                 | 说明                                         | 鉴权   |
| ---- | -------------------- | -------------------------------------------- | ------ |
| POST | `/api/auth/register` | 注册（`username`/`password`/`phone`/`type`） | -      |
| POST | `/api/auth/login`    | 登录                                         | -      |
| POST | `/api/auth/logout`   | 退出登录                                     | Bearer |
| GET  | `/api/auth/me`       | 当前用户信息                                 | Bearer |

### 商城 `/api/mall`

| 方法 | 路径                     | 说明                                                 | 鉴权   |
| ---- | ------------------------ | ---------------------------------------------------- | ------ |
| GET  | `/api/mall/products`     | 商品列表（支持 `?keyword=` 搜索、`?category=` 筛选） | -      |
| GET  | `/api/mall/products/:id` | 商品详情                                             | -      |
| GET  | `/api/mall/cart`         | 购物车                                               | Bearer |
| POST | `/api/mall/cart`         | 加入购物车                                           | Bearer |
| POST | `/api/mall/cart/remove`  | 移出购物车                                           | Bearer |
| POST | `/api/mall/order`        | 提交订单                                             | Bearer |

### 研学 `/api/study`

| 方法   | 路径                      | 说明     | 鉴权   |
| ------ | ------------------------- | -------- | ------ |
| GET    | `/api/study/courses`      | 课程列表 | -      |
| POST   | `/api/study/book`         | 预约课程 | Bearer |
| GET    | `/api/study/bookings`     | 我的预约 | Bearer |
| DELETE | `/api/study/bookings/:id` | 取消预约 | Bearer |

### 博物馆 `/api/museum`

| 方法 | 路径                           | 说明     | 鉴权   |
| ---- | ------------------------------ | -------- | ------ |
| GET  | `/api/museum/stories`          | 村民故事 | -      |
| GET  | `/api/museum/heritage`         | 非遗列表 | -      |
| GET  | `/api/museum/messages`         | 留言簿   | -      |
| POST | `/api/museum/stories/:id/like` | 故事点赞 | Bearer |
| POST | `/api/museum/messages`         | 发表留言 | Bearer |

### 社区 `/api/community`

| 方法 | 路径                                | 说明     | 鉴权   |
| ---- | ----------------------------------- | -------- | ------ |
| GET  | `/api/community/posts`              | 帖子列表 | -      |
| POST | `/api/community/posts`              | 发布帖子 | Bearer |
| POST | `/api/community/posts/:id/like`     | 帖子点赞 | Bearer |
| GET  | `/api/community/posts/:id/comments` | 评论列表 | -      |
| POST | `/api/community/posts/:id/comments` | 发表评论 | Bearer |
| GET  | `/api/community/activities`         | 活动列表 | -      |
| GET  | `/api/community/questions`          | 问答列表 | -      |
| POST | `/api/community/questions`          | 发布提问 | Bearer |

---

## 数据层

`backend/modules/store.py` 提供轻量 JSON 持久化：

- 数据文件位于 `data/*.json`，首次访问自动创建
- `threading.RLock` 按文件加锁 + `*.tmp` 原子 `os.replace` 落盘
- `load / save / update（原子读改写）/ now` 四个原语，所有业务模块共用
- 零第三方依赖；如需多机 / 生产部署，将 `store.py` 替换为 SQLite / MySQL 实现即可，业务模块 API 无需变动

---

## 前端共享资源

- **`assets/css/site.css`**
- **`assets/js/site.js`**

---

## 测试

```bash
# 冒烟测试：覆盖页面可达性、注册/登录、商城、研学、博物馆、社区核心流程
python backend/test_api.py

# 端到端检查（如需启动服务后检查）
python backend/e2e_check.py
```
