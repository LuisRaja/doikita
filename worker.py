from dotenv import load_dotenv
load_dotenv()

from service.scheduler import start_scheduler
from service.telegram import run_bot

if __name__ == "__main__":
    start_scheduler()
    run_bot()
