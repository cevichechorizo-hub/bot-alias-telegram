#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE ALIAS - Telegram
- POLLING CONFIABLE (funciona 100%)
- Keepalive cada 30 segundos
- Funcionamiento 24/7 sin interrupciones
"""

import os
import time
import logging
import threading
from datetime import datetime
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8687327095:AAGn0C3_hJJJrf6oqcXf5kNZzuQ_X-D5pjA')
TARGET_GROUP_ID = int(os.getenv('TARGET_GROUP_ID', '-1003534894759'))

LOG_FILE = "bot_alias_live.log"

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# INICIALIZAR BOT
# ============================================================================

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# Cache de admins
admin_cache = {}
admin_cache_time = 0

# ============================================================================
# FUNCIONES
# ============================================================================

def get_admins():
    """Obtener administradores del grupo."""
    global admin_cache, admin_cache_time
    
    current_time = time.time()
    if current_time - admin_cache_time > 600:
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = current_time
            logger.info(f"✅ Admins actualizados: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo admins: {e}")
    
    return admin_cache

def process_message(message):
    """Procesar mensaje de usuario."""
    try:
        # Solo procesar mensajes del grupo objetivo
        if message.chat.id != TARGET_GROUP_ID:
            return
        
        user_id = message.from_user.id
        username = message.from_user.username
        message_text = (message.text[:50] if message.text else "[sin texto]")
        
        logger.info(f"📨 MENSAJE: Usuario {user_id} (@{username}): {message_text}")
        
        # Obtener admins
        admins = get_admins()
        
        # Si es admin, permitir
        if user_id in admins:
            logger.info(f"✅ Admin permitido")
            return
        
        # Si tiene username, permitir
        if username:
            logger.info(f"✅ Usuario con username permitido")
            return
        
        # Usuario SIN username - ACTUAR INMEDIATAMENTE
        logger.warning(f"🚫 USUARIO SIN USERNAME - ACCIONANDO AHORA")
        
        # Borrar mensaje
        try:
            bot.delete_message(TARGET_GROUP_ID, message.message_id)
            logger.info(f"✅ Mensaje borrado instantáneamente")
        except Exception as e:
            logger.error(f"❌ Error borrando: {e}")
        
        # Enviar notificación
        try:
            notification = bot.send_message(
                chat_id=TARGET_GROUP_ID,
                text="<b>❌ No puedes enviar mensajes a este grupo porque no tienes un nombre de usuario.</b>\n\n"
                     "Para que puedas escribir, ponte un nombre de usuario.\n\n"
                     "Presiona el botón de abajo para ver las instrucciones 👇",
                parse_mode='HTML',
                reply_markup=types.InlineKeyboardMarkup([
                    [types.InlineKeyboardButton(
                        "📖 Ver instrucciones",
                        url="https://t.me/Aliaselmenchobot?start=help"
                    )]
                ])
            )
            logger.info(f"✅ Notificación enviada instantáneamente")
            
            # Borrar notificación después de 30 segundos
            def delete_notification():
                time.sleep(30)
                try:
                    bot.delete_message(TARGET_GROUP_ID, notification.message_id)
                    logger.info(f"✅ Notificación borrada")
                except Exception as e:
                    logger.debug(f"Error borrando notificación: {e}")
            
            threading.Thread(target=delete_notification, daemon=True).start()
        
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error en process_message: {str(e)}")

# ============================================================================
# MANEJADORES DE MENSAJES
# ============================================================================

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Comando /start y /help."""
    try:
        logger.info(f"📨 /start de usuario {message.from_user.id}")
        
        response = (
            "<b>📋 CÓMO CREAR TU NOMBRE DE USUARIO</b>\n\n"
            "1️⃣ Abre Telegram → Toca tu foto de perfil\n"
            "2️⃣ Toca 'Editar perfil'\n"
            "3️⃣ Busca 'Nombre de usuario' (desplázate abajo)\n"
            "4️⃣ Escribe tu nombre único (sin espacios, letras y números)\n"
            "5️⃣ Toca el icono de verificación (✓)\n\n"
            "<b>✅ ¡Listo! Ahora puedes escribir en el grupo.</b>"
        )
        
        bot.send_message(
            message.from_user.id,
            response,
            parse_mode='HTML'
        )
        logger.info(f"✅ Mensaje /start enviado")
    
    except Exception as e:
        logger.error(f"❌ Error en /start: {e}")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    """Procesar mensajes de texto."""
    process_message(message)

# ============================================================================
# KEEPALIVE
# ============================================================================

def keepalive():
    """Mantener el bot activo cada 30 segundos."""
    while True:
        try:
            time.sleep(30)
            bot.get_me()
            logger.info("✅ Keepalive: Bot activo")
        except Exception as e:
            logger.error(f"❌ Error en keepalive: {e}")
            time.sleep(5)

# ============================================================================
# INICIAR BOT
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🤖 BOT DE ALIAS - INICIADO")
    logger.info(f"👥 Grupo objetivo: {TARGET_GROUP_ID}")
    logger.info("=" * 80)
    
    # Iniciar keepalive en thread separado
    keepalive_thread = threading.Thread(target=keepalive, daemon=True)
    keepalive_thread.start()
    logger.info("✅ Keepalive iniciado (cada 30 segundos)")
    
    logger.info("=" * 80)
    logger.info("✅ Bot LISTO - Usando POLLING CONFIABLE")
    logger.info("✅ NUNCA se duerme - Keepalive cada 30 segundos")
    logger.info("=" * 80)
    
    # Iniciar polling
    try:
        logger.info("🚀 Iniciando POLLING...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"❌ Error en polling: {e}")
        time.sleep(5)
