#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Telegram para verificar usernames en grupo.
Basado en: https://github.com/aeither/telegram-bot-python
Usa telebot (pyTelegramBotAPI) - Mucho más simple y confiable para Railway.
"""

import os
import time
import logging
import telebot
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración
BOT_TOKEN = os.getenv('BOT_TOKEN', '8687327095:AAGn0C3_hJJJrf6oqcXf5kNZzuQ_X-D5pjA')
TARGET_GROUP_ID = int(os.getenv('TARGET_GROUP_ID', '-1003534894759'))

logger.info("=" * 80)
logger.info(f"BOT_TOKEN: {BOT_TOKEN[:30]}...")
logger.info(f"TARGET_GROUP_ID: {TARGET_GROUP_ID}")
logger.info("=" * 80)

# Cache de admins
admin_cache = {}
admin_cache_time = 0

def get_admins(bot):
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

try:
    # Crear bot
    bot = telebot.TeleBot(BOT_TOKEN)
    logger.info("✅ Bot inicializado")
    
    # CRUCIAL: Eliminar webhook para evitar conflictos con polling
    bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook eliminado")
    
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
    
    @bot.message_handler(func=lambda msg: True, content_types=['text'])
    def handle_message(message):
        """Procesar TODOS los mensajes de texto."""
        try:
            # Solo procesar mensajes del grupo objetivo
            if message.chat.id != TARGET_GROUP_ID:
                return
            
            user_id = message.from_user.id
            username = message.from_user.username
            message_text = (message.text[:50] if message.text else "[sin texto]")
            
            logger.info(f"📨 MENSAJE: Usuario {user_id} (@{username}): {message_text}")
            
            # Obtener admins
            admins = get_admins(bot)
            
            # Si es admin, permitir
            if user_id in admins:
                logger.info(f"✅ Admin permitido")
                return
            
            # Si tiene username, permitir
            if username:
                logger.info(f"✅ Usuario con username permitido")
                return
            
            # Usuario SIN username - ACTUAR
            logger.warning(f"🚫 USUARIO SIN USERNAME - ACCIONANDO")
            
            # Borrar mensaje
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje borrado")
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
                    reply_markup=telebot.types.InlineKeyboardMarkup([
                        [telebot.types.InlineKeyboardButton(
                            "📖 Ver instrucciones",
                            url="https://t.me/Aliaselmenchobot?start=help"
                        )]
                    ])
                )
                logger.info(f"✅ Notificación enviada")
                
                # Borrar notificación después de 30 segundos
                def delete_notification():
                    time.sleep(30)
                    try:
                        bot.delete_message(TARGET_GROUP_ID, notification.message_id)
                        logger.info(f"✅ Notificación borrada")
                    except Exception as e:
                        logger.debug(f"Error borrando notificación: {e}")
                
                import threading
                threading.Thread(target=delete_notification, daemon=True).start()
            
            except Exception as e:
                logger.error(f"❌ Error enviando notificación: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error en handle_message: {e}")
    
    # POLLING - Simple y confiable para Railway
    logger.info("=" * 80)
    logger.info("📡 Iniciando POLLING...")
    logger.info("✅ Bot LISTO para recibir mensajes")
    logger.info("✅ El bot NO se dormirá")
    logger.info("=" * 80)
    
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

except Exception as e:
    logger.error(f"❌ CRITICAL ERROR: Failed to initialize bot. Error: {e}")
    logger.error("The application will hang to prevent a restart loop.")
    while True:
        time.sleep(3600)
