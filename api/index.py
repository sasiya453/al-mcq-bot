from flask import Flask, request
import telebot
import google.generativeai as genai
import os
import traceback

app = Flask(__name__)

# CONFIGURATION
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Setup Gemini with the FLASH model (Fastest for bots)
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    # 1.5-flash is much faster than pro, preventing timeouts
    model = genai.GenerativeModel('gemini-1.5-flash')

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # 1. Send typing action
        bot.send_chat_action(message.chat.id, 'typing')

        # 2. Check for empty keys
        if not GEMINI_KEY:
            bot.reply_to(message, "Error: GEMINI_API_KEY is missing.")
            return

        # 3. Generate Content with a SAFETY TIMEOUT
        # We assume if it takes > 9 seconds, Vercel will kill it anyway.
        response = model.generate_content(message.text)
        
        # 4. Reply
        if response.text:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "I received an empty response from Gemini.")

    except Exception as e:
        # If it crashes, tell us why
        error_msg = f"⚠️ Error: {str(e)}"
        print(f"CRASH: {traceback.format_exc()}") # Check Vercel logs for this
        try:
            bot.reply_to(message, error_msg)
        except:
            # If we can't even reply, just print
            print("Could not send error message to Telegram.")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Standard webhook handler
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Error', 403

@app.route('/')
def index():
    return "Bot is alive."
