#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
|                        MANUS - OBRA MAESTRA FINAL                       |
|--------------------------------------------------------------------------|
| Un bot de moderación para Telegram, diseñado para ser indestructible,    |
| infalible y eternamente vigilante. PURO POLLING - SIN DEPENDENCIAS.     |
|--------------------------------------------------------------------------|
| CARACTERÍSTICAS:                                                         |
|--------------------------------------------------------------------------|
|  ✅ INDESTRUCTIBLE: Previene múltiples instancias y se auto-recupera.    |
|  ✅ ETERNAMENTE ACTIVO: Polling infinito con timeout optimizado.         |
|  ✅ RESPUESTA INSTANTÁNEA: Latencia mínima, máxima eficiencia.           |
|  ✅ INTELIGENCIA SUPERIOR: Normalización avanzada de texto.              |
|  ✅ 870+ PALABRAS PROHIBIDAS: Base de conocimiento profesional.          |
|  ✅ CONTROL TOTAL: Warns, admin exempt, detección de enlaces.            |
|  ✅ CERO DEPENDENCIAS EXTRAS: Solo telebot y dotenv.                     |
============================================================================
"""

import os
import time
import logging
import threading
import re
import unicodedata
import signal
import sys
from collections import defaultdict

# Dependencias mínimas
from telebot import TeleBot
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN CENTRAL
# ============================================================================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", "-1001234567890"))
OWNER_ID = int(os.getenv("OWNER_ID", 0))

LOCK_FILE = "/tmp/bot_masterpiece.lock"
LOG_FILE = "bot_masterpiece.log"
BANNED_WORDS_FILE = "banned_words_complete.txt"

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("🔥 INICIANDO OBRA MAESTRA FINAL - BOT INDESTRUCTIBLE")
logger.info("=" * 70)

# ============================================================================
# GESTOR DE INSTANCIA ÚNICA
# ============================================================================
def check_and_acquire_lock():
    """Asegura que solo una instancia corra a la vez."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            logger.warning(f"Instancia previa detectada (PID: {old_pid}). Terminándola...")
            try:
                os.kill(old_pid, signal.SIGKILL)
                logger.info("Instancia previa terminada.")
                time.sleep(1)
            except ProcessLookupError:
                logger.info("Instancia previa ya no existía.")
        except Exception as e:
            logger.error(f"Error al procesar instancia previa: {e}")
    
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"✅ Cerrojo adquirido. PID: {os.getpid()}")
        return True
    except Exception as e:
        logger.error(f"Error al adquirir cerrojo: {e}")
        return False

