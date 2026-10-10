import os
import telebot
import yt_dlp

# استبدل هذا التوكن بتوكن بوتك الصحيح إذا لزم الأمر، أو سيتم سحبه تلقائياً
TOKEN = '8615971353:AAHKiEoXyYIPabTKL8EQ7802zJ7bg8oTULQ'
bot = telebot.TeleBot(8615971353:AAHKiEOxYyIPabTKL8EQ7802zJ7bg8oTULQ)

REQUIRED_CHANNEL = '@SmartDownloader2030'

# دالة التحقق من اشتراك المستخدم في القناة الإلزامية
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
    except Exception:
        pass
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if REQUIRED_CHANNEL and not check_subscription(user_id):
        bot.reply_to(
            message,
            f"⚠️ عذراً، يجب عليك الاشتراك في قناة البوت أولاً لكي تتمكن من استخدامه:\n@{REQUIRED_CHANNEL}\n\nبعد الاشترااك، اضغط على /start مرة أخرى."
        )
        return

    bot.reply_to(
        message,
        " أهلاً بك في بوت التحميل الذكي!\n\nأرسل لي أي رابط من (يوتيوب، إنستجرام، تيك توك) وسأقوم بتحميله وإرساله لك فوراً وبجودة عالية."
    )

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    user_id = message.from_user.id
    if REQUIRED_CHANNEL and not check_subscription(user_id):
        bot.reply_to(
            message,
            f"⚠️ يرجى الاشتراك في قناة البوت أولاً لتتمكن من استخدام الخدمة:\n@{REQUIRED_CHANNEL}"
        )
        return

    url = message.text.strip()
    if not url.startswith('http'):
        bot.reply_to(message, "❌ يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    msg = bot.reply_to(message, "⏳ جاري معالجة وتحميل الطلب، يرجى الانتظار قليلاً...")

    # إعدادات متطورة لـ yt-dlp لتجاوز الحظر والتحميل بسلاسة لجميع المنصات
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        # خيارات التخفي ومحاكاة المتصفح لتجاوز حظر يوتيوب وإنستجرام وتيك توك
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'socket_timeout': 30,
    }

    try:
        os.makedirs('downloads', exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if os.path.exists(filename):
            with open(filename, 'rb') as video_file:
                bot.send_video(message.chat.id, video_file, caption="✅ تم التحميل بنجاح بواسطة بوتك الخاص!")
            bot.delete_message(message.chat.id, msg.message_id)
            # حذف الملف بعد الإرسال لتوفير المساحة
            os.remove(filename)
        else:
            bot.edit_message_text("❌ حدث خطأ: لم يتم العثور على الملف المُحمل.", message.chat.id, msg.message_id)

    except Exception as e:
        error_msg = str(e)
        if "login" in error_msg.lower() or "rate-limit" in error_msg.lower():
            bot.edit_message_text("❌ عذراً، الرابط يتطلب تسجيل دخول أو أن المنصة فرضت تقييداً مؤقتاً، جرب رابطاً آخر.", message.chat.id, msg.message_id)
        else:
            bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل:\n{error_msg[:150]}", message.chat.id, msg.message_id)

if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
