import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# قراءة التوكن بأمان من متغيرات البيئة في ريلواي
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# معرف مجموعتك الإلزامي للاشتراك
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

    # إنشاء الأزرار التفاعلية لاختيار الدقة أو الصوت
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("فيديو عالي (HD)", callback_data=f"hd|{url}"),
        InlineKeyboardButton("فيديو منخفض (SD)", callback_data=f"sd|{url}"),
        InlineKeyboardButton("صوت فقط (MP3)", callback_data=f"mp3|{url}")
    )
    
    bot.reply_to(message, "اختر الجودة المطلوبة للتحميل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data_parts = call.data.split('|', 1)
    if len(data_parts) != 2:
        return
    
    action, url = data_parts
    bot.answer_callback_query(call.id, "جاري بدء التحميل...")
    bot.edit_message_text("جاري معالجة الطلب، يرجى الانتظار...", call.message.chat.id, call.message.message_id)

    ydl_opts = {}
    if action == 'hd':
        ydl_opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': 'video.%(ext)s'}
    elif action == 'sd':
        ydl_opts = {'format': 'worst', 'outtmpl': 'video.%(ext)s'}
    elif action == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'outtmpl': 'audio.%(ext)s'
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        bot.send_message(call.message.chat.id, "جاري إرسال الملف...")
        with open(filename, 'rb') as f:
            if action == 'mp3':
                bot.send_audio(call.message.chat.id, f)
            else:
                bot.send_video(call.message.chat.id, f)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"حدث خطأ أثناء التحميل: {str(e)}")

print("Bot is running...")
bot.infinity_polling(skip_pending=True)
