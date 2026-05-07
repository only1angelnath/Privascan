import asyncio
import structlog
from app.config import settings

log = structlog.get_logger()


async def main():
    log.info("bot.start", token_set=bool(settings.telegram_bot_token))
    log.info("bot.stub — handlers added Day 10-11")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
