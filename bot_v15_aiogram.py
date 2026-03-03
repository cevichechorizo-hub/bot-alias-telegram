#!/usr/bin/env python3
import asyncio, logging, re, unicodedata, signal, sys, time
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = "8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips"
TARGET_GROUP_ID = -1003534894759

logger.info("🤖 BOT V15 - AIOGRAM (ASYNC, SIN THREADING)")

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
    
    # NUEVAS PALABRAS PROHIBIDAS - USUARIO SOLICITÓ
    "cepe", "cepecito", "cepillo", "cepillin", "cepi", "cepita",
    "niñas", "niñitas", "niña", "niñita", "nenitas", "nenas",
    "camiones pesados", "camion pesado", "camiones", "camion", "pesados",
    "pdf", "p.d.f", "p d f",
    "grupo de mrd", "grupo de mierda", "grupo basura", "grupo de basura",
    "me largo del grupo", "largo del grupo", "me voy del grupo",
    "este grupo no pasa nada", "grupo no pasa nada", "no pasa nada aqui",
    "grupo mrd", "mrd", "mierda", "basura",
    
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

# Estado global
user_warns = defaultdict(lambda: defaultdict(int))
messages_to_delete = {}

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

async def delete_message_after_delay(bot, chat_id, message_id, delay=10):
    """Borra un mensaje después de X segundos"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
        logger.info(f"🗑️ Mensaje {message_id} borrado después de {delay}s")
    except Exception as e:
        logger.error(f"Error borrando mensaje: {e}")

async def message_handler(message: Message, bot: Bot):
    """Maneja mensajes del grupo"""
    try:
        # Solo procesar mensajes del grupo objetivo
        if message.chat.id != TARGET_GROUP_ID:
            return
        
        user = message.from_user
        
        # Obtener administradores
        try:
            admins = await bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_ids = {admin.user.id for admin in admins}
            if user.id in admin_ids:
                return
        except:
            pass
        
        # VERIFICACIÓN 1: USUARIO SIN ALIAS
        if not user.username:
            try:
                await bot.delete_message(message.chat.id, message.message_id)
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
                notif = await bot.send_message(message.chat.id, msg_text)
                asyncio.create_task(delete_message_after_delay(bot, notif.chat.id, notif.message_id, 10))
                logger.info(f"❌ {user.first_name} - Sin username")
            except Exception as e:
                logger.error(f"Error: {e}")
            return
        
        text = message.text or message.caption or ""
        if not text:
            return
        
        # VERIFICACIÓN 2: PALABRAS PROHIBIDAS
        is_banned, word = has_banned_word(text)
        if is_banned:
            try:
                await bot.delete_message(message.chat.id, message.message_id)
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
                    try:
                        await bot.ban_chat_member(message.chat.id, user.id)
                    except:
                        pass
                else:
                    remaining = 3 - warns
                    msg_text += f"""

📌 Te quedan {remaining} advertencia(s) antes de ser expulsado.

━━━━━━━━━━━━━━━━━━━━━"""
                
                notif = await bot.send_message(message.chat.id, msg_text)
                asyncio.create_task(delete_message_after_delay(bot, notif.chat.id, notif.message_id, 10))
                logger.info(f"❌ {user.first_name} - Palabra prohibida: '{word}'")
            except Exception as e:
                logger.error(f"Error: {e}")
            return
        
        # VERIFICACIÓN 3: ENLACES/URLS
        if re.search(r'http[s]?://|www\.', text):
            try:
                await bot.delete_message(message.chat.id, message.message_id)
                msg_text = """━━━━━━━━━━━━━━━━━━━━━
🔗 ENLACES NO PERMITIDOS

👤 Usuario

Tu mensaje fue eliminado porque contiene un enlace.

Los enlaces no están permitidos en este grupo.

━━━━━━━━━━━━━━━━━━━━━"""
                notif = await bot.send_message(message.chat.id, msg_text)
                asyncio.create_task(delete_message_after_delay(bot, notif.chat.id, notif.message_id, 10))
                logger.info(f"❌ {user.first_name} - Intento de enlace")
            except Exception as e:
                logger.error(f"Error: {e}")
            return
    except Exception as e:
        logger.error(f"Error general: {e}")

async def main():
    """Función principal"""
    logger.info("🚀 INICIANDO BOT V15 - AIOGRAM")
    logger.info(f"📊 Diccionario cargado: {len(BANNED_WORDS)} palabras prohibidas")
    
    # Crear bot y dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Registrar handler
    dp.message.register(lambda msg: message_handler(msg, bot))
    
    logger.info("✅ CONECTADO A TELEGRAM")
    
    try:
        logger.info("🚀 Iniciando polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Error en polling: {e}")
        await asyncio.sleep(5)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 BOT TERMINADO")
        sys.exit(0)
