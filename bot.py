import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

REQUIRED_CHANNEL = "@SmartDownloader2030"

def check_membership(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception:
        pass
    return False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not check_membership(message.from_user.id):
        bot.reply_to(message, f"عذراً! يجب عليك الانضمام إلى مجموعتنا أولاً لاستخدام البوت:\n{REQUIRED_CHANNEL}")
        return
    bot.reply_to(message, "أهلاً بك في بوت التحميل الشامل! أرسل لي رابط فيديو من (يوتيوب، إنستغرام، تيك توك) وسأعطيك خيارات الدقة والصوت.")

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    if not check_membership(message.from_user.id):
        bot.reply_to(message, f"عذراً، لا يمكنك استخدام البوت قبل الانضمام إلى مجموعتنا:\n{REQUIRED_CHANNEL}")
        return

    url = message.text.strip()
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("فيديو (HD/مباشر)", callback_data=f"video|{url}"),
        InlineKeyboardButton("صوت فقط (MP3)", callback_data=f"mp3|{url}")
    )
    
    bot.reply_to(message, "اختر الصيغة المطلوبة للتحميل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data_parts = call.data.split('|', 1)
    if len(data_parts) != 2:
        return
    
    action, url = data_parts
    bot.answer_callback_query(call.id, "جاري بدء التحميل...")
    bot.edit_message_text("جاري معالجة الطلب عبر السيرفر، يرجى الانتظار...", call.message.chat.id, call.message.message_id)

    # إعدادات متقدمة لتجاوز حظر يوتيوب وضمان نجاح التحميل
    ydl_opts = {
        'outtmpl': 'downloaded_media.%(ext)s',
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }

    if action == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        bot.send_message(call.message.chat.id, "جاري إرسال الملف إليك...")
        with open(filename, 'rb') as f:
            if action == 'mp3':
                bot.send_audio(call.message.chat.id, f)
            else:
                bot.send_video(call.message.chat.id, f)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"حدث خطأ أثناء التحميل: تأكد من أن الرابط صحيح وعام.")

print("Bot is running...")
bot.infinity_polling(skip_pending=True, interval=2, timeout=20)
