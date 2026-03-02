#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT FINAL V2 - NO DEPENDE DE .ENV
Usa variables de entorno de Railway directamente.
Si no existen, usa valores por defecto.
"""

import os
import logging
import re
import unicodedata
import signal
import sys
from collections import defaultdict
from telebot import TeleBot

# CONFIGURACIÓN - DIRECTA DE VARIABLES DE ENTORNO
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips"
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID") or "-1003534894759")

# LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("🤖 BOT INICIANDO")
logger.info(f"TOKEN: {BOT_TOKEN[:30]}...")
logger.info(f"GRUPO: {TARGET_GROUP_ID}")
logger.info("=" * 60)

# INICIALIZAR BOT
try:
    bot = TeleBot(BOT_TOKEN)
    logger.info("✅ CONECTADO A TELEGRAM API")
except Exception as e:
    logger.error(f"❌ ERROR DE CONEXIÓN: {e}")
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
except FileNotFoundError:
    logger.warning("⚠️ Archivo de palabras prohibidas no encontrado")
except Exception as e:
    logger.error(f"Error cargando palabras: {e}")

# FUNCIONES DE PROCESAMIENTO
def normalize(text):
    """Normaliza texto para análisis."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    replacements = {'@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '$': 's'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def has_banned_word(text):
    """Verifica si hay palabras prohibidas."""
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
    """Obtiene lista de admins con cache."""
    global admin_cache, admin_cache_time
    import time
    if time.time() - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = time.time()
            logger.info(f"✅ Admins actualizados: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"Error actualizando admins: {e}")
    return admin_cache

# WARNS
user_warns = defaultdict(lambda: defaultdict(int))

# MANEJADOR DE MENSAJES
@bot.message_handler(func=lambda msg: msg.chat.id == TARGET_GROUP_ID)
def handle_message(message):
    """Procesa cada mensaje en el grupo."""
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
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"Mensaje de {user.first_name} ({user.id}) borrado: Sin username")
            except Exception as e:
                logger.error(f"Error borrando mensaje sin username: {e}")
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
                    try:
                        bot.kick_chat_member(message.chat.id, user.id)
                        logger.info(f"Usuario {user.id} expulsado por 3 advertencias")
                    except:
                        pass
                
                notif = bot.send_message(message.chat.id, msg_text)
                import threading
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"Mensaje de {user.first_name} ({user.id}) borrado: Palabra '{word}'")
            except Exception as e:
                logger.error(f"Error procesando palabra prohibida: {e}")
            return
        
        # 3. VERIFICAR ENLACES
        if re.search(r'http[s]?://|www\.', text):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                notif = bot.send_message(message.chat.id, f"⚠️ {user.first_name}, no se permiten enlaces.")
                import threading
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"Mensaje de {user.first_name} ({user.id}) borrado: Contiene enlace")
            except Exception as e:
                logger.error(f"Error procesando enlace: {e}")
            return
    
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

def safe_delete(chat_id, message_id):
    """Borra un mensaje de forma segura."""
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# MANEJADOR DE SEÑALES
def signal_handler(sig, frame):
    logger.info("🛑 SEÑAL DE TERMINACIÓN RECIBIDA")
    bot.stop_polling()
    logger.info("Bot detenido completamente")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# PUNTO DE ENTRADA
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO POLLING INFINITO")
    logger.info("=" * 60)
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Error en polling: {e}")
        signal_handler(None, None)
