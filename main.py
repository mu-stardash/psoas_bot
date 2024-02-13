import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Функция для получения обновлений с сайта
def get_updates():
    url = "https://www.psoas.fi/en/apartments/?_sfm_htyyppi=y&_sfm_huoneistojen_tilanne=vapaa_ja_vapautumassa&_sfm_koko=7+84&_sfm_vuokra=161+761&_sfm_huonelkm=1+7"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    apartments = soup.find_all("div", class_="apartment-card")
    updates = []
    for apartment in apartments:
        title = apartment.find("h2").text
        price = apartment.find("span", class_="price").text
        updates.append(f"{title}\n{price}")
    return updates

# Функция для отправки уведомлений
def send_updates(updates, context: CallbackContext):
    for update in updates:
        context.bot.send_message(chat_id=YOUR_CHAT_ID, text=update)

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hi! I will notify you about new apartment updates.')

# Функция для обработки команды /check
def check(update: Update, context: CallbackContext):
    updates = get_updates()
    if updates:
        send_updates(updates, context)
        update.message.reply_text('I have sent you the new apartment updates.')
    else:
        update.message.reply_text('No new apartment updates found.')

def main():
    updater = Updater("YOUR_BOT_TOKEN")

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("check", check))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
