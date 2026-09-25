#!/usr/bin/env python3
"""
ADB Bridge - let any AI agent drive a real Android phone over plain ADB.

A small, dependency-free HTTP server that runs on the computer the phone is
plugged into (USB, or same Wi-Fi via `adb connect`). Any agent that can make an
HTTP request - Claude Code, Codex, a Python script, curl - can then see the
screen, read the UI tree, tap, swipe, type, and open apps.

It speaks the MobileRun/Droidrun v1 REST dialect, so anything written against
that cloud API works unchanged by pointing it at http://localhost:8723/v1.
No cloud, no API key, no subscription.

Usage:
    python3 local-bridge/adb-bridge.py                  # first physical device
    ADB_SERIAL=<serial> python3 local-bridge/adb-bridge.py
    PORT=8723 python3 local-bridge/adb-bridge.py

Environment:
    ADB_SERIAL                 pin a device (from `adb devices`); Wi-Fi serials
                               like 192.168.1.20:5555 are re-connected on demand
    PORT                       default 8723
    BIND                       default 127.0.0.1 (this machine only)
    PHONE_BRIDGE_TOKEN         if set, every request needs
                               `Authorization: Bearer <token>` (or X-Auth-Token).
                               Required when BIND is not loopback.
    PHONE_BRIDGE_ALLOW_SHELL=1 enable POST .../shell (off by default)
    PHONE_PIN                  lockscreen PIN for /unlock; or put it in
                               ~/.phone-bridge/pin. Never sent over the API.

Endpoints (MobileRun-compatible):
    GET  /v1/devices
    GET  /v1/devices/{id}
    GET  /v1/devices/{id}/screenshot[?max_height=1600]  -> image/png
    GET  /v1/devices/{id}/ui-state?filter=true          -> {"a11y_tree": ...}
    POST /v1/devices/{id}/tap        {"x","y"}
    POST /v1/devices/{id}/swipe      {"startX","startY","endX","endY","duration"}
    POST /v1/devices/{id}/keyboard   {"text","clear"}
    POST /v1/devices/{id}/global     {"action": 1=back 2=home 3=recents}
    PUT  /v1/devices/{id}/apps/{pkg}                    -> launch app

Extensions:
    GET  /v1/health                            -> adb, device, battery, screen state
    POST /v1/devices/{id}/key       {"keycode"}
    POST /v1/devices/{id}/deeplink  {"url", "package"}
    POST /v1/devices/{id}/wake      {"stayon": true}
    POST /v1/devices/{id}/unlock                -> wake + dismiss lockscreen (+PIN)
    POST /v1/devices/{id}/reconnect             -> re-pick / re-connect the device
    POST /v1/devices/{id}/shell     {"cmd", "timeout"}  (403 unless enabled)

The device id in the path is ignored; the bridge drives one phone.
"""
import hmac
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "2.0.0"
PORT = int(os.environ.get("PORT", "8723"))
BIND = os.environ.get("BIND", "127.0.0.1")
ADB_BIN = os.environ.get("ADB_BIN", "adb")
TOKEN = (os.environ.get("PHONE_BRIDGE_TOKEN") or "").strip()
# `shell` is arbitrary command execution as the adb shell user. Off unless asked for.
ALLOW_SHELL = os.environ.get("PHONE_BRIDGE_ALLOW_SHELL", "").lower() in ("1", "true", "yes")
PIN_FILE = os.path.expanduser("~/.phone-bridge/pin")

START_TIME = time.time()
_lock = threading.RLock()
_serial = None
_last_error = "not connected yet"


# ---- adb plumbing --------------------------------------------------------

