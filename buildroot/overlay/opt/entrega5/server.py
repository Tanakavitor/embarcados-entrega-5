#!/usr/bin/env python3
"""Entrega 5 web server for the DE10-Standard.

Serves the web page and a small JSON API. All hardware access goes through
the `hwctl` C daemon over a UNIX socket.

  GET  /              -> static/index.html
  GET  /api/status    -> {"led": 0|1, "button": 0|1, "imu": {"x","y","z"} | null}
  POST /api/led       -> body {"state": "on"|"off"|"toggle"}
  GET  /camera.jpg    -> one JPEG frame from the USB webcam (via fswebcam)
"""
import json
import os
import shutil
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

SOCKET_PATH = os.environ.get("HWCTL_SOCKET", "/tmp/entrega5.socket")
PORT = int(os.environ.get("PORT", "80"))
CAMERA_DEV = os.environ.get("CAMERA_DEV", "/dev/video0")
CAMERA_RES = os.environ.get("CAMERA_RES", "320x240")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

_hw_lock = threading.Lock()
_cam_lock = threading.Lock()


def hwctl(command):
    with _hw_lock:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(SOCKET_PATH)
            s.sendall((command + "\n").encode())
            reply = b""
            while not reply.endswith(b"\n"):
                chunk = s.recv(256)
                if not chunk:
                    break
                reply += chunk
    return reply.decode().strip()


def parse_kv(reply):
    return dict(item.split("=", 1) for item in reply.split() if "=" in item)


def read_status():
    kv = parse_kv(hwctl("STATUS"))
    imu = None
    if kv.get("IMU", "NA") != "NA":
        x, y, z = (int(v) for v in kv["IMU"].split(","))
        imu = {"x": x, "y": y, "z": z}
    return {"led": int(kv["LED"]), "button": int(kv["BTN"]), "imu": imu}


def capture_jpeg():
    if not os.path.exists(CAMERA_DEV):
        raise RuntimeError("no camera at " + CAMERA_DEV)
    if not shutil.which("fswebcam"):
        raise RuntimeError("fswebcam not installed")
    with _cam_lock:
        out = subprocess.run(
            ["fswebcam", "-q", "-d", CAMERA_DEV, "-r", CAMERA_RES,
             "--no-banner", "--jpeg", "80", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if out.returncode != 0 or not out.stdout:
        raise RuntimeError(out.stderr.decode(errors="replace").strip() or "capture failed")
    return out.stdout


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html"):
                with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            elif path == "/api/status":
                self._send(200, read_status())
            elif path == "/camera.jpg":
                try:
                    self._send(200, capture_jpeg(), "image/jpeg")
                except Exception as e:
                    self._send(503, {"error": str(e)})
            else:
                self._send(404, {"error": "not found"})
        except (OSError, KeyError, ValueError) as e:
            self._send(502, {"error": "hwctl unavailable: %s" % e})

    def do_POST(self):
        if self.path != "/api/led":
            return self._send(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            state = json.loads(self.rfile.read(length) or b"{}").get("state", "toggle")
            if state not in ("on", "off", "toggle"):
                return self._send(400, {"error": "state must be on, off or toggle"})
            hwctl("LED " + state.upper())
            self._send(200, read_status())
        except ValueError:
            self._send(400, {"error": "invalid JSON"})
        except (OSError, KeyError) as e:
            self._send(502, {"error": "hwctl unavailable: %s" % e})

    def log_message(self, fmt, *args):
        pass


class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    print("Entrega 5 web server on port %d (hwctl socket %s)" % (PORT, SOCKET_PATH), flush=True)
    ThreadingServer(("0.0.0.0", PORT), Handler).serve_forever()
