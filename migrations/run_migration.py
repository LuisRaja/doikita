import os
from supabase import create_client

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]
db = create_client(url, key)

sql_path = os.path.join(os.path.dirname(__file__), "002_telegram_auth.sql")
with open(sql_path) as f:
    sql = f.read()

try:
    result = db.rpc("exec_sql", {"query": sql}).execute()
    print("Migration OK:", result)
except Exception as e:
    print("rpc failed, trying direct query:", e)
    # Fallback: run via REST API
    import httpx
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    # Can't execute raw SQL via REST, so try rpc
    print("Please run the SQL manually in Supabase SQL Editor")