def _run(cmd, binary=False, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return (b"" if binary else ""), str(e)
    out = r.stdout if binary else r.stdout.decode("utf-8", "replace")
    return out, r.stderr.decode("utf-8", "replace")


def _alive(serial):
    out, _ = _run([ADB_BIN, "-s", serial, "get-state"], timeout=10)
    return out.strip() == "device"


def _physical_devices():
    out, _ = _run([ADB_BIN, "devices"], timeout=15)
    found = []
    for line in out.splitlines()[1:]:
        if "\tdevice" not in line:
            continue
        serial = line.split("\t")[0].strip()
        if serial.startswith("emulator-"):
            continue
        found.append(serial)
    return found


def ensure_device(force=False):
    """Return a usable serial, re-connecting Wi-Fi ADB or re-picking if needed."""
    global _serial, _last_error
    with _lock:
        if not force and _serial and _alive(_serial):
            return _serial
        wanted = os.environ.get("ADB_SERIAL")
        if wanted:
            if ":" in wanted and not _alive(wanted):
                _run([ADB_BIN, "connect", wanted], timeout=15)
            if _alive(wanted):
                _serial, _last_error = wanted, ""
                return _serial
            _last_error = (f"ADB_SERIAL={wanted} is not attached. Check the cable, "
                           "accept the USB debugging prompt, or re-run `adb connect`.")
            return None
        devices = _physical_devices()
        if devices:
            _serial, _last_error = devices[0], ""
            return _serial
        _last_error = ("no device in `adb devices`. Plug the phone in and accept the "
                       "'Allow USB debugging' prompt, or `adb connect <ip>:5555`.")
        _serial = None
        return None


def adb(args, binary=False, timeout=30):
    serial = ensure_device()
    if not serial:
        return b"" if binary else ""
    out, err = _run([ADB_BIN, "-s", serial] + args, binary=binary, timeout=timeout)
    if not out and ("not found" in err or "offline" in err or "no devices" in err):
        serial = ensure_device(force=True)
        if serial:
            out, _ = _run([ADB_BIN, "-s", serial] + args, binary=binary, timeout=timeout)
    return out


def getprop(name):
    return adb(["shell", "getprop", name], timeout=10).strip()


def device_model():
    return getprop("ro.product.model") or "Android"


def screen_size():
    m = re.search(r"(\d+)x(\d+)", adb(["shell", "wm", "size"], timeout=10))
    return (int(m.group(1)), int(m.group(2))) if m else (1080, 2400)


# ---- input ---------------------------------------------------------------

def esc_text(t):
    """Escape text for `adb shell input text`. Spaces -> %s, shell metachars escaped."""
    out = []
    for ch in t:
        if ch == " ":
            out.append("%s")
        elif ch in "()<>|;&*\\~\"'`$":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def type_text(text, clear):
    if clear:
        adb(["shell", "input", "keyevent", "123"])          # MOVE_END
        adb(["shell", "input", "keyevent"] + ["67"] * 200)  # backspace x200
    for i in range(0, len(text or ""), 200):
        adb(["shell", "input", "text", esc_text(text[i:i + 200])])


# ---- ui-state: uiautomator XML -> MobileRun a11y_tree JSON --------------

def _bounds(s):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", s or "")
    if not m:
        return {"left": 0, "top": 0, "right": 0, "bottom": 0}
    l, t, r, b = map(int, m.groups())
    return {"left": l, "top": t, "right": r, "bottom": b}


def _node(el, filtered):
    text = el.get("text", "") or ""
    desc = el.get("content-desc", "") or ""
    clickable = el.get("clickable", "false") == "true"
    node = {
        "text": text,
        "contentDescription": desc,
        "className": el.get("class", ""),
        "resourceId": el.get("resource-id", ""),
        "isClickable": clickable,
        "boundsInScreen": _bounds(el.get("bounds", "")),
        "children": [],
    }
    for child in el:
        c = _node(child, filtered)
        if c is not None:
            node["children"].append(c)
    # filtered: drop unlabelled, non-clickable leaves
    if filtered and not text and not desc and not clickable and not node["children"]:
        return None
    return node


def _empty_tree():
    return {"text": "", "contentDescription": "", "className": "", "resourceId": "",
            "isClickable": False, "boundsInScreen": _bounds(""), "children": []}


def ui_state(filtered):
    # Remove the previous dump first so a failed dump cannot return a stale screen.
    adb(["shell", "rm", "-f", "/sdcard/wd.xml"], timeout=10)
    adb(["shell", "uiautomator", "dump", "/sdcard/wd.xml"], timeout=40)
    xml = adb(["exec-out", "cat", "/sdcard/wd.xml"], binary=True)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {"a11y_tree": _empty_tree()}
    return {"a11y_tree": _node(root, filtered) or _empty_tree()}


# ---- screenshot ----------------------------------------------------------

def screenshot(max_height=0):
    """PNG bytes, optionally downscaled (needs Pillow; full size otherwise)."""
    png = adb(["exec-out", "screencap", "-p"], binary=True, timeout=60)
    if not max_height or not png:
        return png
    try:
        from PIL import Image
    except ImportError:
        return png
    try:
        img = Image.open(io.BytesIO(png))
        if img.height <= max_height:
            return png
        w = round(img.width * max_height / img.height)
        img = img.resize((w, max_height), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        return png


# ---- power / lockscreen --------------------------------------------------

def screen_state():
    """Awake? Locked? A sleeping phone screenshots black and has an empty UI tree,
    which looks like a broken bridge, so report it explicitly.
    (`grep -m1` is avoided: closing the pipe early kills dumpsys mid-line.)"""
    power = adb(["shell", "dumpsys power | grep mWakefulness"], timeout=20)
    awake = "mWakefulness=Awake" in power
    policy = adb(["shell", "dumpsys window policy | grep mIsShowing"], timeout=20)
    m = re.search(r"mIsShowing=(true|false)", policy)
    locked = (m.group(1) == "true") if m else None
    return {"awake": awake, "locked": locked}


def _stored_pin():
    pin = os.environ.get("PHONE_PIN")
    if pin:
        return pin.strip()
    try:
        with open(PIN_FILE) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def unlock():
    """Wake, swipe the lockscreen away, and enter the stored PIN if there is one."""
    adb(["shell", "input", "keyevent", "224"])   # WAKEUP
    time.sleep(0.6)
    st = screen_state()
    if st["locked"] is False:
        adb(["shell", "svc", "power", "stayon", "true"])
        return {"ok": True, "detail": "already unlocked", "screen": st}

    w, h = screen_size()
    adb(["shell", "input", "swipe", str(w // 2), str(int(h * 0.8)),
         str(w // 2), str(int(h * 0.25)), "200"])
    time.sleep(0.8)
    pin = _stored_pin()
    if pin:
        adb(["shell", "input", "text", pin])
        time.sleep(0.3)
        adb(["shell", "input", "keyevent", "66"])  # ENTER
        time.sleep(1.2)

    st = screen_state()
    ok = st["locked"] is not True
    if ok:
        adb(["shell", "svc", "power", "stayon", "true"])
    return {"ok": ok, "screen": st,
            "detail": "unlocked" if ok else
            "still locked - set PHONE_PIN or write the PIN to ~/.phone-bridge/pin"}


def battery():
    out = adb(["shell", "dumpsys", "battery"], timeout=15)
    info = {}
    for key, field in (("level", "level"), ("status", "status"),
                       ("AC powered", "ac_powered"), ("USB powered", "usb_powered")):
        m = re.search(rf"^\s*{re.escape(key)}:\s*(\S+)", out, re.M)
        if m:
            info[field] = m.group(1)
    return info


# ---- HTTP ----------------------------------------------------------------

DEVICE_RE = re.compile(r"^/v1/devices/[^/]+$")


def _token_ok(handler):
    if not TOKEN:
        return True
    supplied = ""
    auth = handler.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        supplied = auth[7:].strip()
    if not supplied:
        supplied = (handler.headers.get("X-Auth-Token") or "").strip()
    return hmac.compare_digest(supplied, TOKEN)


class Handler(BaseHTTPRequestHandler):
    server_version = f"adb-bridge/{VERSION}"

    def log_message(self, *a):
        pass  # quiet

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or "0")
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _query(self, key, default=None):
        m = re.search(rf"[?&]{re.escape(key)}=([^&]*)", self.path)
        return m.group(1) if m else default

    def _auth(self):
        if _token_ok(self):
            return True
        self._send(401, {"detail": "unauthorized"})
        return False

    def _device_obj(self):
        serial = ensure_device()
        return {
            "id": serial or "local",
            "name": device_model() if serial else "Android",
            "state": "ready" if serial else "unavailable",
            "stateMessage": "connection established (adb-bridge)" if serial else _last_error,
            "screenSize": dict(zip(("width", "height"), screen_size())) if serial else None,
            "type": "adb_local", "billingStrategy": "none",
            "taskCount": 0, "activeTaskId": None, "userId": "local",
        }

    def do_GET(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]

        if path == "/v1/health":
            serial = ensure_device()
            return self._send(200, {
                "ok": bool(serial), "version": VERSION,
                "serial": serial, "adb_error": _last_error or None,
                "device": device_model() if serial else None,
                "android": getprop("ro.build.version.release") if serial else None,
                "battery": battery() if serial else {},
                "screen": screen_state() if serial else {},
                "shell_enabled": ALLOW_SHELL,
                "uptime_seconds": round(time.time() - START_TIME),
            })

        if path == "/v1/devices":
            return self._send(200, {
                "items": [self._device_obj()],
                "pagination": {"hasNext": False, "hasPrev": False, "page": 1,
                               "pageSize": 20, "total": 1, "pages": 1},
            })

        if path.endswith("/screenshot"):
            try:
                mh = int(self._query("max_height", "0") or 0)
            except ValueError:
                mh = 0
            png = screenshot(mh)
            if not png:
                return self._send(503, {"detail": _last_error or "screencap failed"})
            return self._send(200, png, ctype="image/png")

        if path.endswith("/ui-state"):
            return self._send(200, ui_state(self._query("filter") == "true"))

        if DEVICE_RE.match(path):
            return self._send(200, self._device_obj())

        return self._send(404, {"detail": "not found"})

    def do_POST(self):
        if not self._auth():
            return
        path = self.path.split("?")[0]
        b = self._body()

        if path.endswith("/tap"):
            adb(["shell", "input", "tap", str(int(b.get("x", 0))), str(int(b.get("y", 0)))])
            return self._send(200, {"ok": True})

        if path.endswith("/swipe"):
            adb(["shell", "input", "swipe",
                 str(int(b.get("startX", 0))), str(int(b.get("startY", 0))),
                 str(int(b.get("endX", 0))), str(int(b.get("endY", 0))),
                 str(int(b.get("duration", 300)))])
            return self._send(200, {"ok": True})

        if path.endswith("/keyboard"):
            type_text(b.get("text", ""), bool(b.get("clear", False)))
            return self._send(200, {"ok": True})

        if path.endswith("/global"):
            code = {1: "4", 2: "3", 3: "187"}.get(b.get("action"), "4")  # back/home/recents
            adb(["shell", "input", "keyevent", code])
            return self._send(200, {"ok": True})

        if path.endswith("/key"):
            adb(["shell", "input", "keyevent", str(int(b.get("keycode", 4)))])
            return self._send(200, {"ok": True})

        if path.endswith("/deeplink"):
            url = b.get("url", "")
            if not url:
                return self._send(400, {"detail": "url required"})
            args = ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d",
                    "'" + url.replace("'", "'\\''") + "'"]
            if b.get("package"):
                args += ["-p", b["package"]]
            out = adb(args, timeout=30)
            return self._send(200, {"ok": "Error" not in out, "output": out})

        if path.endswith("/wake"):
            adb(["shell", "input", "keyevent", "224"])  # WAKEUP
            if b.get("stayon", True):
                adb(["shell", "svc", "power", "stayon", "true"])
            return self._send(200, {"ok": True})

        if path.endswith("/unlock"):
            r = unlock()
            return self._send(200 if r["ok"] else 409, r)

        if path.endswith("/reconnect"):
            serial = ensure_device(force=True)
            return self._send(200 if serial else 503,
                              {"ok": bool(serial), "serial": serial,
                               "detail": _last_error or None})

        if path.endswith("/shell"):
            if not ALLOW_SHELL:
                return self._send(403, {"detail":
                    "shell endpoint is disabled (it is arbitrary command execution). "
                    "Restart the bridge with PHONE_BRIDGE_ALLOW_SHELL=1 to enable."})
            cmd = b.get("cmd", "")
            if not cmd:
                return self._send(400, {"detail": "cmd required"})
            try:
                timeout = min(int(b.get("timeout", 60)), 300)
            except (TypeError, ValueError):
                timeout = 60
            return self._send(200, {"ok": True, "output": adb(["shell", cmd], timeout=timeout)})

        return self._send(404, {"detail": "not found"})

    def do_PUT(self):
        if not self._auth():
            return
        m = re.search(r"/apps/([^/?]+)$", self.path.split("?")[0])
        if m:
            adb(["shell", "monkey", "-p", m.group(1), "-c",
                 "android.intent.category.LAUNCHER", "1"], timeout=30)
            return self._send(200, {"ok": True})
        return self._send(404, {"detail": "not found"})


def main():
    if not shutil.which(ADB_BIN):
        sys.exit("adb not found. Install Android platform-tools "
                 "(macOS: brew install android-platform-tools).")
    if BIND not in ("127.0.0.1", "localhost", "::1") and not TOKEN:
        sys.exit(f"Refusing to listen on {BIND} without PHONE_BRIDGE_TOKEN. Anyone who "
                 "can reach this port could drive the phone. Set a token, or keep "
                 "BIND=127.0.0.1.")
    serial = ensure_device()
    print(f"adb-bridge {VERSION}: MobileRun-compatible API on http://{BIND}:{PORT}/v1")
    if serial:
        print(f"  device : {device_model()} (Android "
              f"{getprop('ro.build.version.release')}, serial {serial})")
    else:
        print(f"  device : NOT ATTACHED - {_last_error}")
        print("           (the bridge keeps running and picks the phone up when it appears)")
    print(f"  auth   : {'token required' if TOKEN else 'none (loopback only)'}")
    print(f"  shell  : {'ENABLED' if ALLOW_SHELL else 'disabled (default)'}")
    print(f"  CLI    : local-bridge/phonectl health")
    sys.stdout.flush()
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
