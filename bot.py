#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
BOT_TOKEN = os.getenv("BOT_TOKEN", "8687327095:AAGn0C3_hJJJrf6oqcXf5kNZzuQ_X-D5pjA")
TARGET_GROUP_ID = int(os.getenv("TARGET_GROUP_ID", "-1003534894759"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8000"))

# Cache de admins
admin_cache = {}
admin_cache_time = 0

async def get_admins(context):
    """Obtener administradores del grupo."""
    global admin_cache, admin_cache_time
    import time
    
    current_time = time.time()
    # Actualizar cada 10 minutos
    if current_time - admin_cache_time > 600:
        try:
            admins = await context.bot.get_chat_administrators(TARGET_GROUP_ID)
            admin_cache = {admin.user.id for admin in admins}
            admin_cache_time = current_time
            logger.info(f"✅ Admins actualizados: {len(admin_cache)}")
        except Exception as e:
            logger.error(f"❌ Error obteniendo admins: {e}")
    
    return admin_cache

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesar TODOS los mensajes del grupo."""
    try:
        # Solo procesar mensajes del grupo objetivo
        if update.message.chat_id != TARGET_GROUP_ID:
            return
        
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        message_text = update.message.text[:50] if update.message.text else "[sin texto]"
        
        logger.info(f"📨 MENSAJE: Usuario {user_id} (@{username}): {message_text}")
        
        # Obtener admins
        admins = await get_admins(context)
        
        # Si es admin, permitir
        if user_id in admins:
            logger.info(f"✅ Admin permitido")
            return
        
        # Si tiene username, permitir
        if username:
            logger.info(f"✅ Usuario con username permitido")
            return
        
        # Si NO tiene username, ACTUAR INMEDIATAMENTE
        logger.warning(f"🚫 USUARIO SIN USERNAME - ACCIONANDO")
        
        # Borrar el mensaje
        try:
            await update.message.delete()
            logger.info(f"✅ Mensaje borrado")
        except Exception as e:
            logger.error(f"❌ Error borrando: {e}")
        
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
            logger.info(f"✅ Notificación enviada")
            
            # Borrar notificación después de 30 segundos
            async def delete_notification():
                await asyncio.sleep(30)
                try:
                    await context.bot.delete_message(TARGET_GROUP_ID, notification.message_id)
                    logger.info(f"✅ Notificación borrada")
                except Exception as e:
                    logger.debug(f"Error borrando notificación: {e}")
            
            asyncio.create_task(delete_notification())
        
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error en handle_message: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start."""
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
        
        # Borrar después de 60 segundos
        async def delete_message():
            await asyncio.sleep(60)
            try:
                await context.bot.delete_message(update.message.from_user.id, message.message_id)
                logger.info(f"✅ Mensaje /start borrado")
            except Exception as e:
                logger.debug(f"Error borrando /start: {e}")
        
        asyncio.create_task(delete_message())
    
    except Exception as e:
        logger.error(f"❌ Error en /start: {e}")

async def main():
    """Función principal - WEBHOOK para Railway."""
    logger.info("=" * 80)
    logger.info("🤖 INICIANDO BOT DE TELEGRAM - VERIFICADOR DE USERNAME")
    logger.info(f"   Token: {BOT_TOKEN[:30]}...")
    logger.info(f"   Grupo: {TARGET_GROUP_ID}")
    logger.info(f"   Webhook URL: {WEBHOOK_URL}")
    logger.info(f"   Puerto: {PORT}")
    logger.info("=" * 80)
    
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
    
    # Configurar WEBHOOK para Railway
    logger.info("📡 Configurando WEBHOOK...")
    
    if WEBHOOK_URL:
        # Usar WEBHOOK (recomendado para Railway)
        try:
            await app.bot.set_webhook(url=WEBHOOK_URL + BOT_TOKEN)
            logger.info(f"✅ Webhook configurado: {WEBHOOK_URL + BOT_TOKEN}")
            
            # Iniciar servidor web para recibir webhooks
            await app.updater.start_webhook(
                listen="0.0.0.0",
                port=PORT,
                url_path=BOT_TOKEN,
                webhook_url=WEBHOOK_URL + BOT_TOKEN
            )
            logger.info(f"✅ Servidor webhook escuchando en puerto {PORT}")
            logger.info("✅ Bot LISTO para recibir mensajes vía WEBHOOK")
            
            # Mantener corriendo
            await asyncio.Event().wait()
        
        except Exception as e:
            logger.error(f"❌ Error configurando webhook: {e}")
            logger.info("📡 Fallback a POLLING...")
            
            # Fallback a polling si webhook falla
            await app.updater.start_polling(
                allowed_updates=["message", "edited_message"],
                drop_pending_updates=False
            )
            logger.info("✅ Polling activo (modo fallback)")
            await asyncio.Event().wait()
    else:
        # Usar POLLING si no hay WEBHOOK_URL
        logger.info("⚠️ WEBHOOK_URL no configurada, usando POLLING...")
        await app.updater.start_polling(
            allowed_updates=["message", "edited_message"],
            drop_pending_updates=False
        )
        logger.info("✅ Polling activo - Bot LISTO para recibir mensajes")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Bot detenido")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
