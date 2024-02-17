import logging
import re
import requests
from bs4 import BeautifulSoup
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, Updater, CallbackQueryHandler, CallbackContext
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
        context.bot.send_message(chat_id=context.job.context["chat_id"], text=update)

# Define a few command handlers. These usually take the two arguments update and
# context.
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Send a message when the command /start is issued."""
#     user = update.effective_user
#     # await update.message.reply_html(
#     #     rf"Hi {user.mention_html()}!",
#     #     reply_markup=ForceReply(selective=True),
#     # )
#     await update.message.reply_text('Hi! I will notify you about new PSOAS apartment updates.')

async def start(update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Check Updates", callback_data='check')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Hi! I will notify you about new PSOAS apartment updates.', reply_markup=reply_markup)
    # Планируем выполнение функции проверки каждые 10 минут
    asyncio.create_task(schedule_check(update.message.chat_id, context.bot))

# Function to handle inline button callbacks
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.message:
        await query.answer()
        if query.data == 'check':
            await check_command(query.message, context)  # Используем query.message здесь
        elif query.data == 'help':
            await query.message.edit_text(text="Here are the available commands:\n/check - Check for new updates")

async def schedule_job(chat_id, context):
    updates = get_updates()
    if updates:
        await context.bot.send_message(chat_id=chat_id, text="I have sent you the new apartment updates.")
        for update in updates:
            await context.bot.send_message(chat_id=chat_id, text=update)
    else:
        await context.bot.send_message(chat_id=chat_id, text="No new apartment updates found.")

async def check_command(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gives new choices"""
    if context.job:
        await message.reply_text('There is already a scheduled job.')
        return
    # Schedule the job
    asyncio.create_task(schedule_job(message.chat_id, context))  # Используем message.chat_id здесь
    await message.reply_text('Job scheduled successfully.')

# async def schedule_check(context: ContextTypes.DEFAULT_TYPE):
#     while True:
#         updates = get_updates()
#         if updates:
#             for update in updates:
#                 await context.bot.send_message(chat_id=context.job.context["chat_id"], text=update)
#         else:
#             await context.bot.send_message(chat_id=context.job.context["chat_id"], text="No new apartment updates found.")
#         await asyncio.sleep(60)  # Пауза в 600 секунд (10 минут)

async def schedule_check(chat_id, bot):
    while True:
        updates = get_updates()
        if updates:
            for update in updates:
                await bot.send_message(chat_id=chat_id, text=update)
        else:
            await bot.send_message(chat_id=chat_id, text="No new apartment updates found.")
        await asyncio.sleep(30)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(Token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    # application.run_polling(allowed_updates=Update.ALL_TYPES)
    application.run_polling()

if __name__ == "__main__":
    main()