import httpx, os, asyncio

token = os.environ["BOT_TOKEN"]

# Clear webhook + drop pending updates
r = httpx.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
print("deleteWebhook:", r.json())

# Get me
r = httpx.get(f"https://api.telegram.org/bot{token}/getMe")
print("getMe:", r.json())
