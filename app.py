import logging
import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from bot.handlers.commands import register_commands
from bot.handlers.events import register_events
from bot.scheduler import DeadlineScheduler
from bot.services.restaurant_service import RestaurantService
from bot.services.session_service import SessionService
from bot.storage import FileStore

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

data_dir = os.getenv("DATA_DIR", "./data")
store = FileStore(data_dir)
restaurant_service = RestaurantService(store)
scheduler = DeadlineScheduler()
session_service = SessionService(store, scheduler)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

register_commands(app, session_service, restaurant_service)
register_events(app, session_service)

if __name__ == "__main__":
    scheduler.start()
    logger.info("Starting lunch ordering bot (Socket Mode)")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
