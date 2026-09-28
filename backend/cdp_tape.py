# -*- coding: utf-8 -*-
"""验证04胶带:量测 tape 与 main 的边界关系 + 截图。"""
import base64
import json
import socket
import struct
import subprocess
import time
import urllib.request

EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
PORT = 9231

proc = subprocess.Popen([
    EDGE, "--headless", "--disable-gpu", f"--remote-debugging-port={PORT}",
    "--window-size=1920,1080",
    "--user-data-dir=C:/Users/Admin/AppData/Local/Temp/edgeprof9",
    "http://127.0.0.1:5000/",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    tabs = {}
    for _ in range(40):
        try:
            tabs = [t for t in json.loads(urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/json", timeout=1).read())
                if t.get("type") == "page" and "5000" in t.get("url", "")]
            if tabs:
                break
        except Exception:
            time.sleep(0.5)
    ws_url = tabs[0]["webSocketDebuggerUrl"]
    path = ws_url.split("9231")[1]
    sock = socket.create_connection(("127.0.0.1", PORT), timeout=30)
    key = base64.b64encode(b"1234567812345678").decode()
    sock.send((f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{PORT}\r\n"
               "Upgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += sock.recv(4096)
    sock.settimeout(30)
    mid = 0

    def _recv():
        h = sock.recv(2)
        ln = h[1] & 0x7F
        if ln == 126:
            ln = struct.unpack(">H", sock.recv(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", sock.recv(8))[0]
        data = b""
        while len(data) < ln:
            chunk = sock.recv(ln - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def cmd(method, **params):
        global mid
        mid += 1
        payload = json.dumps({"id": mid, "method": method, "params": params}).encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        sock.send(bytes(header) + b"\x00\x00\x00\x00" + payload)
        while True:
            r = json.loads(_recv().decode("utf-8", "ignore"))
            if r.get("id") == mid:
                return r

    def ev(expr):
        r = cmd("Runtime.evaluate", expression=expr, returnByValue=True)
        res = r.get("result", {}).get("result", {})
        return res.get("value")

    time.sleep(8)
    ev("(function(){var l=document.getElementById('loader');if(l)l.classList.add('done');})()")
    # 直接点 rail 跳到 05(data-step=4)
    ev("(function(){document.querySelectorAll('#rail .dot')[4].click();})()")
    time.sleep(3)

    info = ev("""(function(){
        var card = document.querySelector('.module-card[data-step="4"]');
        var main = card.querySelector('.main');
        var tape = card.querySelector('.tape');
        var mb = main.getBoundingClientRect();
        var tb = tape.getBoundingClientRect();
        var cs = getComputedStyle(main);
        return {
            mainTop: Math.round(mb.top),
            tapeTop: Math.round(tb.top),
            tapeAboveMain: tb.top < mb.top,
            overhang: Math.round(mb.top - tb.top),
            mainOverflow: cs.overflow,
            mainClip: cs.clipPath,
            tapeOpacity: getComputedStyle(tape).opacity,
            tapeTransform: getComputedStyle(tape).transform.substring(0, 30)
        };
    })()""")
    print(json.dumps(info, ensure_ascii=False, indent=1))

    r = cmd("Page.captureScreenshot", format="png")
    png = base64.b64decode(r["result"]["data"])
    open("C:/Users/Admin/AppData/Local/Temp/yzy_04tape.png", "wb").write(png)
    print("shot saved")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
