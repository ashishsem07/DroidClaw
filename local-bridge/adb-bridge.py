#!/usr/bin/env python3
"""
ADB Bridge - a local drop-in replacement for the MobileRun REST API.

Speaks MobileRun's v1 dialect (the exact endpoints every agent RUN.md already
calls via curl) but executes everything over plain ADB against a locally
connected Android phone. No cloud, no API key, no subscription, no device slots.

Why this exists: MobileRun is a cloud relay on top of Android's own ADB +
accessibility. When the phone is on the same machine/network as the agents,
the relay buys nothing. This server removes the dependency entirely.

Usage:
    python3 local-bridge/adb-bridge.py            # auto-pick first physical device
    ADB_SERIAL=<device-serial> python3 local-bridge/adb-bridge.py
    PORT=8723 python3 local-bridge/adb-bridge.py

Then point the agents at it (one line, replaces the MobileRun base + key):
    export MOBILERUN_BASE="http://localhost:8723/v1"
    export MOBILERUN_API_KEY="local"        # ignored, kept so curls don't change
    export MOBILERUN_DEVICE_ID="local"      # ignored, path id is not used

Every existing curl in every RUN.md then works unchanged.

Endpoints implemented (MobileRun-compatible):
    GET  /v1/devices                          -> list (single local device, state ready)
    GET  /v1/devices/{id}                      -> device info
    GET  /v1/devices/{id}/screenshot           -> image/png
    GET  /v1/devices/{id}/ui-state?filter=true -> accessibility tree JSON ({"a11y_tree": ...})
    POST /v1/devices/{id}/tap        {"x","y"}
    POST /v1/devices/{id}/swipe      {"startX","startY","endX","endY","duration"}
    POST /v1/devices/{id}/keyboard   {"text","clear"}
    POST /v1/devices/{id}/global     {"action": 1=back 2=home 3=recents}
    PUT  /v1/devices/{id}/apps/{pkg}           -> launch app by package
"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8723"))


def pick_serial():
    """Use ADB_SERIAL if set, else the first non-emulator device."""
    forced = os.environ.get("ADB_SERIAL")
    if forced:
        return forced
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
    physical = []
    for line in out.splitlines()[1:]:
        if "\tdevice" not in line:
            continue
        serial = line.split("\t")[0].strip()
        if serial.startswith("emulator-") or serial.startswith("127.0.0.1"):
            continue
        physical.append(serial)
    if not physical:
        sys.exit("No physical ADB device found. Plug in the phone or set ADB_SERIAL.")
    return physical[0]


SERIAL = pick_serial()


def adb(args, binary=False, timeout=30):
    cmd = ["adb", "-s", SERIAL] + args
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if binary:
        return r.stdout
    return r.stdout.decode("utf-8", "replace")


def device_model():
    return adb(["shell", "getprop", "ro.product.model"]).strip() or "Android"


# ---- input helpers -------------------------------------------------------

def esc_text(t):
    """Escape text for `adb shell input text`. Spaces -> %s, shell metachars escaped."""
    t = t.replace("%", "%%") if False else t  # input text does not use %% ; keep literal
    # input text treats space specially; use %s. Escape characters the shell would eat.
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
        # move to end, then delete a generous amount in both directions
        adb(["shell", "input", "keyevent", "123"])  # MOVE_END
        dels = " ".join(["67"] * 200)               # KEYCODE_DEL (backspace)
        adb(["shell", "input", "keyevent"] + dels.split())
    if text:
        # chunk to avoid arg length limits; each chunk via one input text call
        for i in range(0, len(text), 200):
            chunk = text[i:i + 200]
            adb(["shell", "input", "text", esc_text(chunk)])


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
        "isClickable": clickable,
        "boundsInScreen": _bounds(el.get("bounds", "")),
        "children": [],
    }
    for child in el:
        c = _node(child, filtered)
        if c is not None:
            node["children"].append(c)
    if filtered:
        # drop nodes that carry no label and no labelled descendants and are not clickable
        if not text and not desc and not clickable and not node["children"]:
            return None
    return node


def ui_state(filtered):
    adb(["shell", "uiautomator", "dump", "/sdcard/wd.xml"], timeout=40)
    xml = adb(["exec-out", "cat", "/sdcard/wd.xml"], binary=True)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {"a11y_tree": {"text": "", "contentDescription": "", "isClickable": False,
                              "boundsInScreen": _bounds(""), "children": []}}
    # uiautomator root is <hierarchy>; descend to its content
    tree = _node(root, filtered) or {"text": "", "contentDescription": "",
                                     "isClickable": False, "boundsInScreen": _bounds(""),
                                     "children": []}
    return {"a11y_tree": tree}


# ---- HTTP ----------------------------------------------------------------

DEVICE_RE = re.compile(r"^/v1/devices/[^/]+")


class Handler(BaseHTTPRequestHandler):
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
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or "0")
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode() or "{}")
        except json.JSONDecodeError:
            return {}

    def _device_obj(self):
        return {
            "id": SERIAL, "name": device_model(), "state": "ready",
            "stateMessage": "connection established (adb-bridge)",
            "type": "adb_local", "billingStrategy": "none",
            "taskCount": 0, "activeTaskId": None, "userId": "local",
        }

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/v1/devices":
            return self._send(200, {
                "items": [self._device_obj()],
                "pagination": {"hasNext": False, "hasPrev": False, "page": 1,
                               "pageSize": 20, "total": 1, "pages": 1},
            })
        if path.endswith("/screenshot"):
            png = adb(["exec-out", "screencap", "-p"], binary=True)
            return self._send(200, png, ctype="image/png")
        if path.endswith("/ui-state"):
            filtered = "filter=true" in self.path
            return self._send(200, ui_state(filtered))
        if DEVICE_RE.match(path):  # GET /v1/devices/{id}
            return self._send(200, self._device_obj())
        return self._send(404, {"detail": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        b = self._body()
        if path.endswith("/tap"):
            adb(["shell", "input", "tap", str(b.get("x", 0)), str(b.get("y", 0))])
            return self._send(200, {"ok": True})
        if path.endswith("/swipe"):
            adb(["shell", "input", "swipe",
                 str(b.get("startX", 0)), str(b.get("startY", 0)),
                 str(b.get("endX", 0)), str(b.get("endY", 0)),
                 str(b.get("duration", 300))])
            return self._send(200, {"ok": True})
        if path.endswith("/keyboard"):
            type_text(b.get("text", ""), bool(b.get("clear", False)))
            return self._send(200, {"ok": True})
        if path.endswith("/global"):
            code = {1: "4", 2: "3", 3: "187"}.get(b.get("action"), "4")  # back/home/recents
            adb(["shell", "input", "keyevent", code])
            return self._send(200, {"ok": True})
        return self._send(404, {"detail": "not found"})

    def do_PUT(self):
        path = self.path.split("?")[0]
        m = re.search(r"/apps/([^/]+)$", path)
        if m:
            pkg = m.group(1)
            adb(["shell", "monkey", "-p", pkg, "-c",
                 "android.intent.category.LAUNCHER", "1"])
            return self._send(200, {"ok": True})
        return self._send(404, {"detail": "not found"})


if __name__ == "__main__":
    print(f"adb-bridge: serving MobileRun-compatible API on http://localhost:{PORT}/v1")
    print(f"            device: {device_model()}  (serial {SERIAL})")
    print(f"            point agents at: export MOBILERUN_BASE=http://localhost:{PORT}/v1")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
