import json
import requests
from config import APPS_SCRIPT_URL


def append_transaction(data: dict) -> int | None:
    if not APPS_SCRIPT_URL:
        return None

    payload = {
        "tanggal": data.get("tanggal", ""),
        "user": data["user"],
        "tipe": data["type"],
        "deskripsi": data["description"],
        "jumlah": data["amount"],
        "metode": data.get("metode", ""),
    }

    try:
        resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        return resp.json().get("saldo")
    except Exception:
        return None
