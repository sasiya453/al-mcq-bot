from flask import Flask, request
import telebot
import google.generativeai as genai
import os
import traceback

app = Flask(__name__)

# CONFIGURATION
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Setup Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    
    # --- DIAGNOSTIC: PRINT AVAILABLE MODELS TO LOGS ---
    try:
        print("--- CHECKING AVAILABLE MODELS ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"AVAILABLE MODEL: {m.name}")
        print("--- END MODEL LIST ---")
    except Exception as e:
        print(f"Could not list models: {e}")
    # --------------------------------------------------

    # We will try the most specific versioned name which is safer
    # If this fails, check your Vercel Logs for the list above!
    model = genai.GenerativeModel('gemini-1.5-flash-001')

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if not GEMINI_KEY:
            bot.reply_to(message, "Error: GEMINI_API_KEY is missing.")
            return

        bot.send_chat_action(message.chat.id, 'typing')
        
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)

    except Exception as e:
        # Send the specific error to Telegram
        error_msg = f"⚠️ Error: {str(e)}"
        print(error_msg)
        bot.reply_to(message, error_msg)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Error', 403

@app.route('/')
def index():
    return "Bot is running. Check Vercel Logs for model list."
