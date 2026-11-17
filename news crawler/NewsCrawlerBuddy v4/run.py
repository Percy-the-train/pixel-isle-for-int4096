"""Launcher.  Run:  python run.py   ->  opens http://127.0.0.1:8765"""
import os
import socket
import threading
import webbrowser

import uvicorn

from app.main import app


def _free_port(host: str, port: int) -> int:
    probe = "127.0.0.1" if host == "0.0.0.0" else host
    for p in range(port, port + 20):
        with socket.socket() as s:
            if s.connect_ex((probe, p)) != 0:  # nothing listening -> free
                return p
    return port


def main() -> None:
    host = os.environ.get("NCB_HOST", "127.0.0.1")
    port = _free_port(host, int(os.environ.get("NCB_PORT", "8765")))
    url = f"http://127.0.0.1:{port}"
    print(f"NewsCrawler Buddy is running at {url}   (Ctrl+C to quit)")
    if not os.environ.get("NCB_NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()