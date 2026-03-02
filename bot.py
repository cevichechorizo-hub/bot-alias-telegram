#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT ULTRA SIMPLE - SOLO FUNCIONALIDAD PURA
Sin complicaciones, sin errores, 100% confiable.
"""

import os
import logging
import re
import unicodedata
import signal
import sys
from collections import defaultdict
from dotenv import load_dotenv
from telebot import TeleBot

# CONFIGURACIÓN
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", "-1001234567890"))

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN no está configurado")
    sys.exit(1)

# LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info(f"🤖 BOT INICIANDO - TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"📍 GRUPO: {TARGET_GROUP_ID}")

# INICIALIZAR BOT
try:
    bot = TeleBot(BOT_TOKEN)
    logger.info("✅ BOT CONECTADO A TELEGRAM")
except Exception as e:
    logger.error(f"❌ ERROR AL CONECTAR: {e}")
    sys.exit(1)

# CARGAR PALABRAS PROHIBIDAS
BANNED_WORDS = set()
try:
    with open("banned_words_complete.txt", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word:
                BANNED_WORDS.add(word)
    logger.info(f"✅ {len(BANNED_WORDS)} palabras prohibidas cargadas")
except:
    logger.warning("⚠️ No se encontró archivo de palabras prohibidas")

# NORMALIZAR TEXTO
def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    for old, new in {'@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '$': 's'}.items():
        text = text.replace(old, new)
    return text

# VERIFICAR PALABRAS PROHIBIDAS
def has_banned_word(text):
    normalized = normalize(text)
    words = set(re.findall(r'\b\w+\b', normalized))
    for word in words:
        if word in BANNED_WORDS:
            return True, word
    return False, None

# CACHE DE ADMINS
admin_cache = set()
admin_cache_time = 0

def get_admins():
    global admin_cache, admin_cache_time
    import time
    if time.time() - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = time.time()
        except:
            pass
    return admin_cache

# WARNS
user_warns = defaultdict(lambda: defaultdict(int))

# MANEJADOR DE MENSAJES
@bot.message_handler(func=lambda msg: msg.chat.id == TARGET_GROUP_ID)
def handle_message(message):
    try:
        user = message.from_user
        
        # ADMINS SON INMUNES
        if user.id in get_admins():
            return
        
        # 1. VERIFICAR USERNAME
        if not user.username:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                notif = bot.send_message(
                    message.chat.id,
                    f"⚠️ {user.first_name}, necesitas un @username para escribir aquí."
                )
                import threading
                threading.Timer(30, lambda: bot.delete_message(notif.chat.id, notif.message_id)).start()
            except:
                pass
            return
        
        text = message.text or message.caption or ""
        if not text:
            return
        
        # 2. VERIFICAR PALABRAS PROHIBIDAS
        is_banned, word = has_banned_word(text)
        if is_banned:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                user_warns[user.id][message.chat.id] += 1
                warns = user_warns[user.id][message.chat.id]
                
                msg_text = f"⚠️ {user.first_name}, palabra no permitida.\nAdvertencias: {warns}/3"
                if warns >= 3:
                    msg_text += "\n❌ HAS SIDO EXPULSADO"
                    bot.kick_chat_member(message.chat.id, user.id)
                
                notif = bot.send_message(message.chat.id, msg_text)
                import threading
                threading.Timer(30, lambda: bot.delete_message(notif.chat.id, notif.message_id)).start()
            except:
                pass
            return
        
        # 3. VERIFICAR ENLACES
        if re.search(r'http[s]?://|www\.', text):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                notif = bot.send_message(message.chat.id, f"⚠️ {user.first_name}, no se permiten enlaces.")
                import threading
                threading.Timer(30, lambda: bot.delete_message(notif.chat.id, notif.message_id)).start()
            except:
                pass
            return
    
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

# MANEJADOR DE SEÑALES
def signal_handler(sig, frame):
    logger.info("🛑 BOT DETENIDO")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# INICIAR
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 POLLING INICIADO - BOT EN SERVICIO")
    logger.info("=" * 50)
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Error en polling: {e}")
        signal_handler(None, None)
