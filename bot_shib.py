import os
from telegram import Update
from telegram.ext import Application, CommandHandler
import requests
import logging

# Configura logging para ver más detalles
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Cambiado a DEBUG para más información
)

# IMPORTANTE: Reemplaza esto con un nuevo token después de revocar el expuesto
TOKEN = "7474550148:AAEsCI_WzlsDYxPYAMdwrEASsvUDuNFINT0"  # Obtener de @BotFather

async def precio(update: Update, context):
    """Maneja el comando /precio para mostrar información de SHIB"""
    try:
        logging.info(f"Recibido comando /precio de {update.effective_user.id}")
        
        def get_data(url):
            """Obtiene datos de la API Bitso con manejo de errores"""
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Lanza excepción para códigos 4XX/5XX
                data = response.json()
                return data.get('payload') if data.get('success') else None
            except Exception as e:
                logging.error(f"Error en API call a {url}: {str(e)}")
                return None

        # Obtener datos de las APIs
        shib_data = get_data('https://api.bitso.com/v3/ticker/?book=shib_usd')
        usd_data = get_data('https://api.bitso.com/v3/ticker/?book=usd_mxn')

        if not shib_data or not usd_data:
            await update.message.reply_text("🔴 Datos no disponibles. Intenta más tarde")
            return

        # Cálculos y formato de respuesta
        precio_shib = float(shib_data['last']) * float(usd_data['last'])
        cambio = float(shib_data.get('change_24', 0))
        
        respuesta = (
            f"🐕 *SHIB/MXN*: ${precio_shib:,.8f}\n"
            f"📈 *24h*: {cambio:+.2f}%\n"
            f"💵 *100 MXN* = {100/precio_shib:,.0f} SHIB"
        )
        
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        logging.info("Respuesta enviada correctamente")

    except Exception as e:
        logging.error(f"Error en precio(): {str(e)}", exc_info=True)
        await update.message.reply_text("⚠️ Error temporal. Ya lo estoy solucionando")

async def start(update: Update, context):
    """Maneja el comando /start"""
    user = update.effective_user
    logging.info(f"Nuevo usuario: {user.id} - {user.first_name}")
    await update.message.reply_text("👋 ¡Bot SHIB activado! Usa /precio")

def main():
    """Configura y ejecuta el bot"""
    try:
        logging.info("Iniciando configuración del bot...")
        
        app = Application.builder() \
            .token(TOKEN) \
            .concurrent_updates(True) \
            .build()
        
        # Manejadores de comandos
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("precio", precio))
        
        # Modo desarrollo con polling
        logging.info("Iniciando bot en modo polling...")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logging.critical(f"Error fatal en main(): {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Configuración adicional para pruebas en VSCode
    try:
        # Verifica dependencias
        import telegram
        import requests
        logging.info("Todas las dependencias están instaladas")
        
        # Inicia el bot
        main()
    except ImportError as e:
        logging.error(f"Falta dependencia: {str(e)}")
        print(f"ERROR: Instala los paquetes faltantes con: pip install python-telegram-bot requests")
