# Bot de Alias para Telegram

Bot que verifica que los usuarios tengan un nombre de usuario antes de permitirles enviar mensajes en el grupo.

## Características

✅ Verifica automáticamente que los usuarios tengan username
✅ Borra mensajes de usuarios sin username
✅ Envía instrucciones claras sobre cómo crear username
✅ Los admins pueden escribir sin username
✅ Notificaciones se eliminan automáticamente después de 30 segundos

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Edita `bot.py` y cambia:
- `BOT_TOKEN`: Tu token de bot de Telegram
- `TARGET_GROUP_ID`: El ID de tu grupo

## Ejecución Local

```bash
python3 bot.py
```

## Despliegue en Railway

1. Conecta tu repositorio de GitHub a Railway
2. Railway detectará automáticamente el Procfile
3. El bot se ejecutará automáticamente

## Logs

El bot genera logs detallados con:
- ✅ Mensajes procesados
- ❌ Errores
- 📨 Acciones tomadas

Revisa los logs en Railway para debugging.
