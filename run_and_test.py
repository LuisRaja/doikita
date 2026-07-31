import asyncio, httpx, os, threading, time

token = os.environ["BOT_TOKEN"]

# Start bot in background thread
def start_bot():
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    os.chdir(os.path.dirname(__file__))
    from dotenv import load_dotenv
    load_dotenv()
    from service.telegram import run_bot
    run_bot()

t = threading.Thread(target=start_bot, daemon=True)
t.start()
time.sleep(3)

# Send a message to the bot
# First, get updates to find our chat_id
r = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
print("Updates:", r.json())

# Try sending a test message
# We need a chat_id - let's check if there are any pending
if r.json().get("result"):
    chat_id = r.json()["result"][0]["message"]["chat"]["id"]
    print(f"Found chat: {chat_id}")
else:
    print("No messages found. Send /start to the bot first.")
