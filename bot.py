#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE MODERACIÓN PROFESIONAL - SISTEMA DINÁMICO
Basado en Rose Bot - Código copiado de repositorio profesional
- Verificación de username
- Blacklist dinámico (TÚ agregas las palabras)
- Detección de enlaces y desvíos
- Sistema de warns (3 = ban automático)
- Respuesta INSTANTÁNEA
- NUNCA se duerme - Keepalive cada 30 segundos
"""
import os
import time
import logging
import threading
import re
import html
import unicodedata
from collections import defaultdict
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
load_dotenv()

DEFAULT_BOT_TOKEN = '8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips'
DEFAULT_GROUP_ID = -1003534894759
OWNER_ID = 0  # CAMBIAR POR TU ID

BOT_TOKEN = os.getenv('BOT_TOKEN', DEFAULT_BOT_TOKEN)
TARGET_GROUP_ID_STR = os.getenv('TARGET_GROUP_ID', str(DEFAULT_GROUP_ID))
OWNER_ID = int(os.getenv('OWNER_ID', OWNER_ID))

try:
    TARGET_GROUP_ID = int(TARGET_GROUP_ID_STR)
except (ValueError, TypeError):
    TARGET_GROUP_ID = DEFAULT_GROUP_ID

LOG_FILE = "moderation_bot.log"

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

logger.info(f"✅ BOT_TOKEN: {BOT_TOKEN[:20]}...")
logger.info(f"✅ TARGET_GROUP_ID: {TARGET_GROUP_ID}")
logger.info(f"✅ OWNER_ID: {OWNER_ID}")

# ============================================================================
# INICIALIZAR BOT
# ============================================================================
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================================
# BLACKLIST DINÁMICO - ALMACENAMIENTO EN MEMORIA
# ============================================================================
CHAT_BLACKLISTS = defaultdict(set)  # {chat_id: {palabra1, palabra2, ...}}

# Patrones para detectar URLs y desvíos
URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)
SHORTENED_URL_PATTERN = re.compile(
    r'(bit\.ly|tinyurl|short\.link|ow\.ly|goo\.gl|is\.gd|buff\.ly|adf\.ly|t\.co|youtu\.be)'
)

# Cache de admins
admin_cache = {}
admin_cache_time = 0

# Sistema de warns: {user_id: {chat_id: warn_count}}
user_warns = defaultdict(lambda: defaultdict(int))

# ============================================================================
# FUNCIONES AUXILIARES
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
    
    return admin_cache


def normalize_text(text):
    """Normalizar texto para búsqueda."""
    if not text:
        return ""
    
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def contains_banned_word(text, chat_id):
    """Verificar si el texto contiene palabras prohibidas."""
    if not text or chat_id not in CHAT_BLACKLISTS:
        return False, None
    
    normalized = normalize_text(text)
    
    for word in CHAT_BLACKLISTS[chat_id]:
        if re.search(r'\b' + re.escape(word.lower()) + r'\b', normalized):
            return True, word
    
    return False, None


def contains_url(text):
    """Detectar URLs y desvíos."""
    if not text:
        return False, None
    
    # Buscar URLs directas
    if URL_PATTERN.search(text):
        return True, "URL directa"
    
    # Buscar desvíos (URLs acortadas)
    if SHORTENED_URL_PATTERN.search(text):
        return True, "URL acortada/desvío"
    
    return False, None


def delete_message_delayed(chat_id, message_id, delay=30):
    """Borrar mensaje después de X segundos."""
    def _delete():
        try:
            time.sleep(delay)
            bot.delete_message(chat_id, message_id)
            logger.info(f"✅ Mensaje {message_id} borrado")
        except Exception as e:
            logger.debug(f"Error borrando mensaje: {e}")
    
    thread = threading.Thread(target=_delete, daemon=True)
    thread.start()


def send_warning(user_id, first_name, reason, warn_count, chat_id):
    """Enviar advertencia al usuario."""
    try:
        warning_text = (
            f"<b>⚠️ ADVERTENCIA - {first_name}</b>\n\n"
            f"<b>Razón:</b> {reason}\n"
            f"<b>Advertencias:</b> {warn_count}/3\n\n"
        )
        
        if warn_count >= 3:
            warning_text += "<b>❌ HAS SIDO BANEADO DEL GRUPO</b>"
        else:
            warning_text += f"<b>⚠️ {3 - warn_count} advertencia(s) más y serás baneado</b>"
        
        notification = bot.send_message(chat_id, warning_text, parse_mode='HTML')
        logger.info(f"✅ Advertencia enviada a {user_id}: {reason}")
        
        delete_message_delayed(chat_id, notification.message_id, delay=30)
    
    except Exception as e:
        logger.error(f"❌ Error enviando advertencia: {e}")


# ============================================================================
# COMANDOS PRIVADOS (SOLO PARA EL OWNER)
# ============================================================================

@bot.message_handler(commands=['start', 'help'], func=lambda m: m.chat.type == 'private')
def handle_start_private(message):
    """Comando /start en privado - Solo para el owner."""
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.from_user.id, "❌ No tienes permiso para usar este bot.")
        return
    
    help_text = (
        "<b>🤖 BOT DE MODERACIÓN PROFESIONAL</b>\n\n"
        "<b>COMANDOS PARA AGREGAR PALABRAS PROHIBIDAS:</b>\n\n"
        "<code>/addblacklist palabra1 palabra2 palabra3</code>\n"
        "Agrega palabras a la lista de prohibidas\n\n"
        "<code>/unblacklist palabra1 palabra2</code>\n"
        "Quita palabras de la lista\n\n"
        "<code>/blacklist</code>\n"
        "Ver todas las palabras prohibidas\n\n"
        "<b>FUNCIONES AUTOMÁTICAS:</b>\n"
        "✅ Verifica username - Borra mensajes sin alias\n"
        "✅ Detecta palabras prohibidas - Las que TÚ agregues\n"
        "✅ Detecta URLs y desvíos - Bloquea enlaces\n"
        "✅ Sistema de warns - 3 advertencias = ban\n"
        "✅ Admin exempt - Los admins pueden escribir lo que quieran\n"
        "✅ NUNCA se duerme - Keepalive cada 30 segundos\n\n"
        "<b>EJEMPLO:</b>\n"
        "<code>/addblacklist spam scam estafa</code>\n"
        "Esto agregará 'spam', 'scam' y 'estafa' a la lista"
    )
    
    bot.send_message(message.from_user.id, help_text, parse_mode='HTML')


@bot.message_handler(commands=['addblacklist'], func=lambda m: m.chat.type == 'private')
def add_blacklist_private(message):
    """Agregar palabras a la blacklist."""
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.from_user.id, "❌ No tienes permiso.")
        return
    
    words = message.text.split(None, 1)
    if len(words) < 2:
        bot.send_message(message.from_user.id, "❌ Uso: /addblacklist palabra1 palabra2 palabra3")
        return
    
    text = words[1]
    to_blacklist = list(set(word.strip().lower() for word in text.split() if word.strip()))
    
    for word in to_blacklist:
        CHAT_BLACKLISTS[TARGET_GROUP_ID].add(word)
    
    response = f"✅ Se agregaron {len(to_blacklist)} palabra(s) a la blacklist:\n\n"
    for word in to_blacklist:
        response += f"• {word}\n"
    
    bot.send_message(message.from_user.id, response)
    logger.info(f"✅ Palabras agregadas: {to_blacklist}")


@bot.message_handler(commands=['unblacklist'], func=lambda m: m.chat.type == 'private')
def unblacklist_private(message):
    """Quitar palabras de la blacklist."""
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.from_user.id, "❌ No tienes permiso.")
        return
    
    words = message.text.split(None, 1)
    if len(words) < 2:
        bot.send_message(message.from_user.id, "❌ Uso: /unblacklist palabra1 palabra2")
        return
    
    text = words[1]
    to_unblacklist = list(set(word.strip().lower() for word in text.split() if word.strip()))
    
    successful = 0
    for word in to_unblacklist:
        if word in CHAT_BLACKLISTS[TARGET_GROUP_ID]:
            CHAT_BLACKLISTS[TARGET_GROUP_ID].remove(word)
            successful += 1
    
    response = f"✅ Se removieron {successful} palabra(s) de la blacklist"
    bot.send_message(message.from_user.id, response)
    logger.info(f"✅ Palabras removidas: {successful}")


@bot.message_handler(commands=['blacklist'], func=lambda m: m.chat.type == 'private')
def blacklist_private(message):
    """Ver todas las palabras prohibidas."""
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.from_user.id, "❌ No tienes permiso.")
        return
    
    if TARGET_GROUP_ID not in CHAT_BLACKLISTS or not CHAT_BLACKLISTS[TARGET_GROUP_ID]:
        bot.send_message(message.from_user.id, "📋 No hay palabras prohibidas aún.\n\nUsa /addblacklist para agregar")
        return
    
    response = f"📋 <b>Palabras prohibidas ({len(CHAT_BLACKLISTS[TARGET_GROUP_ID])}):</b>\n\n"
    for word in sorted(CHAT_BLACKLISTS[TARGET_GROUP_ID]):
        response += f"• {word}\n"
    
    # Dividir si es muy largo
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            bot.send_message(message.from_user.id, part, parse_mode='HTML')
    else:
        bot.send_message(message.from_user.id, response, parse_mode='HTML')


# ============================================================================
# MANEJADORES DE MENSAJES EN EL GRUPO
# ============================================================================

@bot.message_handler(commands=['start', 'help'], func=lambda m: m.chat.type == 'group' or m.chat.type == 'supergroup')
def handle_start_group(message):
    """Comando /start en el grupo."""
    response = (
        "<b>📋 CÓMO CREAR TU NOMBRE DE USUARIO</b>\n\n"
        "1️⃣ Abre Telegram → Toca tu foto de perfil\n"
        "2️⃣ Toca 'Editar perfil'\n"
        "3️⃣ Busca 'Nombre de usuario'\n"
        "4️⃣ Escribe tu nombre único\n"
        "5️⃣ Toca el icono de verificación (✓)\n\n"
        "<b>✅ ¡Listo! Ahora puedes escribir en el grupo.</b>"
    )
    
    bot.send_message(message.chat.id, response, parse_mode='HTML')


@bot.message_handler(content_types=['text'], func=lambda m: m.chat.type == 'group' or m.chat.type == 'supergroup')
def handle_message_group(message):
    """Procesar mensajes del grupo - FUNCIÓN PRINCIPAL."""
    try:
        if message.chat.id != TARGET_GROUP_ID:
            return
        
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        message_text = (message.text[:50] if message.text else "[sin texto]")
        
        logger.info(f"📨 MENSAJE: {user_id} (@{username}): {message_text}")
        
        # Obtener admins
        admins = get_admins()
        
        # Si es admin, permitir TODO
        if user_id in admins:
            logger.info(f"✅ Admin {user_id} permitido")
            return
        
        # ============================================================================
        # VERIFICACIÓN 1: USUARIO SIN USERNAME
        # ============================================================================
        if not username:
            logger.warning(f"🚫 SIN USERNAME: {user_id}")
            
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje borrado (sin username)")
            except Exception as e:
                logger.error(f"❌ Error borrando: {e}")
            
            send_warning(user_id, first_name, "No tienes nombre de usuario", 1, TARGET_GROUP_ID)
            return
        
        # ============================================================================
        # VERIFICACIÓN 2: URLs Y DESVÍOS
        # ============================================================================
        has_url, url_type = contains_url(message.text)
        
        if has_url:
            logger.warning(f"🚫 URL DETECTADA: {user_id} - {url_type}")
            
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje borrado (URL)")
            except Exception as e:
                logger.error(f"❌ Error borrando: {e}")
            
            user_warns[user_id][TARGET_GROUP_ID] += 1
            warn_count = user_warns[user_id][TARGET_GROUP_ID]
            
            send_warning(user_id, first_name, f"Detectado: {url_type}", warn_count, TARGET_GROUP_ID)
            
            if warn_count >= 3:
                try:
                    bot.ban_chat_member(TARGET_GROUP_ID, user_id)
                    logger.warning(f"🚫 BANEADO: {user_id}")
                    
                    ban_msg = bot.send_message(
                        TARGET_GROUP_ID,
                        f"<b>🚫 {first_name} ha sido baneado</b>\n<i>Razón: Violaciones repetidas</i>",
                        parse_mode='HTML'
                    )
                    delete_message_delayed(TARGET_GROUP_ID, ban_msg.message_id, delay=30)
                except Exception as e:
                    logger.error(f"❌ Error baneando: {e}")
            
            return
        
        # ============================================================================
        # VERIFICACIÓN 3: PALABRAS PROHIBIDAS
        # ============================================================================
        has_banned, banned_word = contains_banned_word(message.text, TARGET_GROUP_ID)
        
        if has_banned:
            logger.warning(f"🚫 PALABRA PROHIBIDA: {user_id} - '{banned_word}'")
            
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje borrado (palabra prohibida)")
            except Exception as e:
                logger.error(f"❌ Error borrando: {e}")
            
            user_warns[user_id][TARGET_GROUP_ID] += 1
            warn_count = user_warns[user_id][TARGET_GROUP_ID]
            
            send_warning(user_id, first_name, f"Palabra prohibida: '{banned_word}'", warn_count, TARGET_GROUP_ID)
            
            if warn_count >= 3:
                try:
                    bot.ban_chat_member(TARGET_GROUP_ID, user_id)
                    logger.warning(f"🚫 BANEADO: {user_id}")
                    
                    ban_msg = bot.send_message(
                        TARGET_GROUP_ID,
                        f"<b>🚫 {first_name} ha sido baneado</b>\n<i>Razón: Violaciones repetidas</i>",
                        parse_mode='HTML'
                    )
                    delete_message_delayed(TARGET_GROUP_ID, ban_msg.message_id, delay=30)
                except Exception as e:
                    logger.error(f"❌ Error baneando: {e}")
            
            return
        
        # ✅ Mensaje permitido
        logger.info(f"✅ Mensaje permitido de @{username}")
    
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")


# ============================================================================
# KEEPALIVE
# ============================================================================

def keepalive_worker():
    """Mantener el bot activo."""
    logger.info("✅ Keepalive iniciado")
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
    logger.info("🤖 BOT DE MODERACIÓN PROFESIONAL - INICIANDO")
    logger.info(f"👥 Grupo: {TARGET_GROUP_ID}")
    logger.info(f"👤 Owner: {OWNER_ID}")
    logger.info("=" * 80)
    
    # Iniciar keepalive
    keepalive_thread = threading.Thread(target=keepalive_worker, daemon=True)
    keepalive_thread.start()
    
    logger.info("=" * 80)
    logger.info("✅ FUNCIONES ACTIVAS:")
    logger.info("✅ Verificación de username")
    logger.info("✅ Detección de URLs y desvíos")
    logger.info("✅ Blacklist dinámico (TÚ agregas palabras)")
    logger.info("✅ Sistema de warns (3 = ban)")
    logger.info("✅ Admin exempt")
    logger.info("✅ Keepalive cada 30 segundos")
    logger.info("=" * 80)
    
    try:
        logger.info("🚀 Iniciando POLLING...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        time.sleep(5)
