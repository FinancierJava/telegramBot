import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import router
import logging
from config import TOKEN


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
