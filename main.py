import logging
import re
import requests
from bs4 import BeautifulSoup
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
import time
from contextlib import AsyncExitStack

Token = '6803252445:AAHIuRqEERFqHhJYNBPoxRIrRgdn58z-9pk'

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to updates."""
    chat_id = update.message.chat_id
    # context.chat_data["subscribers"].add(chat_id)
    context.bot_data.setdefault("subscribers", set()).add(chat_id)
    await update.message.reply_text("You are subscribed to updates.")


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from updates."""
    chat_id = update.message.chat_id
    subscribers = context.bot_data.get("subscribers", set())
    if chat_id in subscribers: # context.chat_data["subscribers"]:
        # context.chat_data["subscribers"].remove(chat_id)
        subscribers.remove(chat_id)
        await update.message.reply_text("You are unsubscribed from updates.")
    else:
        await update.message.reply_text("You are not subscribed to updates.")


# Function to get updates from the website
def get_updates():
    url = 'https://www.psoas.fi/en/apartments/?_sfm_htyyppi=p&_sfm_huoneistojen_tilanne=vapaa_ja_vapautumassa&_sfm_koko=7+84&_sfm_vuokra=161+761&_sfm_huonelkm=1+7#'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    container_div = soup.find("div", class_="huoneistohaku__lista__container")
    updates = []

    if container_div:
        apartment_divs = container_div.find_all("article", class_="card-huoneisto")

        for apartment_div in apartment_divs:
            title = apartment_div.find("span", class_="card-huoneisto__summary__nimi").text.strip()
            address = apartment_div.find("span", class_="card-huoneisto__summary__osoite").text.strip()
            descr = apartment_div.find('span', class_ = 'card-huoneisto__summary__report').text.strip()

            span_element = apartment_div.find("span", class_="card-huoneisto__summary__nimi")
            link = span_element.find("span").get("onclick")
            if link:
                # Extracting the URL from the onclick attribute
                url = re.search(r"\('([^']+)', '_self'\);", link)
                if url:
                    url = url.group(1)

            print(f"Title: {title}")
            print(f"Address: {address}")
            print(f'Description: {descr}')
            print(f"Link: {url}")
            print("----------")
            updates.append(f"{title}\n{address}\n{descr}\n{url}")
    return updates

# Function to send updates as messages
def send_updates(updates, context: ContextTypes.DEFAULT_TYPE):
    for update in updates:
        # context.bot.send_message(chat_id=context.job.context['chat_id'], text=update)
        context.bot.send_message(chat_id=context.job.context["chat_id"], text=update)

# функцию для периодической проверки обновлений:
# async def periodic_check(context):
#     while True:
#         updates = get_updates()
#         if updates:
#             for chat_id in context.chat_data["subscribers"]:
#                 await send_updates(updates, context, chat_id)
#         await asyncio.sleep(3600)  # Проверка каждый час
        
async def periodic_check():
    while True:
        updates = get_updates()
        if updates:
            for chat_id in subscribers:
                await send_updates(updates, chat_id)
        await asyncio.sleep(3600)  # Проверка каждый час

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    # await update.message.reply_html(
    #     rf"Hi {user.mention_html()}!",
    #     reply_markup=ForceReply(selective=True),
    # )
    await update.message.reply_text('Hi! I will notify you about new PSOAS apartment updates.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("SOS!")

async def schedule_job(chat_id, context):
    updates = get_updates()
    if updates:
        await context.bot.send_message(chat_id=chat_id, text="I have sent you the new apartment updates.")
        for update in updates:
            await context.bot.send_message(chat_id=chat_id, text=update)
    else:
        await context.bot.send_message(chat_id=chat_id, text="No new apartment updates found.")

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gives new choices"""
    if context.job:
        await update.message.reply_text('There is already a scheduled job.')
        return

    # Schedule the job
    asyncio.create_task(schedule_job(update.message.chat_id, context))
    await update.message.reply_text('Job scheduled successfully.')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


async def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Initialize subscribers set
    global subscribers
    subscribers = set()

    # Schedule periodic check
    asyncio.create_task(periodic_check())
    # stack.push_async_callback(application.job_queue.run_repeating, periodic_check, interval=3600)
    # stack.push_async_callback(periodic_check, application)

    # Create an event to wait for shutdown signal
    shutdown_event = asyncio.Event()

    # Run the bot until the user presses Ctrl-C
    # await application.run_polling(allowed_updates=Update.ALL_TYPES)

    try:
        # Run the bot until the user presses Ctrl-C
        # await application.initialize()
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        # await shutdown_event.wait()
    finally:
        await application.shutdown()

    # # Schedule periodic check
    # asyncio.create_task(periodic_check(application))

    # # Run the bot until the user presses Ctrl-C
    # application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # main()
    asyncio.run(main())