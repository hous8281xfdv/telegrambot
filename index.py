import json
import telebot
import requests
import logging
import sys
import re
from http.server import BaseHTTPRequestHandler
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

TOKEN = "8684389209:AAEeBacmqyT-QRvRmIC-isJ4unHaShipicI"
WEBHOOK_URL = "https://telegrambot-ten-ivory.vercel.app"
DEEPSEEK_KEY = "sk-aebbd973b0964ae688f40ae1974792fc"

bot = telebot.TeleBot(TOKEN, threaded=False)

WELCOME_TEXT = """🚀 *БОТ-ГЕНЕРАТОР ЛЕНДИНГОВ + ЧАТ*

Привет! Я умею ДВЕ вещи:

🤖 *Просто пообщаться* — пиши что хочешь, я отвечу
🎨 *Создать лендинг* — напиши «Сделай лендинг для...»

📋 *Примеры:*
• «Привет, как дела?»
• «Сделай лендинг для пиццерии»
• «Расскажи анекдот»
• «Сайт для стоматологии, синий цвет»

⚡️ Работает быстро и БЕСПЛАТНО!"""

def ask_deepseek(prompt, is_landing=False):
    """Универсальный запрос к DeepSeek"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    
    if is_landing:
        system_prompt = """Ты — профессиональный веб-дизайнер. 
Создай КРАСИВЫЙ, СОВРЕМЕННЫЙ лендинг в одном HTML-файле.
Используй градиенты, тени, анимации, адаптивность.
Добавь кнопку "Заказать" или "Связаться".
ОТВЕЧАЙ ТОЛЬКО HTML-КОДОМ! НИКАКИХ ОБЪЯСНЕНИЙ!"""
    else:
        system_prompt = """Ты — дружелюбный помощник. 
