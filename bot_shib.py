import requests
from telegram import Update
from telegram.ext import Application, CommandHandler
import time

# Datos para el gráfico
HISTORIAL_PRECIOS = []
MAX_PUNTOS = 10  # Máximo de puntos en el gráfico

async def precio_shib(update: Update, context):
    global HISTORIAL_PRECIOS
    
    try:
        # Obtener precio SHIB/USD y USD/MXN
        shib_usd = requests.get("https://api.bitso.com/v3/ticker/?book=shib_usd").json()
        usd_mxn = requests.get("https://api.bitso.com/v3/ticker/?book=usd_mxn").json()
        
        precio_shib_usd = float(shib_usd["payload"]["last"])
        precio_usd_mxn = float(usd_mxn["payload"]["last"])
        precio_shib_mxn = precio_shib_usd * precio_usd_mxn
        cambio_24h = float(shib_usd["payload"]["change_24"])
        
        # Actualizar historial
        HISTORIAL_PRECIOS.append(precio_shib_mxn)
        if len(HISTORIAL_PRECIOS) > MAX_PUNTOS:
            HISTORIAL_PRECIOS.pop(0)
        
        # Crear gráfico con emojis (versión sensible)
        emoji_tendencia = "📈" if cambio_24h >= 0 else "📉"
        if len(HISTORIAL_PRECIOS) > 1:
            rango = max(HISTORIAL_PRECIOS) - min(HISTORIAL_PRECIOS)
            escala = 0.000001  # Ajusta este valor según tus necesidades
        else:
            rango = 1
            escala = 1

        grafico = ""
        for precio in HISTORIAL_PRECIOS:
            if len(HISTORIAL_PRECIOS) > 1:
                diferencia = precio - min(HISTORIAL_PRECIOS)
                posicion = min(int(diferencia / escala), 5)
            else:
                posicion = 3  # Neutral si solo hay un dato
            
            emoji_grafico = "🟢" * posicion + "⚪" * (3 - posicion) + "🔴" * (5 - posicion)
            grafico += f"{emoji_grafico} ${precio:,.8f}\n"

        await update.message.reply_text(
            f"{emoji_tendencia} **SHIB = ${precio_shib_mxn:,.8f} MXN**\n"
            f"🔄 Cambio 24h: {cambio_24h:+.2f}%\n\n"
            f"📊 **Últimos {len(HISTORIAL_PRECIOS)} precios:**\n"
            f"{grafico}\n"
            f"💡 *Escala: ~{escala:,.8f} MXN por emoji*"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al obtener datos: {str(e)}")

# Configuración del bot
application = Application.builder().token("7576781420:AAGyHRgs1qnDAWQJxSE_j0YqYFBd-ehCVkw").build()
application.add_handler(CommandHandler("precio_shib", precio_shib))
application.run_polling()