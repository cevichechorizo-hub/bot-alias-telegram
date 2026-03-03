#!/usr/bin/env python3
import os, logging, re, unicodedata, signal, sys, time, threading
from collections import defaultdict
from telebot import TeleBot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips"
TARGET_GROUP_ID = -1003534894759

logger.info("🤖 BOT V12 - ELIMINACIÓN EN SEGUNDO PLANO")
bot = TeleBot(BOT_TOKEN, skip_pending=True)
logger.info("✅ CONECTADO A TELEGRAM")

# DICCIONARIO AMPLIO DE PALABRAS PROHIBIDAS
BANNED_WORDS = {
    # CONTENIDO SEXUAL EXPLÍCITO
    "sexo", "porno", "pornografía", "xxx", "anal", "anus", "anilingus", "asswipe",
    "bastard", "bitch", "cock", "cocksucker", "crap", "damn", "dick", "dickhead",
    "dildo", "douche", "fuck", "fucker", "fuckhead", "fucking", "fuckwad", "fuckwit",
    "goddamn", "goddamned", "hell", "horny", "horseshit", "jackass", "jerk", "jerkoff",
    "jism", "jizz", "motherfucker", "motherfucking", "piss", "pissed", "pissing",
    "pussy", "pussies", "shit", "shitass", "shithead", "shithole", "shitty", "slut",
    "slutty", "smutty", "snatch", "son", "sonofabitch", "taint", "tits", "titties",
    "tittyfucker", "titty", "twat", "twatwaffle", "wank", "wanker", "whore", "whored",
    "whores", "whoring", "whorishly", "whorishness", "cum", "cumshot", "blowjob",
    "handjob", "gangbang", "bukkake", "creampie", "squirt", "orgasm", "orgy",
    
    # EXPLOTACIÓN INFANTIL (CSAM/CP) - CRÍTICO
    "pedofilia", "pedófilo", "pedo", "cp", "csam", "child", "porn", "loli", "lolita",
    "shota", "shotacon", "kiddies", "kiddie", "child abuse", "child exploitation",
    "minor", "underage", "toddler", "infant", "baby", "little girl", "little boy",
    "grooming", "groomer", "pedo ring", "child trafficking", "child molester",
    "child predator", "jailbait", "barely legal", "teen porn", "young girls",
    "young boys", "preteen", "prepubescent", "pedofile", "kidporn", "childporn",
    
    # INSULTOS Y PALABRAS OFENSIVAS
    "arsehole", "asshole", "ape", "retard", "retarded", "stupid", "idiot", "dumb",
    "moron", "imbecile", "cretin", "halfwit", "dimwit", "blockhead", "bonehead",
    "dumbass", "dumbshit", "fuckface", "assface", "shitface", "cunt", "cunts",
    "nigger", "nigga", "faggot", "fag", "homo", "gay", "lesbian", "tranny",
    "whore", "slut", "bitch", "hoe", "ho", "prostitute", "escort",
    
    # VIOLENCIA Y AMENAZAS
    "kill", "murder", "rape", "assault", "attack", "bomb", "shoot", "stab",
    "violence", "violent", "threat", "threatening", "death threat", "rape threat",
    "i will kill", "i will rape", "i will hurt", "i will beat",
    
    # DISCRIMINACIÓN Y ODIO
    "racist", "racism", "sexist", "sexism", "homophobic", "transphobic",
    "nazi", "hitler", "klan", "white power", "white supremacy", "aryan",
    
    # DROGAS Y SUSTANCIAS ILEGALES
    "cocaine", "heroin", "meth", "methamphetamine", "fentanyl", "opioid",
    "lsd", "acid", "mdma", "ecstasy", "xanax", "viagra", "cialis",
    "weed", "marijuana", "cannabis", "pot", "hash", "hashish", "molly",
    "crack", "crystal", "ice", "speed", "amphetamine", "pcp", "ketamine",
    
    # VARIANTES Y OFUSCACIONES COMUNES
    "s3x", "s3xo", "p0rn", "p0rno", "xxx", "x3x", "pedo.", "ped0",
    "ch1ld", "ch1ld p0rn", "c.p", "c-p", "cp.", "csam.", "abuse",
    
    # SPAM Y CONTENIDO NO DESEADO
    "casino", "poker", "bet", "betting", "gambling", "slots", "roulette",
    "forex", "crypto scam", "bitcoin scam", "nft scam", "get rich quick",
    "click here", "buy now", "limited time", "act now", "urgent",
}

# Cola de mensajes a borrar: {(chat_id, msg_id): timestamp_expiration}
messages_to_delete = {}
delete_lock = threading.Lock()

