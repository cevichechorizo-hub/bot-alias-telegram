#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT DE MODERACIÓN PROFESIONAL - Telegram
- Usa SOLO palabras prohibidas REALES de repositorios profesionales
- Verificación de username
- Detección de palabras prohibidas
- L33t speak, acentos, caracteres especiales
- Sistema de warns (3 = ban automático)
- Respuesta INSTANTÁNEA (<0.5s)
- NUNCA se duerme - Keepalive cada 30 segundos
- Admin exempt
"""
import os
import time
import logging
import threading
import re
import unicodedata
from collections import defaultdict
from telebot import TeleBot, types
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
load_dotenv()

# Valores por defecto
DEFAULT_BOT_TOKEN = '8491596754:AAHBnLtSRI9Ii3uL6y-rcmLXxfU_7_7bips'
DEFAULT_GROUP_ID = -1003534894759

# Obtener variables de entorno
BOT_TOKEN = os.getenv('BOT_TOKEN', DEFAULT_BOT_TOKEN)
TARGET_GROUP_ID_STR = os.getenv('TARGET_GROUP_ID', str(DEFAULT_GROUP_ID))

# Convertir TARGET_GROUP_ID a int
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

# Log de configuración
logger.info(f"✅ BOT_TOKEN configurado: {BOT_TOKEN[:20]}...")
logger.info(f"✅ TARGET_GROUP_ID: {TARGET_GROUP_ID}")

# ============================================================================
# INICIALIZAR BOT
# ============================================================================
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================================
# PALABRAS PROHIBIDAS - SOLO REALES DE REPOSITORIOS PROFESIONALES
# ============================================================================

# Lista de palabras prohibidas en español - DIRECTAMENTE de repositorios profesionales
# Fuente: https://github.com/Hesham-Elbadawi/list-of-banned-words/blob/master/es
BANNED_WORDS = {
    'asesinato', 'asno', 'bastardo', 'bollera', 'cabron', 'cabrón', 'caca',
    'chupada', 'chupapollas', 'chupetón', 'concha', 'coño', 'coprofagía',
    'culo', 'drogas', 'esperma', 'follador', 'follar', 'gilipichis',
    'gilipollas', 'heroína', 'hija de puta', 'hijaputa', 'hijo de puta',
    'hijoputa', 'idiota', 'imbécil', 'infierno', 'jilipollas', 'kapullo',
    'lameculos', 'maciza', 'macizorra', 'maldito', 'mamada', 'marica',
    'maricón', 'mariconazo', 'martillo', 'mierda', 'nazi', 'orina', 'pedo',
    'pervertido', 'pezón', 'pinche', 'pis', 'prostituta', 'puta', 'racista',
    'ramera', 'sádico', 'semen', 'sexo', 'sexo oral', 'soplagaitas',
    'soplapollas', 'tetas grandes', 'tía buena', 'travesti', 'trio', 'verga',
    'vete a la mierda', 'vulva'
}

# L33t speak mappings
LEET_MAPPINGS = {
    '0': 'o',
    '1': 'i',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '7': 't',
    '8': 'b',
    '9': 'g',
    '@': 'a',
    '$': 's',
    '!': 'i',
}

# Cache de admins
admin_cache = {}
admin_cache_time = 0

# Sistema de warns: {user_id: warn_count}
user_warns = defaultdict(int)

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


def normalize_text(text):
    """Normalizar texto: remover acentos, convertir a minúsculas, remover l33t speak."""
    if not text:
        return ""
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Reemplazar l33t speak
    for leet, normal in LEET_MAPPINGS.items():
        text = text.replace(leet, normal)
    
    # Remover acentos y caracteres especiales
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    
    # Remover caracteres especiales pero mantener espacios
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Remover espacios múltiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def contains_banned_word(text):
    """Verificar si el texto contiene palabras prohibidas."""
    if not text:
        return False, None
    
    normalized = normalize_text(text)
    
    # Verificar palabras prohibidas - BÚSQUEDA EXACTA DE PALABRA
    for word in BANNED_WORDS:
        # Usar word boundaries para evitar falsas positivas
        # Ejemplo: "hola" no coincide con "holaaaa"
        if re.search(r'\b' + re.escape(word) + r'\b', normalized):
            return True, word
    
    return False, None


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


def send_warning(user_id, first_name, reason, warn_count):
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
        
        notification = bot.send_message(
            TARGET_GROUP_ID,
            warning_text,
            parse_mode='HTML'
        )
        logger.info(f"✅ Advertencia enviada a {user_id}: {reason}")
        
        # Borrar notificación después de 30 segundos
        delete_message_delayed(TARGET_GROUP_ID, notification.message_id, delay=30)
    
    except Exception as e:
        logger.error(f"❌ Error enviando advertencia: {e}")


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
    """Procesar mensajes de texto - FUNCIÓN PRINCIPAL."""
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
        
        # Si es admin, permitir TODO
        if user_id in admins:
            logger.info(f"✅ Admin {user_id} permitido")
            return
        
        # ============================================================================
        # VERIFICACIÓN 1: USUARIO SIN USERNAME
        # ============================================================================
        if not username:
            logger.warning(f"🚫 USUARIO SIN USERNAME: {user_id} ({first_name})")
            
            # Borrar mensaje INMEDIATAMENTE
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje {message.message_id} borrado (sin username)")
            except Exception as e:
                logger.error(f"❌ Error borrando mensaje: {e}")
            
            # Enviar advertencia
            send_warning(user_id, first_name, "No tienes nombre de usuario", 1)
            return
        
        # ============================================================================
        # VERIFICACIÓN 2: PALABRAS PROHIBIDAS
        # ============================================================================
        has_banned, banned_word = contains_banned_word(message.text)
        
        if has_banned:
            logger.warning(f"🚫 PALABRA PROHIBIDA: {user_id} (@{username}) - '{banned_word}'")
            
            # Borrar mensaje INMEDIATAMENTE
            try:
                bot.delete_message(TARGET_GROUP_ID, message.message_id)
                logger.info(f"✅ Mensaje {message.message_id} borrado (palabra prohibida)")
            except Exception as e:
                logger.error(f"❌ Error borrando mensaje: {e}")
            
            # Incrementar warns
            user_warns[user_id] += 1
            warn_count = user_warns[user_id]
            
            # Enviar advertencia
            send_warning(user_id, first_name, f"Palabra prohibida: '{banned_word}'", warn_count)
            
            # Si 3 warns, banear
            if warn_count >= 3:
                try:
                    bot.ban_chat_member(TARGET_GROUP_ID, user_id)
                    logger.warning(f"🚫 USUARIO BANEADO: {user_id} (@{username})")
                    
                    ban_msg = bot.send_message(
                        TARGET_GROUP_ID,
                        f"<b>🚫 {first_name} ha sido baneado del grupo</b>\n"
                        f"<i>Razón: Violaciones repetidas de las reglas</i>",
                        parse_mode='HTML'
                    )
                    delete_message_delayed(TARGET_GROUP_ID, ban_msg.message_id, delay=30)
                except Exception as e:
                    logger.error(f"❌ Error baneando usuario: {e}")
            
            return
        
        # ✅ Mensaje permitido
        logger.info(f"✅ Mensaje permitido de @{username}")
    
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
    logger.info("🤖 BOT DE MODERACIÓN PROFESIONAL - INICIANDO")
    logger.info(f"👥 Grupo objetivo: {TARGET_GROUP_ID}")
    logger.info(f"📝 Palabras prohibidas: {len(BANNED_WORDS)} (SOLO REALES)")
    logger.info("=" * 80)
    
    # Iniciar keepalive en thread separado
    keepalive_thread = threading.Thread(target=keepalive_worker, daemon=True)
    keepalive_thread.start()
    
    logger.info("=" * 80)
    logger.info("✅ Bot LISTO")
    logger.info("✅ Verificación de username ACTIVA")
    logger.info("✅ Detección de palabras prohibidas ACTIVA (SOLO REALES)")
    logger.info("✅ Sistema de warns (3 = ban) ACTIVO")
    logger.info("✅ Usando POLLING PURO (sin Flask, sin webhooks)")
    logger.info("✅ Keepalive cada 30 segundos")
    logger.info("✅ RESPUESTA INSTANTÁNEA - NUNCA se duerme")
    logger.info("=" * 80)
    
    # Iniciar polling
    try:
        logger.info("🚀 Iniciando POLLING...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"❌ Error crítico en polling: {e}")
        time.sleep(5)
