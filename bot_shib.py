import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
import threading
import logging

# Configuración básica
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables globales
HISTORIAL_PRECIOS = []
MAX_PUNTOS = 10
TOKEN = os.getenv('TOKEN_BOT')

# Health Check para Render
def wake_up():
    try:
        requests.get(os.getenv('WEBHOOK_URL'), timeout=10)
    except Exception as e:
        logging.warning(f"Healtcheck failed: {e}")
    finally:
        threading.Timer(300, wake_up).start()

async def start(update: Update, context):
    await update.message.reply_text("👋 ¡Bot SHIB activado! Usa /precio_shib")

async def precio_shib(update: Update, context):
    global HISTORIAL_PRECIOS
    
    try:
        # Obtener datos de Bitso
        shib_usd = requests.get("https://api.bitso.com/v3/ticker/?book=shib_usd", timeout=10).json()
        usd_mxn = requests.get("https://api.bitso.com/v3/ticker/?book=usd_mxn", timeout=10).json()
        
        if not shib_usd.get('success') or not usd_mxn.get('success'):
            raise Exception("API Bitso no respondió correctamente")

        precio_shib_usd = float(shib_usd["payload"]["last"])
        precio_usd_mxn = float(usd_mxn["payload"]["last"])
        precio_shib_mxn = precio_shib_usd * precio_usd_mxn
        cambio_24h = float(shib_usd["payload"].get("change_24", 0))
        
        # Actualizar historial
        HISTORIAL_PRECIOS.append(precio_shib_mxn)
        if len(HISTORIAL_PRECIOS) > MAX_PUNTOS:
            HISTORIAL_PRECIOS.pop(0)
        
        # Crear gráfico
        emoji_tendencia = "📈" if cambio_24h >= 0 else "📉"
        min_precio = min(HISTORIAL_PRECIOS) if HISTORIAL_PRECIOS else 0
        escala = 0.000001  # Ajusta según necesidad

        grafico = ""
        for precio in HISTORIAL_PRECIOS:
            posicion = min(int((precio - min_precio) / escala), 5) if len(HISTORIAL_PRECIOS) > 1 else 3
            emoji_grafico = "🟢" * posicion + "⚪" * (3 - posicion) + "🔴" * (5 - posicion)
            grafico += f"{emoji_grafico} ${precio:,.8f}\n"

        respuesta = (
            f"{emoji_tendencia} **SHIB = ${precio_shib_mxn:,.8f} MXN**\n"
            f"🔄 Cambio 24h: {cambio_24h:+.2f}%\n\n"
            f"📊 **Últimos {len(HISTORIAL_PRECIOS)} precios:**\n"
            f"{grafico}\n"
            f"💡 *Escala: ~{escala:,.8f} MXN por emoji*"
        )
        
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Error en precio_shib: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ Error temporal al obtener datos. Intenta nuevamente.")

def main():
    # Iniciar health check si está en Render
    if os.getenv('RENDER'):
        wake_up()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("precio_shib", precio_shib))
    
    if os.getenv('RENDER'):
        app.run_webhook(
            listen="0.0.0.0",
            port=10000,
            webhook_url=os.getenv('WEBHOOK_URL'),
            secret_token=os.getenv('SECRET_TOKEN'),
            drop_pending_updates=True
        )
    else:
        # Modo desarrollo con logging más detallado
        logging.getLogger().setLevel(logging.DEBUG)
        app.run_polling()

if __name__ == "__main__":
    main()
