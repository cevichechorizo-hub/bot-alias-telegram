#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot de Telegram para verificar que los usuarios tengan username.
Borra mensajes de usuarios sin username y envía instrucciones.
"""

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
BOT_TOKEN = "8687327095:AAGn0C3_hJJJrf6oqcXf5kNZzuQ_X-D5pjA"
TARGET_GROUP_ID = -1003534894759

# Cache de admins
admin_cache = set()
admin_cache_time = 0

async def get_admins(context):
    """Obtener lista de admins del grupo."""
    global admin_cache, admin_cache_time
    import time
    
    current_time = time.time()
    # Actualizar cache cada 10 minutos
    if current_time - admin_cache_time > 600:
        try:
            admins = await context.bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = current_time
            logger.info(f"✅ Admins actualizados: {len(admin_cache)} admins")
        except Exception as e:
            logger.error(f"❌ Error obteniendo admins: {e}")
    
    return admin_cache

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes del grupo."""
    try:
        # Solo procesar mensajes del grupo objetivo
        if update.message.chat_id != TARGET_GROUP_ID:
            logger.debug(f"Mensaje de chat diferente: {update.message.chat_id}")
            return
        
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        
        logger.info(f"📨 Mensaje de usuario {user_id}, username: {username}")
        
        # Obtener admins
        admins = await get_admins(context)
        
        # Si es admin, permitir
        if user_id in admins:
            logger.info(f"✅ Usuario {user_id} es admin, permitiendo")
            return
        
        # Si tiene username, permitir
        if username:
            logger.info(f"✅ Usuario {user_id} tiene username '{username}', permitiendo")
            return
        
        # Si NO tiene username, actuar
        logger.warning(f"🚫 Usuario {user_id} SIN USERNAME - Borrando mensaje")
        
        # Borrar el mensaje
        try:
            await update.message.delete()
            logger.info(f"✅ Mensaje borrado")
        except Exception as e:
            logger.error(f"❌ Error borrando mensaje: {e}")
            return
        
        # Enviar notificación
        try:
            notification = await context.bot.send_message(
                chat_id=TARGET_GROUP_ID,
                text="<b>❌ No puedes enviar mensajes a este grupo porque no tienes un nombre de usuario.</b>\n\n"
                     "Para que puedas escribir, ponte un nombre de usuario.\n\n"
                     "Presiona el botón de abajo para ver las instrucciones 👇",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 Ver instrucciones", url="https://t.me/Aliaselmenchobot?start=help")]
                ])
            )
            logger.info(f"✅ Notificación enviada (ID: {notification.message_id})")
            
            # Borrar notificación después de 30 segundos
            async def delete_after_delay():
                await asyncio.sleep(30)
                try:
                    await context.bot.delete_message(TARGET_GROUP_ID, notification.message_id)
                    logger.info(f"✅ Notificación borrada")
                except Exception as e:
                    logger.debug(f"Error borrando notificación: {e}")
            
            asyncio.create_task(delete_after_delay())
        
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error en handle_message: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar comando /start."""
    try:
        logger.info(f"📨 /start de usuario {update.message.from_user.id}")
        
        message = await context.bot.send_message(
            chat_id=update.message.from_user.id,
            text="<b>📋 CÓMO CREAR TU NOMBRE DE USUARIO</b>\n\n"
                 "1️⃣ Abre Telegram → Toca tu foto de perfil\n"
                 "2️⃣ Toca 'Editar perfil'\n"
                 "3️⃣ Busca 'Nombre de usuario' (desplázate abajo)\n"
                 "4️⃣ Escribe tu nombre único (sin espacios, letras y números)\n"
                 "5️⃣ Toca el icono de verificación (✓)\n\n"
                 "<b>✅ ¡Listo! Ahora puedes escribir en el grupo.</b>",
            parse_mode='HTML'
        )
        
        logger.info(f"✅ Mensaje /start enviado")
        
        # Borrar mensaje después de 60 segundos
        async def delete_after_delay():
            await asyncio.sleep(60)
            try:
                await context.bot.delete_message(update.message.from_user.id, message.message_id)
                logger.info(f"✅ Mensaje /start borrado")
            except Exception as e:
                logger.debug(f"Error borrando mensaje /start: {e}")
        
        asyncio.create_task(delete_after_delay())
    
    except Exception as e:
        logger.error(f"❌ Error en /start: {e}")

async def main():
    """Función principal."""
    logger.info("=" * 70)
    logger.info("🤖 INICIANDO BOT DE TELEGRAM - VERIFICADOR DE USERNAME")
    logger.info(f"   Token: {BOT_TOKEN[:30]}...")
    logger.info(f"   Grupo: {TARGET_GROUP_ID}")
    logger.info("=" * 70)
    
    # Crear aplicación
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Agregar handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_message
    ))
    
    # Inicializar
    await app.initialize()
    logger.info("✅ Bot inicializado")
    
    # Iniciar
    await app.start()
    logger.info("✅ Bot iniciado")
    
    # Polling
    logger.info("📡 Iniciando polling...")
    await app.updater.start_polling(
        allowed_updates=["message"],
        drop_pending_updates=False
    )
    logger.info("✅ Polling activo - Bot listo para recibir mensajes")
    
    # Mantener corriendo
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        raise