Отвечай кратко, понятно, с эмодзи.
Будь вежливым и полезным."""

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7 if not is_landing else 0.8,
        "max_tokens": 4000 if is_landing else 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            if is_landing:
                content = re.sub(r'```html\n?', '', content)
                content = re.sub(r'```\n?', '', content)
            return content
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_messages(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    text_lower = text.lower()
    
    logger.info(f"📩 Сообщение от {chat_id}: {text}")
    
    # --- КОМАНДЫ ---
    if text_lower in ["привет", "здравствуй", "здравствуйте", "старт", "/start", "hello", "hi", "ку", "даров"]:
        bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
        return
    
    if text_lower in ["помощь", "help", "/help", "что умеешь", "команды"]:
        bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
        return
    
    # --- ГЕНЕРАЦИЯ ЛЕНДИНГА ---
    if "лендинг" in text_lower or "сайт" in text_lower or "сделай" in text_lower:
        if len(text) < 5:
            bot.send_message(chat_id, "❌ *Слишком короткий запрос.*\n\nОпишите подробнее, для чего вам нужен сайт.", parse_mode="Markdown")
            return
        
        status_msg = bot.send_message(chat_id, "⏳ *Генерирую лендинг...*\n\nDeepSeek работает, подожди 15-30 секунд.", parse_mode="Markdown")
        
        html_code = ask_deepseek(text, is_landing=True)
        
        if html_code and len(html_code) > 100:
            filename = f"landing_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_code)
            
            bot.send_document(
                chat_id,
                open(filename, "rb"),
                caption=f"✅ *Лендинг готов!*\n\n📝 Запрос: {text}\n\n💾 Сохраните файл и откройте в браузере.",
                parse_mode="Markdown"
            )
            
            bot.delete_message(chat_id, status_msg.message_id)
            bot.send_message(chat_id, "🎉 *Готово!* Если хотите другой стиль — просто напишите новый запрос!", parse_mode="Markdown")
            
            import os
            os.remove(filename)
        else:
            bot.edit_message_text(
                "❌ *Ошибка генерации.*\n\nDeepSeek временно недоступен. Попробуйте через 1-2 минуты или переформулируйте запрос.\n\n💡 Пример: «Сделай красивый лендинг для доставки суши»",
                chat_id,
                status_msg.message_id,
                parse_mode="Markdown"
            )
        return
    
    # --- ОБЫЧНОЕ ОБЩЕНИЕ ---
    status_msg = bot.send_message(chat_id, "🤔 *Думаю...*", parse_mode="Markdown")
    
    response = ask_deepseek(text, is_landing=False)
    
    if response:
        bot.edit_message_text(response, chat_id, status_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(
            "😅 *Ой, я затупил!*\n\nDeepSeek временно недоступен. Попробуй через минуту или напиши что-то попроще.",
            chat_id,
            status_msg.message_id,
            parse_mode="Markdown"
        )

HTML_PAGE = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Генератор Лендингов</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; background: #0a0a0a; padding: 50px; color: #fff; }}
        .card {{ background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); display: inline-block; max-width: 500px; border: 1px solid #333; }}
        h1 {{ background: linear-gradient(90deg, #f7971e, #ffd200); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2em; }}
        .status {{ background: #1a1a2e; padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #2a2a4e; }}
        .status span {{ color: #4ade80; }}
        .btn {{ background: linear-gradient(90deg, #f7971e, #ffd200); color: #000; border: none; padding: 15px 30px; font-size: 18px; border-radius: 12px; cursor: pointer; text-decoration: none; font-weight: bold; display: inline-block; width: 80%; margin-bottom: 15px; }}
        .btn:hover {{ transform: scale(1.05); }}
        .btn-alt {{ background: linear-gradient(90deg, #667eea, #764ba2); color: #fff; }}
        .btn-alt:hover {{ transform: scale(1.05); }}
        p {{ color: #888; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 Генератор Лендингов</h1>
        <div class="status">✅ <span>Бот активен</span><br>🤖 DeepSeek AI</div>
        <a href="/set-webhook" class="btn">🔄 Установить вебхук</a>
        <a href="https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}" target="_blank" class="btn btn-alt">🔗 Прямая ссылка</a>
        <p>📱 Просто напишите «Сделай лендинг для...»</p>
        <p style="font-size:12px; color:#555;">⚡ Генерация за 15-30 секунд</p>
    </div>
</body>
</html>"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/set-webhook':
            try:
                bot.remove_webhook()
                success = bot.set_webhook(url=WEBHOOK_URL)
                status = "✅ ВЕБХУК УСТАНОВЛЕН!" if success else "❌ Ошибка"
            except Exception as e:
                status = f"❌ Ошибка: {e}"
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"<h1>{status}</h1><a href='/'>Назад</a>".encode('utf-8'))
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode('utf-8'))
    
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            json_string = post_data.decode('utf-8')
            data = json.loads(json_string)
            
            if "business_message" in data:
                b_msg = data["business_message"]
                b_text = b_msg.get("text", "").strip()
                chat_id = b_msg.get("chat", {}).get("id")
                b_conn_id = b_msg.get("business_connection_id")
                
                if chat_id and b_conn_id and b_text:
                    text_lower = b_text.lower()
                    
                    if text_lower in ["привет", "здравствуй", "здравствуйте", "старт", "/start", "hello", "hi", "ку", "даров"]:
                        bot.send_message(
                            chat_id=chat_id,
                            text=WELCOME_TEXT,
                            parse_mode="Markdown",
                            business_connection_id=b_conn_id
                        )
                        return
                    
                    if "лендинг" in text_lower or "сайт" in text_lower or "сделай" in text_lower:
                        if len(b_text) < 5:
                            bot.send_message(
                                chat_id=chat_id,
                                text="❌ *Слишком короткий запрос.*\n\nОпишите подробнее, для чего вам нужен сайт.",
                                parse_mode="Markdown",
                                business_connection_id=b_conn_id
                            )
                            return
                        
                        status_msg = bot.send_message(
                            chat_id=chat_id,
                            text="⏳ *Генерирую лендинг...*\n\nDeepSeek работает, подожди 15-30 секунд.",
                            parse_mode="Markdown",
                            business_connection_id=b_conn_id
                        )
                        
                        html_code = ask_deepseek(b_text, is_landing=True)
                        
                        if html_code and len(html_code) > 100:
                            filename = f"landing_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                            
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(html_code)
                            
                            bot.send_document(
                                chat_id=chat_id,
                                document=open(filename, "rb"),
                                caption=f"✅ *Лендинг готов!*\n\n📝 Запрос: {b_text}\n\n💾 Сохраните файл и откройте в браузере.",
                                parse_mode="Markdown",
                                business_connection_id=b_conn_id
                            )
                            
                            bot.delete_message(chat_id, status_msg.message_id)
                            bot.send_message(
                                chat_id=chat_id,
                                text="🎉 *Готово!* Если хотите другой стиль — просто напишите новый запрос!",
                                parse_mode="Markdown",
                                business_connection_id=b_conn_id
                            )
                            
                            import os
                            os.remove(filename)
                        else:
                            bot.edit_message_text(
                                "❌ *Ошибка генерации.*\n\nDeepSeek временно недоступен. Попробуйте через 1-2 минуты или переформулируйте запрос.\n\n💡 Пример: «Сделай красивый лендинг для доставки суши»",
                                chat_id,
                                status_msg.message_id,
                                parse_mode="Markdown"
                            )
                        return
                    
                    status_msg = bot.send_message(
                        chat_id=chat_id,
                        text="🤔 *Думаю...*",
                        parse_mode="Markdown",
                        business_connection_id=b_conn_id
                    )
                    
                    response = ask_deepseek(b_text, is_landing=False)
                    
                    if response:
                        bot.edit_message_text(
                            response,
                            chat_id,
                            status_msg.message_id,
                            parse_mode="Markdown"
                        )
                    else:
                        bot.edit_message_text(
                            "😅 *Ой, я затупил!*\n\nDeepSeek временно недоступен. Попробуй через минуту или напиши что-то попроще.",
                            chat_id,
                            status_msg.message_id,
                            parse_mode="Markdown"
                        )
            else:
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                
        except Exception as e:
            logger.error(f"❌ Ошибка POST: {e}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
