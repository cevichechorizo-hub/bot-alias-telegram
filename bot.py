#!/usr/bin/env python3
import os, logging, re, unicodedata, signal, sys, threading, time
from collections import defaultdict
from telebot import TeleBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips"
TARGET_GROUP_ID = -1003534894759

logger.info("🤖 BOT INICIANDO - V5 SIMPLE")
bot = TeleBot(BOT_TOKEN)
logger.info("✅ CONECTADO A TELEGRAM")

# Palabras prohibidas clave
BANNED_WORDS = {"sexo", "porno", "xxx", "pedofilia", "cepecito", "anal", "anus", "anilingus", 
"ape", "arsehole", "asshole", "asswipe", "bastard", "bitch", "cock", "cocksucker", "crap", 
"damn", "dick", "dickhead", "dildo", "douche", "fuck", "fucker", "fuckhead", "fucking", 
"fuckwad", "fuckwit", "goddamn", "goddamned", "hell", "horny", "horseshit", "jackass", 
"jerk", "jerkoff", "jism", "jizz", "motherfucker", "motherfucking", "piss", "pissed", 
"pissing", "pussy", "pussies", "shit", "shitass", "shithead", "shithole", "shitty", 
"slut", "slutty", "smutty", "snatch", "son", "sonofabitch", "taint", "tits", "titties", 
"tittyfucker", "titty", "twat", "twatwaffle", "wank", "wanker", "whore", "whored", 
"whores", "whoring", "whorishly", "whorishness"}

def normalize(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    for old, new in {'@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '$': 's'}.items():
        text = text.replace(old, new)
    return text

def has_banned_word(text):
    normalized = normalize(text)
    words = set(re.findall(r'\b\w+\b', normalized))
    for word in words:
        if word in BANNED_WORDS:
            return True, word
    return False, None

admin_cache = set()
admin_cache_time = 0

def get_admins():
    global admin_cache, admin_cache_time
    if time.time() - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = time.time()
        except: pass
    return admin_cache

user_warns = defaultdict(lambda: defaultdict(int))

def safe_delete(chat_id, message_id):
    try: bot.delete_message(chat_id, message_id)
    except: pass

@bot.message_handler(func=lambda msg: msg.chat.id == TARGET_GROUP_ID)
def handle_message(message):
    try:
        user = message.from_user
        if user.id in get_admins(): return
        
        if not user.username:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                msg_text = f"""⚠️ <b>{user.first_name or 'Usuario'}</b>, no tienes alias

<b>Problema:</b>
No puedes escribir sin un nombre de usuario.

<b>Solución:</b>
1. Abre tu perfil
2. Edita perfil
3. Busca "Nombre de usuario"
4. Crea tu alias
5. Guarda cambios"""
                notif = bot.send_message(message.chat.id, msg_text)
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"❌ {user.first_name} - Sin username")
            except Exception as e: logger.error(f"Error: {e}")
            return
        
        text = message.text or message.caption or ""
        if not text: return
        
        is_banned, word = has_banned_word(text)
        if is_banned:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                user_warns[user.id][message.chat.id] += 1
                warns = user_warns[user.id][message.chat.id]
                msg_text = f"""⚠️ <b>{user.first_name or 'Usuario'}</b>, contenido no permitido

<b>Advertencias:</b> {warns}/3"""
                if warns >= 3:
                    msg_text += "\n\n❌ <b>HAS SIDO EXPULSADO</b>"
                    try: bot.kick_chat_member(message.chat.id, user.id)
                    except: pass
                else:
                    msg_text += f"\n\nTe quedan {3 - warns} advertencia(s)."
                
                notif = bot.send_message(message.chat.id, msg_text)
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"❌ {user.first_name} - Palabra: '{word}'")
            except Exception as e: logger.error(f"Error: {e}")
            return
        
        if re.search(r'http[s]?://|www\.', text):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                msg_text = f"""⚠️ <b>{user.first_name or 'Usuario'}</b>, enlaces no permitidos

Los enlaces no están permitidos aquí."""
                notif = bot.send_message(message.chat.id, msg_text)
                threading.Timer(30, lambda: safe_delete(notif.chat.id, notif.message_id)).start()
                logger.info(f"❌ {user.first_name} - Enlace")
            except Exception as e: logger.error(f"Error: {e}")
            return
    except Exception as e: logger.error(f"Error: {e}")

def keepalive_loop():
    while True:
        try:
            time.sleep(30)
            logger.info("✅ Keepalive: Bot activo 24/7")
        except: pass

def signal_handler(sig, frame):
    logger.info("🛑 TERMINANDO")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    logger.info("🚀 POLLING INFINITO")
    keepalive_thread = threading.Thread(target=keepalive_loop, daemon=True)
    keepalive_thread.start()
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Error: {e}")
        signal_handler(None, None)
