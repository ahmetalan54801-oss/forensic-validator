"""Zincir-i emanet (chain-of-custody) defteri.

Her kayıt bir öncekinin hash'ini içerir (blockchain'deki gibi basit bir hash
zinciri) — böylece dosya sonradan değiştirilirse zincir kırılır ve
`verify_chain` bunu tespit eder. Kriptografik olarak saldırıya dayanıklı bir
sistem değildir; amaç kazara/basit müdahaleyi görünür kılmaktır.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

GENESIS_HASH = "0" * 64


def _entry_hash(prev_hash: str, timestamp: str, actor: str, action: str, details: str) -> str:
    payload = f"{prev_hash}|{timestamp}|{actor}|{action}|{details}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_entries(ledger_path: Path) -> list[dict]:
    if not ledger_path.exists():
        return []
    entries = []
    with ledger_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def add_entry(ledger_path: str, actor: str, action: str, details: str = "") -> dict:
    path = Path(ledger_path)
    entries = _read_entries(path)
    prev_hash = entries[-1]["entry_hash"] if entries else GENESIS_HASH
    timestamp = datetime.now(timezone.utc).isoformat()

    entry_hash = _entry_hash(prev_hash, timestamp, actor, action, details)
    entry = {
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "details": details,
        "prev_hash": prev_hash,
        "entry_hash": entry_hash,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def verify_chain(ledger_path: str) -> dict:
    path = Path(ledger_path)
    entries = _read_entries(path)

    expected_prev = GENESIS_HASH
    for i, entry in enumerate(entries):
        if entry["prev_hash"] != expected_prev:
            return {"valid": False, "broken_at": i, "reason": "prev_hash uyuşmuyor"}

        recomputed = _entry_hash(
            entry["prev_hash"], entry["timestamp"], entry["actor"], entry["action"], entry["details"]
        )
        if recomputed != entry["entry_hash"]:
            return {"valid": False, "broken_at": i, "reason": "entry_hash uyuşmuyor (kayıt değiştirilmiş olabilir)"}

        expected_prev = entry["entry_hash"]

    return {"valid": True, "entry_count": len(entries)}


def list_entries(ledger_path: str) -> list[dict]:
    return _read_entries(Path(ledger_path))
