import telebot
from telebot import types
import yt_dlp
import os
import random

TOKEN = '8615971353:AAHKiEOxYyIPabTKL8EQ7802zJ7bg8oTULQ'
bot = telebot.TeleBot(TOKEN, threaded=True, skip_pending=True)

REQUIRED_CHANNEL = '@SmartDownloader2030' 

# قاموس مؤقت لحفظ الروابط التي يرسلها المستخدمون
user_urls = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.reply_to(message, f"عذراً يا كريم، يجب عليك الاشتراك في المجموعة أولاً لتتمكن من استخدام البوت:\n{REQUIRED_CHANNEL}\n\nبعد الاشتراك، أرسل /start مرة أخرى.")
        return
    
    bot.reply_to(message, "مرحباً بك يا بطل! أرسل لي رابط الفيديو (يوتيوب، إنستغرام، إلخ) ثم اختر الجودة أو صيغة الصوت التي تريدها.")

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        bot.reply_to(message, f"عذراً، لا يمكنك استخدام البوت إلا بعد الاشتراك في المجموعة:\n{REQUIRED_CHANNEL}")
        return

    url = message.text
    if url.startswith("http"):
        # حفظ الرابط الخاص بالمرسل
        user_urls[user_id] = url
        
        # إنشاء أزرار تفاعلية تحت الرسالة
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_hd = types.InlineKeyboardButton("🎬 فيديو جودة عالية (HD)", callback_data="hd")
        btn_sd = types.InlineKeyboardButton("📱 فيديو جودة متوسطة (سريع)", callback_data="sd")
        btn_audio = types.InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data="audio")
        
        markup.add(btn_hd, btn_sd, btn_audio)
        
        bot.reply_to(message, "اختر الجودة أو الصيغة التي تريد تحكيلها:", reply_markup=markup)
    else:
        bot.reply_to(message, "يرجى إرسال رابط صالح يبدأ بـ http أو https.")

# التعامل مع ضغطات الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    
    if not check_subscription(user_id):
        bot.answer_callback_query(call.id, "يجب عليك الاشتراك في المجموعة أولاً!")
        return

    if user_id not in user_urls:
        bot.answer_callback_query(call.id, "انتهت جلسة الرابط، يرجى إعادة إرسال الرابط من جديد.")
        return

    url = user_urls[user_id]
    choice = call.data

    bot.answer_callback_query(call.id, "جاري بدء التحميل...")
    bot.edit_message_text("جاري معالجة وتحميل الطلب، يرجى الانتظار قليلاً...", chat_id=call.message.chat.id, message_id=call.message.message_id)

    if choice == "hd":
        file_name = f"video_hd_{random.randint(1000, 9999)}.mp4"
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_name,
            'socket_timeout': 60,
        }
        is_audio = False

    elif choice == "sd":
        file_name = f"video_sd_{random.randint(1000, 9999)}.mp4"
        ydl_opts = {
            'format': 'worst[ext=mp4]/worst',
            'outtmpl': file_name,
            'socket_timeout': 60,
        }
        is_audio = False

    elif choice == "audio":
        file_name = f"audio_{random.randint(1000, 9999)}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': file_name,
            'socket_timeout': 60,
        }
        is_audio = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.send_message(call.message.chat.id, "تم التحميل بنجاح، جاري الإرسال...")

        with open(file_name, 'rb') as file_data:
            if is_audio:
                bot.send_audio(call.message.chat.id, file_data, timeout=120)
            else:
                bot.send_video(call.message.chat.id, file_data, timeout=120)

        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"حدث خطأ أثناء التحميل أو الإرسال: {str(e)}")
        if os.path.exists(file_name):
            os.remove(file_name)

print("Bot is running with options...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)