def release_lock():
    """Libera el cerrojo al terminar."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
        logger.info("Cerrojo liberado.")
    except:
        pass

# ============================================================================
# INICIALIZAR BOT
# ============================================================================
try:
    bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
    logger.info("✅ Conexión con Telegram API establecida.")
except Exception as e:
    logger.critical(f"❌ Error al conectar con Telegram: {e}")
    sys.exit(1)

# ============================================================================
# BASE DE CONOCIMIENTO
# ============================================================================
BANNED_WORDS = set()

def load_banned_words():
    """Carga la lista de palabras prohibidas."""
    try:
        with open(BANNED_WORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    BANNED_WORDS.add(word)
        logger.info(f"✅ {len(BANNED_WORDS)} palabras prohibidas cargadas.")
    except FileNotFoundError:
        logger.warning("⚠️ Archivo de palabras prohibidas no encontrado.")
    except Exception as e:
        logger.error(f"Error al cargar palabras prohibidas: {e}")

# ============================================================================
# PROCESAMIENTO DE TEXTO
# ============================================================================
URL_PATTERN = re.compile(r'http[s]?://|www\.')

def normalize_text(text):
    """Normaliza texto para análisis inteligente."""
    if not text:
        return ""
    
    text = text.lower()
    # Descomponer acentos
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    
    # Reemplazos de l33t speak
    replacements = {'@': 'a', '4': 'a', '3': 'e', '1': 'i', '0': 'o', '5': 's', '$': 's'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def contains_banned_word(text):
    """Verifica si el texto contiene palabras prohibidas."""
    normalized = normalize_text(text)
    words = set(re.findall(r'\b\w+\b', normalized))
    
    for word in words:
        if word in BANNED_WORDS:
            return True, word
    return False, None

# ============================================================================
# LÓGICA DE MODERACIÓN
# ============================================================================
admin_cache = set()
admin_cache_time = 0
user_warns = defaultdict(lambda: defaultdict(int))

def get_admins():
    """Obtiene lista de admins con cache de 10 minutos."""
    global admin_cache, admin_cache_time
    
    if time.time() - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = time.time()
            logger.info(f"✅ Cache de admins actualizado. Total: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"Error actualizando admins: {e}")
    
    return admin_cache

def delete_and_notify(message, reason, is_username_violation=False):
    """Borra mensaje y envía notificación."""
    user = message.from_user
    
    try:
        bot.delete_message(message.chat.id, message.message_id)
        logger.info(f"Mensaje {message.message_id} de {user.first_name} ({user.id}) borrado. Razón: {reason}")
        
        if is_username_violation:
            text = f"<b>⚠️ {user.first_name}</b>, debes tener un @username para participar."
            notification = bot.send_message(message.chat.id, text)
            threading.Timer(30.0, lambda: safe_delete(notification.chat.id, notification.message_id)).start()
            return
        
        # Sistema de warns
        user_warns[user.id][message.chat.id] += 1
        warn_count = user_warns[user.id][message.chat.id]
        
        text = f"<b>⚠️ ADVERTENCIA - {user.first_name}</b>\n"
        text += f"<b>Razón:</b> {reason}\n"
        text += f"<b>Advertencias:</b> {warn_count}/3"
        
        if warn_count >= 3:
            text += "\n\n<b>❌ HAS SIDO EXPULSADO DEL GRUPO.</b>"
            try:
                bot.kick_chat_member(message.chat.id, user.id)
                logger.info(f"Usuario {user.id} expulsado por 3 advertencias.")
            except:
                pass
        
        notification = bot.send_message(message.chat.id, text)
        threading.Timer(30.0, lambda: safe_delete(notification.chat.id, notification.message_id)).start()
    
    except Exception as e:
        logger.error(f"Error en ciclo de moderación: {e}")

def safe_delete(chat_id, message_id):
    """Borra un mensaje de forma segura."""
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

@bot.message_handler(func=lambda message: message.chat.id == TARGET_GROUP_ID)
def moderate_message(message):
    """Núcleo del sistema de moderación."""
    user = message.from_user
    
    # Admins son inmunes
    if user.id in get_admins():
        return
    
    # 1. Verificar username
    if not user.username:
        delete_and_notify(message, "Sin @username", is_username_violation=True)
        return
    
    text = message.text or message.caption or ""
    if not text:
        return
    
    # 2. Verificar palabras prohibidas
    is_banned, word = contains_banned_word(text)
    if is_banned:
        delete_and_notify(message, f"Palabra no permitida: '{word}'")
        return
    
    # 3. Verificar enlaces
    if URL_PATTERN.search(text):
        delete_and_notify(message, "Enlaces no permitidos")
        return

# ============================================================================
# KEEPALIVE ETERNO
# ============================================================================
def keepalive_loop():
    """Mantiene el bot activo con logs periódicos."""
    while True:
        try:
            time.sleep(30)
            logger.info("✅ Keepalive: Bot activo y vigilante")
        except:
            pass

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
def main():
    """Función principal."""
    
    # Adquirir cerrojo
    if not check_and_acquire_lock():
        logger.error("No se pudo adquirir el cerrojo. Saliendo.")
        sys.exit(1)
    
    # Manejadores de señales
    def graceful_shutdown(signum, frame):
        logger.info("🛑 Recibida señal de terminación. Apagando gracefully...")
        bot.stop_polling()
        release_lock()
        logger.info("Bot detenido completamente.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    # Cargar base de conocimiento
    load_banned_words()
    
    # Iniciar keepalive en hilo separado
    keepalive_thread = threading.Thread(target=keepalive_loop, name="KeepaliveThread", daemon=True)
    keepalive_thread.start()
    logger.info("✅ Keepalive iniciado en hilo separado.")
    
    # Iniciar polling infinito
    logger.info("=" * 70)
    logger.info("🚀 INICIANDO POLLING INFINITO - BOT EN SERVICIO ACTIVO")
    logger.info("=" * 70)
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.critical(f"Error en polling: {e}")
    finally:
        graceful_shutdown(None, None)

if __name__ == "__main__":
    main()
