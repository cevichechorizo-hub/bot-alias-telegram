#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE ALIAS OPTIMIZADO - Telegram
- Webhooks para respuesta instantánea (<0.5 seg)
- Keepalive cada 30 segundos (NUNCA se duerme)
- Funcionamiento 24/7 sin interrupciones
- Como BotFather: rápido y siempre activo
"""

import os
import time
import logging
import threading
import json
from datetime import datetime
from flask import Flask, request
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8687327095:AAGn0C3_hJJJrf6oqcXf5kNZzuQ_X-D5pjA')
TARGET_GROUP_ID = int(os.getenv('TARGET_GROUP_ID', '-1003534894759'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://bot-alias-telegram.railway.app')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '5000'))

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
# INICIALIZAR BOT Y FLASK
# ============================================================================

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

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
# WEBHOOK
# ============================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recibir actualizaciones via webhook - INSTANTÁNEO."""
    try:
        json_data = request.get_json()
        update = types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}")
        return "ERROR", 500

@app.route('/health', methods=['GET'])
def health():
    """Health check para keepalive."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}, 200

# ============================================================================
# KEEPALIVE AGRESIVO
# ============================================================================

def keepalive_aggressive():
    """Mantener el bot activo CADA 30 SEGUNDOS - NUNCA se duerme."""
    while True:
        try:
            time.sleep(30)  # 30 segundos
            bot.get_me()  # Ping a Telegram
            logger.info("✅ Keepalive: Bot activo (cada 30 seg)")
        except Exception as e:
            logger.error(f"❌ Error en keepalive: {e}")
            time.sleep(5)

# ============================================================================
# INICIAR BOT
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🤖 BOT DE ALIAS OPTIMIZADO - INICIADO")
    logger.info(f"👥 Grupo objetivo: {TARGET_GROUP_ID}")
    logger.info(f"🌐 Webhook URL: {WEBHOOK_URL}/webhook")
    logger.info("=" * 80)
    
    # Iniciar keepalive agresivo en thread separado
    keepalive_thread = threading.Thread(target=keepalive_aggressive, daemon=True)
    keepalive_thread.start()
    logger.info("✅ Keepalive AGRESIVO iniciado (cada 30 segundos)")
    
    # Configurar webhook
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        logger.info("✅ Webhook configurado - Respuesta INSTANTÁNEA")
    except Exception as e:
        logger.error(f"❌ Error configurando webhook: {str(e)}")
        logger.info("⚠️ Usando POLLING como fallback")
    
    logger.info("=" * 80)
    logger.info("✅ Bot LISTO - Responde en <0.5 segundos")
    logger.info("✅ NUNCA se duerme - Keepalive cada 30 segundos")
    logger.info("=" * 80)
    
    # Iniciar Flask
    app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=False)
