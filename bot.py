import os
import telebot
import yt_dlp

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت التحميل الذكي! أرسل لي رابط أي فيديو وسأقوم بتحميله لك فوراً.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    if not url.startswith('http'):
        bot.reply_to(message, "الرجاء إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    bot.reply_to(message, "جاري معالجة الطلب وتحميل الفيديو، يرجى الانتظار...")
    
    output_template = 'video.%(ext)s'
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        bot.reply_to(message, "جاري إرسال الفيديو...")
        with open(filename, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء التحميل: {str(e)}")

print("Bot is running...")
bot.infinity_polling(skip_pending=True)