def normalize(text):
    """Normaliza texto para detección robusta"""
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    replacements = {
        '@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '$': 's',
        '7': 't', '8': 'b', '9': 'g', '2': 'z', '!': 'i', '|': 'i',
        '.': '', '-': '', '_': '', ' ': '', ',': ''
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def has_banned_word(text):
    """Detecta palabras prohibidas con normalización"""
    normalized = normalize(text)
    words = set(re.findall(r'\b\w+\b', normalized))
    for word in words:
        if word in BANNED_WORDS:
            return True, word
    return False, None

admin_cache = set()
admin_cache_time = 0

def get_admins():
    """Obtiene lista de administradores con caché"""
    global admin_cache, admin_cache_time
    if time.time() - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = time.time()
        except: pass
    return admin_cache

user_warns = defaultdict(lambda: defaultdict(int))

def schedule_delete(chat_id, message_id, delay=10):
    """Programa un mensaje para ser borrado en 'delay' segundos"""
    with delete_lock:
        messages_to_delete[(chat_id, message_id)] = time.time() + delay

def background_delete_worker():
    """Thread en segundo plano que borra mensajes"""
    while True:
        try:
            time.sleep(1)  # Revisar cada segundo
            current_time = time.time()
            
            with delete_lock:
                to_delete = [(k, v) for k, v in messages_to_delete.items() if v <= current_time]
                
                for (chat_id, msg_id), _ in to_delete:
                    try:
                        bot.delete_message(chat_id, msg_id)
                        logger.info(f"🗑️ Mensaje {msg_id} borrado después de 10s")
                    except Exception as e:
                        logger.error(f"Error borrando {msg_id}: {e}")
                    finally:
                        if (chat_id, msg_id) in messages_to_delete:
                            del messages_to_delete[(chat_id, msg_id)]
        except Exception as e:
            logger.error(f"Error en background worker: {e}")

@bot.message_handler(func=lambda msg: msg.chat.id == TARGET_GROUP_ID)
def handle_message(message):
    try:
        user = message.from_user
        if user.id in get_admins(): return
        
        # VERIFICACIÓN 1: USUARIO SIN ALIAS
        if not user.username:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                msg_text = """━━━━━━━━━━━━━━━━━━━━━
⚠️ NOMBRE DE USUARIO REQUERIDO

👤 Hola Usuario

Este grupo requiere que todos los miembros tengan un nombre de usuario (@alias) para poder escribir.

📋 PASOS PARA CREAR TU ALIAS:

1. Abre tu perfil de Telegram
2. Toca en "Editar perfil"
3. Busca la opción "Nombre de usuario"
4. Crea un alias único
5. Guarda los cambios

Una vez que tengas alias, podrás escribir sin problemas.

━━━━━━━━━━━━━━━━━━━━━"""
                notif = bot.send_message(message.chat.id, msg_text)
                schedule_delete(notif.chat.id, notif.message_id, 10)
                logger.info(f"❌ {user.first_name} - Sin username")
            except Exception as e: logger.error(f"Error: {e}")
            return
        
        text = message.text or message.caption or ""
        if not text: return
        
        # VERIFICACIÓN 2: PALABRAS PROHIBIDAS
        is_banned, word = has_banned_word(text)
        if is_banned:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                user_warns[user.id][message.chat.id] += 1
                warns = user_warns[user.id][message.chat.id]
                
                msg_text = f"""━━━━━━━━━━━━━━━━━━━━━
🚫 CONTENIDO NO PERMITIDO

👤 {user.first_name or 'Usuario'}

Tu mensaje fue eliminado por contener contenido prohibido en este grupo.

⚠️ ADVERTENCIAS: {warns}/3"""
                
                if warns >= 3:
                    msg_text += f"""

━━━━━━━━━━━━━━━━━━━━━
❌ HAS SIDO EXPULSADO

Alcanzaste 3 advertencias y fuiste removido del grupo.
Si crees que es un error, contacta a los administradores.
━━━━━━━━━━━━━━━━━━━━━"""
                    try: bot.kick_chat_member(message.chat.id, user.id)
                    except: pass
                else:
                    remaining = 3 - warns
                    msg_text += f"""

📌 Te quedan {remaining} advertencia(s) antes de ser expulsado.

━━━━━━━━━━━━━━━━━━━━━"""
                
                notif = bot.send_message(message.chat.id, msg_text)
                schedule_delete(notif.chat.id, notif.message_id, 10)
                logger.info(f"❌ {user.first_name} - Palabra prohibida: '{word}'")
            except Exception as e: logger.error(f"Error: {e}")
            return
        
        # VERIFICACIÓN 3: ENLACES/URLS
        if re.search(r'http[s]?://|www\.', text):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                msg_text = """━━━━━━━━━━━━━━━━━━━━━
🔗 ENLACES NO PERMITIDOS

👤 Usuario

Tu mensaje fue eliminado porque contiene un enlace.

Los enlaces no están permitidos en este grupo.

━━━━━━━━━━━━━━━━━━━━━"""
                notif = bot.send_message(message.chat.id, msg_text)
                schedule_delete(notif.chat.id, notif.message_id, 10)
                logger.info(f"❌ {user.first_name} - Intento de enlace")
            except Exception as e: logger.error(f"Error: {e}")
            return
    except Exception as e: logger.error(f"Error general: {e}")

def signal_handler(sig, frame):
    logger.info("🛑 TERMINANDO BOT")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    logger.info("🚀 INICIANDO BOT V12 - ELIMINACIÓN EN SEGUNDO PLANO")
    logger.info(f"📊 Diccionario cargado: {len(BANNED_WORDS)} palabras prohibidas")
    
    # Iniciar thread de eliminación en segundo plano
    delete_thread = threading.Thread(target=background_delete_worker, daemon=True)
    delete_thread.start()
    logger.info("✅ Thread de eliminación iniciado")
    
    try:
        logger.info("🚀 Iniciando polling...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
    except Exception as e:
        logger.error(f"❌ Error en polling: {e}")
    except KeyboardInterrupt:
        signal_handler(None, None)
