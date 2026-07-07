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

WELCOME_TEXT = """🚀 *БОТ-ГЕНЕРАТОР ЛЕНДИНГОВ*

Привет! Я создаю красивые лендинги за 30 секунд!

📝 *Что нужно сделать:*
1. Напишите *для чего* вам сайт
2. Укажите *цветовую гамму* (опционально)
3. Получите готовый HTML-код!

📋 *Примеры запросов:*
• «Сделай лендинг для пиццерии»
• «Сайт для стоматологии, синий цвет»
• «Лендинг для курсов английского, яркий стиль»
• «Сайт для свадебного фотографа»

⚡️ Работает быстро и БЕСПЛАТНО!"""

HELP_TEXT = """📖 *КАК РАБОТАТЬ:*

1️⃣ Напишите цель вашего лендинга
2️⃣ Добавьте пожелания по дизайну
3️⃣ Получите готовый HTML код

🎨 *Примеры:*
• «Красивый лендинг для доставки суши»
• «Сайт для фитнес-клуба, тёмный стиль»
• «Лендинг для онлайн-школы, светлый»

💡 Чем подробнее опишете — тем лучше результат!"""

def generate_landing(prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """Ты — профессиональный веб-дизайнер и разработчик. 
Создавай красивые, современные лендинги в одном HTML-файле.

Требования:
1. ВСЁ в одном HTML-файле (CSS внутри <style>)
2. Современный дизайн с градиентами, тенями, анимациями
3. Адаптивность под все экраны
4. Контактная информация, кнопка "Связаться" или "Заказать"
5. Используй эмодзи для украшения
6. Чистый, читаемый код

ОТВЕЧАЙ ТОЛЬКО HTML-КОДОМ, БЕЗ ЛИШНИХ СЛОВ!"""
    
    user_prompt = f"""Создай современный лендинг для: {prompt}

Сделай стильным, красивым, с градиентами и анимациями.
Обязательно добавь кнопку призыва к действию.
Код должен быть полностью рабочим."""

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            html_code = result["choices"][0]["message"]["content"]
            html_code = re.sub(r'```html\n?', '', html_code)
            html_code = re.sub(r'```\n?', '', html_code)
            return html_code
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
    
    if text_lower in ["привет", "здравствуй", "здравствуйте", "старт", "/start", "hello", "hi", "ку", "даров"]:
        bot.send_message(chat_id, WELCOME_TEXT, parse_mode="Markdown")
        return
    
    if text_lower in ["помощь", "help", "/help", "что умеешь", "команды"]:
        bot.send_message(chat_id, HELP_TEXT, parse_mode="Markdown")
        return
    
    if len(text) < 5:
        bot.send_message(chat_id, "❌ *Слишком короткий запрос.*\n\nОпишите подробнее, для чего вам нужен лендинг.", parse_mode="Markdown")
        return
    
    status_msg = bot.send_message(chat_id, "⏳ *Генерирую лендинг...*\n\nЭто займёт 15-30 секунд.", parse_mode="Markdown")
    
    html_code = generate_landing(text)
    
    if html_code:
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
            "❌ *Ошибка генерации.*\n\nПопробуйте переформулировать запрос или написать подробнее.",
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
                    if len(b_text) < 5:
                        bot.send_message(
                            chat_id=chat_id,
                            text="❌ *Слишком короткий запрос.*\n\nОпишите подробнее, для чего вам нужен лендинг.",
                            parse_mode="Markdown",
                            business_connection_id=b_conn_id
                        )
                        return
                    
                    status_msg = bot.send_message(
                        chat_id=chat_id,
                        text="⏳ *Генерирую лендинг...*\n\nЭто займёт 15-30 секунд.",
                        parse_mode="Markdown",
                        business_connection_id=b_conn_id
                    )
                    
                    html_code = generate_landing(b_text)
                    
                    if html_code:
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
                            "❌ *Ошибка генерации.*\n\nПопробуйте переформулировать запрос или написать подробнее.",
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
