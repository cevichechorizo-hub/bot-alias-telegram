#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE ALIAS - Telegram
- POLLING PURO (sin Flask, sin webhooks)
- Keepalive cada 30 segundos
- Funcionamiento 24/7
"""
import os
import time
import logging
import threading
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
TARGET_GROUP_ID = int(os.getenv('TARGET_GROUP_ID'))

if not BOT_TOKEN or not TARGET_GROUP_ID:
    raise ValueError("❌ BOT_TOKEN o TARGET_GROUP_ID no configurados en .env")

LOG_FILE = "bot_alias.log"

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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
logger.info(f"✅ Bot inicializado con token: {BOT_TOKEN[:20]}...")
logger.info(f"✅ Grupo objetivo: {TARGET_GROUP_ID}")

# Cache de admins
admin_cache = {}
admin_cache_time = 0

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_admins():
    """Obtener administradores del grupo."""
    global admin_cache, admin_cache_time
    
    current_time = time.time()
    if current_time - admin_cache_time > 600:  # Actualizar cada 10 minutos
        try:
            admins = bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = current_time
            logger.info(f"✅ Admins actualizados: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo admins: {e}")
            return admin_cache
    
    return admin_cache


def delete_message_delayed(chat_id, message_id, delay=30):
    """Borrar mensaje después de X segundos."""
    def _delete():
        try:
            time.sleep(delay)
            bot.delete_message(chat_id, message_id)
            logger.info(f"✅ Mensaje {message_id} borrado después de {delay}s")
        except Exception as e:
            logger.debug(f"Error borrando mensaje: {e}")
    
    thread = threading.Thread(target=_delete, daemon=True)
    thread.start()


# ============================================================================
# MANEJADORES DE MENSAJES
# ============================================================================

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Comando /start y /help."""
    try:
        logger.info(f"📨 /start de usuario {message.from_user.id} (@{message.from_user.username})")
        
        response = (
            "<b>📋 CÓMO CREAR TU NOMBRE DE USUARIO</b>\n\n"
            "1️⃣ Abre Telegram → Toca tu foto de perfil\n"
            "2️⃣ Toca 'Editar perfil'\n"
            "3️⃣ Busca 'Nombre de usuario' (desplázate abajo)\n"
            "4️⃣ Escribe tu nombre único (sin espacios, letras y números)\n"
            "5️⃣ Toca el icono de verificación (✓)\n\n"
            "<b>✅ ¡Listo! Ahora puedes escribir en el grupo.</b>"
        )
        
        bot.send_message(message.from_user.id, response, parse_mode='HTML')
        logger.info(f"✅ Instrucciones enviadas a {message.from_user.id}")
    
    except Exception as e:
        logger.error(f"❌ Error en /start: {e}")


@bot.message_handler(content_types=['text'])
def handle_message(message):
    """Procesar mensajes de texto."""
    try:
        # Solo procesar mensajes del grupo objetivo
        if message.chat.id != TARGET_GROUP_ID:
            logger.debug(f"Ignorando mensaje de chat diferente: {message.chat.id}")
            return
        
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        message_text = (message.text[:50] if message.text else "[sin texto]")
        
        logger.info(f"📨 MENSAJE: Usuario {user_id} (@{username}): {message_text}")
        
        # Obtener admins
        admins = get_admins()
        
        # Si es admin, permitir
        if user_id in admins:
            logger.info(f"✅ Admin {user_id} permitido")
            return
        
        # Si tiene username, permitir
        if username:
            logger.info(f"✅ Usuario @{username} tiene alias - permitido")
            return
        
        # ⚠️ Usuario SIN username - ACCIÓN INMEDIATA
        logger.warning(f"🚫 USUARIO SIN USERNAME: {user_id} ({first_name})")
        
        # 1. BORRAR MENSAJE INMEDIATAMENTE
        try:
            bot.delete_message(TARGET_GROUP_ID, message.message_id)
            logger.info(f"✅ Mensaje {message.message_id} borrado")
        except Exception as e:
            logger.error(f"❌ Error borrando mensaje: {e}")
        
        # 2. ENVIAR NOTIFICACIÓN
        try:
            notification_text = (
                f"<b>⚠️ {first_name}</b>\n\n"
                f"<i>Debes tener un nombre de usuario para escribir en este grupo.</i>\n\n"
                f"Toca el botón abajo para ver instrucciones."
            )
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                text="📖 Ver instrucciones",
                url="https://t.me/Aliaselmenchobot?start=help"
            ))
            
            notification = bot.send_message(
                TARGET_GROUP_ID,
                notification_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
            logger.info(f"✅ Notificación enviada: {notification.message_id}")
            
            # 3. BORRAR NOTIFICACIÓN DESPUÉS DE 30 SEGUNDOS
            delete_message_delayed(TARGET_GROUP_ID, notification.message_id, delay=30)
        
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")


# ============================================================================
# KEEPALIVE
# ============================================================================

def keepalive_worker():
    """Mantener el bot activo cada 30 segundos."""
    logger.info("✅ Keepalive iniciado (cada 30 segundos)")
    while True:
        try:
            time.sleep(30)
            bot.get_me()
            logger.info("✅ Keepalive: Bot activo")
        except Exception as e:
            logger.error(f"❌ Error en keepalive: {e}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🤖 BOT DE ALIAS - INICIANDO")
    logger.info(f"👥 Grupo objetivo: {TARGET_GROUP_ID}")
    logger.info("=" * 80)
    
    # Iniciar keepalive en thread separado
    keepalive_thread = threading.Thread(target=keepalive_worker, daemon=True)
    keepalive_thread.start()
    
    logger.info("=" * 80)
    logger.info("✅ Bot LISTO")
    logger.info("✅ Usando POLLING PURO (sin Flask, sin webhooks)")
    logger.info("✅ Keepalive cada 30 segundos")
    logger.info("=" * 80)
    
    # Iniciar polling
    try:
        logger.info("🚀 Iniciando POLLING...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"❌ Error crítico en polling: {e}")
        time.sleep(5)
