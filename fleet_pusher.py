#!/usr/bin/env python3
"""Push fleet health status to the Pico over USB serial.

The Pico has no WiFi, so this runs on the Mac (which can reach everything) and writes
one status line every few seconds to the Pico's USB CDC port. The Pico renders it.

    F|NAS:1:12:46C|VM:1:3|VPS:1:45|TS:22:41

Usage:
    python3 fleet_pusher.py                 # push every 5s until Ctrl-C
    python3 fleet_pusher.py --once          # push one line and exit
    python3 fleet_pusher.py --interval 10 --verbose
"""
import argparse
import os
import re
import select
import socket
import ssl
import subprocess
import sys
import termios
import time
import tty
import urllib.request

NAS_IP = os.environ.get("FLEET_NAS_IP", "192.168.1.57")
VM_IP = os.environ.get("FLEET_VM_IP", "192.168.1.130")
VPS_URL = os.environ.get("FLEET_VPS_URL", "https://www.persanz.online/health")
NAS_USER = os.environ.get("FLEET_NAS_USER", "persanz")
DEFAULT_PORT = os.environ.get("PICO_PORT", "/dev/cu.usbmodem101")


def tcp(host, port, timeout=3.0):
    t0 = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, int((time.time() - t0) * 1000)
    except OSError:
        return False, 0


def http_status(url, timeout=8.0):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fleet-pusher/1.0"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, int((time.time() - t0) * 1000)
    except Exception:
        return 0, 0


def nas_temp():
    try:
        out = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", f"{NAS_USER}@{NAS_IP}",
             "sensors 2>/dev/null | grep -m1 'Package id 0'"],
            capture_output=True, text=True, timeout=14).stdout
        m = re.search(r"\+(\d+(?:\.\d+)?)", out)
        return f"{m.group(1)}C" if m else ""
    except Exception:
        return ""


def build_line(verbose=False, include_fleet=False):
    lt = time.localtime()
    parts = []
    if include_fleet:
        nas_up, nas_ms = tcp(NAS_IP, 22)
        nas_extra = nas_temp() if nas_up else ""
        vm_ssh, vm_ms1 = tcp(VM_IP, 22)
        vm_web, vm_ms2 = tcp(VM_IP, 443)
        vm_ok = vm_ssh or vm_web
        vps_code, vps_ms = http_status(VPS_URL)
        parts += [
            "NAS:%d:%d%s" % (1 if nas_up else 0, nas_ms, (":" + nas_extra) if nas_extra else ""),
            "VM:%d:%d" % (1 if vm_ok else 0, max(vm_ms1, vm_ms2)),
            "VPS:%d:%d" % (1 if vps_code == 200 else 0, vps_ms),
        ]
        if verbose:
            print("  [fleet] NAS=%s VM=%s(%s/%s) VPS=%s(%s)" %
                  (nas_up, vm_ok, vm_ssh, vm_web, vps_code, vps_ms), flush=True)
    parts.append("DT:%04d-%02d-%02d:%02d:%02d:%02d:%d" %
                 (lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec, lt.tm_wday))
    parts.append("TS:" + time.strftime("%H:%M:%S"))
    return "S|" + "|".join(parts)


def resolve_port(dev):
    """Use the configured port if present, else the first USB CDC device found."""
    if os.path.exists(dev):
        return dev
    import glob
    cands = sorted(glob.glob("/dev/cu.usbmodem*")) + sorted(glob.glob("/dev/cu.usbserial*"))
    return cands[0] if cands else dev


def open_port(dev):
    dev = resolve_port(dev)
    if not os.path.exists(dev):
        raise FileNotFoundError(dev)
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    tty.setraw(fd)
    a = termios.tcgetattr(fd)
    a[4] = a[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=DEFAULT_PORT)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--fleet", action="store_true",
                    help="also check NAS/VM/VPS health (default: time sync only)")
    args = ap.parse_args()

    def push(fd):
        line = build_line(args.verbose, args.fleet)
        os.write(fd, (line + "\n").encode())
        if args.verbose:
            print("  -> " + line, flush=True)

    if args.once:
        fd = open_port(args.port)
        print(f"connected to {resolve_port(args.port)} @115200", flush=True)
        push(fd)
        time.sleep(0.5)
        try:
            print("  <- " + os.read(fd, 256).decode("utf-8", "replace").strip(), flush=True)
        except BlockingIOError:
            pass
        os.close(fd)
        return

    print(f"pushing every {args.interval}s (reconnects automatically) — Ctrl-C to stop", flush=True)
    while True:
        fd = None
        try:
            fd = open_port(args.port)
            print(f"{time.strftime('%H:%M:%S')} connected to {resolve_port(args.port)}", flush=True)
            push(fd)
            last = time.time()
            while True:
                r, _, _ = select.select([fd], [], [], 0.25)
                if r:
                    data = os.read(fd, 512).decode("utf-8", "replace")
                    if args.verbose and data.strip():
                        print("  <- pico: %r" % data.strip(), flush=True)
                    if "R" in data and time.time() - last >= 2.0:
                        print(f"{time.strftime('%H:%M:%S')} pico requested refresh", flush=True)
                        push(fd)
                        last = time.time()
                if time.time() - last >= args.interval:
                    push(fd)
                    last = time.time()
        except KeyboardInterrupt:
            print("\nstopped")
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
            return
        except OSError as e:
            print(f"{time.strftime('%H:%M:%S')} link lost ({e}) — retrying in 3s", flush=True)
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
            time.sleep(3)


if __name__ == "__main__":
    main()
