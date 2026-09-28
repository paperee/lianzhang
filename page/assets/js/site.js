/* 云上樟源 · 子页面共享脚本：API 封装 / 登录态 / 导航 / 入场动效 / Toast */
(function () {
    'use strict';

    /* ---------- API 封装 ---------- */
    var TOKEN_KEY = 'yzy_token';
    var USER_KEY = 'yzy_user';

    function token() { return localStorage.getItem(TOKEN_KEY) || ''; }
    function user() {
        try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); } catch (e) { return null; }
    }

    function api(method, url, body) {
        return fetch(url, {
            method: method,
            headers: Object.assign(
                { 'Content-Type': 'application/json' },
                token() ? { 'Authorization': 'Bearer ' + token() } : {}
            ),
            body: body === undefined ? undefined : JSON.stringify(body)
        }).then(function (r) {
            return r.json().then(function (j) {
                if (!j) throw new Error('响应解析失败');
                if (j.code !== 0) throw new Error(j.msg || '请求失败');
                return j.data;
            });
        });
    }

    window.YZY = {
        api: api,
        get: function (u) { return api('GET', u); },
        post: function (u, b) { return api('POST', u, b || {}); },
        del: function (u) { return api('DELETE', u); },
        token: token,
        user: user,
        saveSession: function (data) {
            localStorage.setItem(TOKEN_KEY, data.token);
            localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        },
        clearSession: function () {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
        }
    };

    /* ---------- 导航滚动态 ---------- */
    var nav = document.querySelector('.subnav');
    function onScroll() {
        if (nav) nav.classList.toggle('scrolled', window.scrollY > 60);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    /* ---------- 入场动效 ---------- */
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
            if (en.isIntersecting) {
                en.target.classList.add('in');
                io.unobserve(en.target);
            }
        });
    }, { threshold: .12 });
    document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
    window.io = io;  // 供各页面动态插入的 .reveal 元素复用

    /* ---------- Toast ---------- */
    var toastEl = document.querySelector('.toast');
    var toastTimer = null;
    window.toast = function (msg) {
        if (!toastEl) return;
        toastEl.textContent = msg;
        toastEl.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2800);
    };

    /* ---------- 登录 / 注册模态框 ---------- */
    var modal = document.getElementById('authModal');
    var loginForm = document.getElementById('loginForm');
    var regForm = document.getElementById('registerForm');

    window.openAuth = function (mode) {
        if (!modal) return;
        modal.classList.add('active');
        switchTab(mode || 'login');
    };
    window.closeAuth = function () {
        if (modal) modal.classList.remove('active');
    };
    window.switchTab = function (tab) {
        var isLogin = tab === 'login';
        if (loginForm) loginForm.style.display = isLogin ? 'block' : 'none';
        if (regForm) regForm.style.display = isLogin ? 'none' : 'block';
        var tabs = modal.querySelectorAll('.tabs button');
        tabs[0].classList.toggle('active', isLogin);
        tabs[1].classList.toggle('active', !isLogin);
    };

    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var name = document.getElementById('loginUsername').value.trim();
            var pwd = document.getElementById('loginPassword').value;
            YZY.post('/api/auth/login', { username: name, password: pwd }).then(function (data) {
                YZY.saveSession(data);
                closeAuth();
                toast('欢迎回来，' + data.user.username);
                renderAuthState();
                document.dispatchEvent(new CustomEvent('yzy:login', { detail: data.user }));
            }).catch(function (err) { toast(err.message); });
        });
    }
    if (regForm) {
        regForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var g = function (id) { return document.getElementById(id).value; };
            var pwd = g('registerPassword');
            if (pwd !== g('registerConfirmPassword')) { toast('两次输入的密码不一致'); return; }
            YZY.post('/api/auth/register', {
                username: g('registerUsername'), phone: g('registerPhone'),
                type: g('registerType'), password: pwd
            }).then(function (data) {
                YZY.saveSession(data);
                closeAuth();
                toast('注册成功，欢迎加入');
                renderAuthState();
                document.dispatchEvent(new CustomEvent('yzy:login', { detail: data.user }));
            }).catch(function (err) { toast(err.message); });
        });
    }
    if (modal) {
        modal.addEventListener('click', function (e) { if (e.target === modal) closeAuth(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAuth(); });
    }

    function renderAuthState() {
        var box = document.getElementById('authArea');
        if (!box) return;
        var u = YZY.user();
        if (u) {
            box.innerHTML = '<span class="who">☁ ' + u.username + '</span>' +
                '<a href="javascript:;" id="logoutBtn" style="margin-left:14px;opacity:.7">退出</a>';
            document.getElementById('logoutBtn').onclick = function () {
                YZY.post('/api/auth/logout').catch(function () {});
                YZY.clearSession();
                renderAuthState();
                document.dispatchEvent(new CustomEvent('yzy:logout'));
                toast('已退出登录');
            };
        } else {
            box.innerHTML = '<a href="javascript:;" onclick="openAuth(\'login\')">登录</a>' +
                '<a href="javascript:;" onclick="openAuth(\'register\')" style="margin-left:14px">注册</a>';
        }
    }
    document.addEventListener('DOMContentLoaded', renderAuthState);
})();
