import logging
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import Executor
from aiogram.dispatcher.webhook import WebhookRequestHandler


TOKEN = os.getenv('5491700411:AAFo1W2J473h67HD6LMUHfK5s4Ar94MGhs0')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)


class MultiBotWebhookRequestHandler(WebhookRequestHandler):
	async def post(self):
		self.validate_ip()

		dispatcher = self.get_dispatcher()
		update = await self.parse_update(dispatcher.bot)

		with bot.with_token(self.request.match_info["token"]):
			results = await self.process_update(update)
		response = self.get_response(results)

		if response:
			web_response = response.get_web_response()
		else:
			web_response = web.Response(text="ok")

		if self.request.app.get("RETRY_AFTER", None):
			web_response.headers["Retry-After"] = self.request.app["RETRY_AFTER"]

		return web_response

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
executor = Executor(dp)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler()
async def echo(message: types.Message):
	# Regular request
	# await bot.send_message(message.chat.id, message.text)

	# or reply INTO webhook
	return SendMessage(message.chat.id, message.text)


async def on_startup(dp):
	# Setup bots webhok
	await bot.set_webhook(WEBHOOK_URL.format(token=TOKEN))
	with bot.with_token("another_token"):
		await bot.set_webhook(WEBHOOK_URL.format(token="another_token"))
	with bot.with_token("yet_another_token"):
		await bot.set_webhook(WEBHOOK_URL.format(token="yet_another_token"))


async def on_shutdown(dp):
	logging.warning('Shutting down..')

	# insert code here to run it before shutdown

	# Remove webhook (not acceptable in some cases)
	await bot.delete_webhook()
	with bot.with_token("another_token"):
		await bot.delete_webhook()
	with bot.with_token("yet_another_token"):
		await bot.delete_webhook()


	# Close DB connection (if used)
	await dp.storage.close()
	await dp.storage.wait_closed()

	logging.warning('Bye!')


if __name__ == '__main__':
	executor.start_webhook(
		webhook_path=WEBHOOK_PATH,
		on_startup=on_startup,
		on_shutdown=on_shutdown,
		host=WEBAPP_HOST,
		port=WEBAPP_PORT,
		request_handler=MultiBotWebhookRequestHandler
	)
