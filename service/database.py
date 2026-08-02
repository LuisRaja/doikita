from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime


def get_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def add_transaction(db: Client, user: str, ttype: str, category: str, amount: int, description: str, owner_pribadi: str = None) -> dict:
    data = {
        "user": user,
        "type": ttype,
        "category": category,
        "amount": amount,
        "description": description,
        "owner_pribadi": owner_pribadi,
    }
    result = db.table("transactions").insert(data).execute()
    return result.data[0]


def get_transactions(db: Client, limit: int = 50, user: str = None) -> list:
    query = db.table("transactions").select("*").order("created_at", desc=True).limit(limit)
    if user:
        query = query.eq("user", user)
    return query.execute().data


def get_transactions_by_month(db: Client, bulan: int, tahun: int, user: str = None) -> list:
    start = f"{tahun}-{bulan:02d}-01"
    if bulan == 12:
        end = f"{tahun + 1}-01-01"
    else:
        end = f"{tahun}-{bulan + 1:02d}-01"

    query = db.table("transactions").select("*").gte("created_at", start).lt("created_at", end)
    if user:
        query = query.eq("user", user)
    return query.order("created_at", desc=True).execute().data


def get_saldo(db: Client) -> list:
    return db.table("saldo").select("*").execute().data


def get_saldo_by_kategori(db: Client, kategori: str) -> int:
    result = db.table("saldo").select("saldo").eq("kategori", kategori).execute()
    if result.data:
        return result.data[0]["saldo"]
    return 0


def update_saldo(db: Client, kategori: str, amount: int):
    current = get_saldo_by_kategori(db, kategori)
    new_saldo = current + amount
    db.table("saldo").update({"saldo": new_saldo, "updated_at": datetime.utcnow().isoformat()}).eq("kategori", kategori).execute()


def init_saldo_if_not_exists(db: Client):
    defaults = [
        {"kategori": "bisnis", "saldo": 0},
        {"kategori": "pribadi_LUIS", "saldo": 0},
        {"kategori": "pribadi_HESTI", "saldo": 0},
    ]
    for d in defaults:
        existing = db.table("saldo").select("id").eq("kategori", d["kategori"]).execute()
        if not existing.data:
            db.table("saldo").insert(d).execute()


def add_rekapan(db: Client, bulan: int, tahun: int, user: str, total_masuk: int, total_keluar: int, saldo_akhir: int, pdf_link: str = None) -> dict:
    data = {
        "bulan": bulan,
        "tahun": tahun,
        "user": user,
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "saldo_akhir": saldo_akhir,
        "pdf_link": pdf_link,
    }
    result = db.table("rekapan").insert(data).execute()
    return result.data[0]


def get_rekapan(db: Client, bulan: int, tahun: int, user: str = None) -> list:
    query = db.table("rekapan").select("*").eq("bulan", bulan).eq("tahun", tahun)
    if user:
        query = query.eq("user", user)
    return query.execute().data


def get_telegram_auth(db: Client) -> dict:
    result = db.table("telegram_auth").select("user_id, mode, chat_id").execute()
    users = {}
    for row in result.data:
        users[str(row["user_id"])] = {
            "mode": row.get("mode"),
            "chat_id": row.get("chat_id") if row.get("chat_id") is not None else int(row["user_id"]),
        }
    return users


def save_telegram_auth(db: Client, users: dict):
    for uid_str, data in users.items():
        db.table("telegram_auth").upsert({
            "user_id": int(uid_str),
            "mode": data.get("mode"),
            "chat_id": data.get("chat_id", int(uid_str)),
        }).execute()

    existing = db.table("telegram_auth").select("user_id").execute()
    known = {str(row["user_id"]) for row in existing.data}
    for uid in known - set(users.keys()):
        db.table("telegram_auth").delete().eq("user_id", int(uid)).execute()


def get_saldo_dashboard(db: Client, user: str) -> dict:
    saldo_list = get_saldo(db)
    result = {}
    for s in saldo_list:
        result[s["kategori"]] = s["saldo"]

    if user == "LUIS":
        return {
            "bisnis": result.get("bisnis", 0),
            "pribadi": result.get("pribadi_LUIS", 0),
        }
    else:
        return {
            "bisnis": result.get("bisnis", 0),
            "pribadi": result.get("pribadi_HESTI", 0),
        }
