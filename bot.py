import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# جلب التوكن من متغيرات البيئة في ريلواي
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# مجموعة اشتراك الإجباري
REQUIRED_CHANNEL = "@SmartDownloader2030"

# قاموس مؤقت لتخزين الروابط لتجاوز حدود الأزرار
url_storage = {}

# دالة التحقق من اشتراك المستخدم في المجموعة
def check_membership(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
    except Exception:
        pass
    return False

# أمر البدء
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.reply_to(
            message, 
            f"⚠️ عذراً، يجب عليك الانضمام إلى قناتنا/مجموعتنا أولاً لتتمكن من استخدام البوت:\n{REQUIRED_CHANNEL}\n\nبعد الانضمام، أرسل /start مجدداً."
        )
        return
    
    bot.reply_to(
        message, 
        "أهلاً بك يا كريم في بوت التحميل الشامل 📥\n\nأرسل لي أي رابط فيديو من (يوتيوب، إنستغرام، تيك توك) وسأساعدك في تحميله بالشكل الذي تحبه!"
    )

# استقبال الروابط وتوليد خيارات الدقة والصوت
@bot.message_handler(func=lambda message: True)
def handle_url(message):
    user_id = message.from_user.id
    if not check_membership(user_id):
        bot.reply_to(
            message, 
            f"⚠️ عذراً، لا يمكنك استخدام البوت قبل الانضمام للمجموعة:\n{REQUIRED_CHANNEL}"
        )
        return

    url = message.text.strip()
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    # تخزين الرابط في الذاكرة المؤقتة باستخدام معرف المستخدم
    url_storage[user_id] = url

    # بناء الأزرار بالخيارات المطلوبة (دقات الفيديو والصوت)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎬 فيديو (جودة عالية HD)", callback_data="vid_high"),
        InlineKeyboardButton("🎬 فيديو (جودة متوسطة)", callback_data="vid_low"),
        InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data="audio_mp3")
    )

    bot.reply_to(message, "اختر الصيغة أو الجودة المناسبة للتحميل:", reply_markup=markup)

# معالجة الضغط على الأزرار وتنزيل الملف
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    action = call.data

    if user_id not in url_storage:
        bot.answer_callback_query(call.id, "انتهت صلاحية الرابط، أرسل الرابط من جديد.")
        return

    url = url_storage[user_id]
    bot.answer_callback_query(call.id, "جاري تجهيز التحميل...")
    bot.edit_message_text("⏳ جاري معالجة طلبك وتحميل الملف، يرجى الانتظار...", call.message.chat.id, call.message.message_id)

    # إعدادات yt-dlp حسب الخيار
    ydl_opts = {
        'outtmpl': 'downloaded_media.%(ext)s',
        'noplaylist': True,
    }

    if action == 'vid_high':
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif action == 'vid_low':
        ydl_opts['format'] = 'worst'
    elif action == 'audio_mp3':
        ydl_opts['format'] = 'bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == 'audio_mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        bot.send_message(call.message.chat.id, "📤 جاري إرسال الملف إليك الآن...")
        with open(filename, 'rb') as f:
            if action == 'audio_mp3':
                bot.send_audio(call.message.chat.id, f)
            else:
                bot.send_video(call.message.chat.id, f)

        # تنظيف الملف من السيرفر بعد الإرسال
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ حدث خطأ أثناء التحميل. تأكد أن الرابط عام وصحيح.")

# تشغيل البوت مع تنظيف الـ Webhook القديم وتخطي الرسائل المعلقة
print("Bot is running cleanly...")
bot.remove_webhook()
bot.infinity_polling(skip_pending=True)
