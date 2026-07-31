import httpx, os

token = os.environ["BOT_TOKEN"]
r = httpx.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print(r.json())
