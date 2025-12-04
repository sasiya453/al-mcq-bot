from flask import Flask, request
import telebot
import google.generativeai as genai
import os
import traceback # Added to see detailed errors

app = Flask(__name__)

# CONFIGURATION
# Make sure these match your Vercel Environment Variables exactly
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Setup Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    # Switched to 'gemini-pro' as it is more stable for text
    model = genai.GenerativeModel('gemini-pro')

# Setup Bot
if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Check if keys are missing
    if not GEMINI_KEY:
        bot.reply_to(message, "Error: GEMINI_API_KEY is missing in Vercel settings.")
        return
    if not TELEGRAM_TOKEN:
        bot.reply_to(message, "Error: TELEGRAM_TOKEN is missing in Vercel settings.")
        return

    try:
        # Send "Typing..." action so you know it received the message
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Generate response
        response = model.generate_content(message.text)
        
        # Reply
        bot.reply_to(message, response.text)
        
    except Exception as e:
        # detailed error handling
        error_msg = f"⚠️ Error: {str(e)}"
        print(error_msg) # Prints to Vercel logs
        bot.reply_to(message, error_msg) # Sends to Telegram

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
    return "Bot is running! Keys loaded: " + str(bool(GEMINI_KEY))
