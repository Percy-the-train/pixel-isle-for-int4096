"""API keys: env vars first, otherwise Fernet-encrypted in SQLite. Never returned in full."""
from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

from . import config, db


def _fernet() -> Fernet:
    config.ensure_dirs()
    if not config.KEY_FILE.exists():
        config.KEY_FILE.write_bytes(Fernet.generate_key())
        try:
            os.chmod(config.KEY_FILE, 0o600)
        except OSError:
            pass
    return Fernet(config.KEY_FILE.read_bytes())


def env_name(pid: str) -> str:
    return f"NEWSCRAWLER_{pid.upper()}_KEY"


def set_key(pid: str, key: str) -> None:
    db.set_setting(f"key:{pid}", _fernet().encrypt(key.strip().encode()).decode())


def delete_key(pid: str) -> None:
    db.delete_setting(f"key:{pid}")


def get_key(pid: str) -> str | None:
    env = os.environ.get(env_name(pid))
    if env:
        return env.strip()
    raw = db.get_setting(f"key:{pid}")
    if not raw:
        return None
    try:
        return _fernet().decrypt(raw.encode()).decode()
    except InvalidToken:
        return None


def mask(key: str) -> str:
    return "••••" if len(key) <= 6 else f"{key[:2]}••••••{key[-2:]}"


def masked_all(provider_ids) -> dict:
    out = {}
    for pid in provider_ids:
        k = get_key(pid)
        out[pid] = ({"masked": mask(k), "source": "env" if os.environ.get(env_name(pid)) else "stored"}
                    if k else None)
    return out