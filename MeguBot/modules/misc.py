from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot import dispatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import MessageEntity, ParseMode, Update
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext, Filters, CommandHandler

MARKDOWN_HELP = f"""
Markdown es una herramienta de formato muy poderosa compatible con Telegram. {dispatcher.bot.first_name} tiene algunas mejoras, para asegurarse de que
los mensajes guardados se analizen correctamente y le permitan crear botones.\n
• <code>_cursiva_</code><b>:</b> Ajustar el texto con '_' producirá texto en cursiva
• <code>*negrita*</code><b>:</b> Ajustar el texto con '*' producirá texto en negrita
• <code>`código`</code><b>:</b> Ajustar el texto con '`' producirá texto monoespaciado, también conocido como 'código'
• <code>[texto](URL)</code><b>:</b> Esto creará un enlace - el mensaje solo se verá el <code>texto</code>,
y al tocarlo se abrirá la página en <code>URL</code>.
<b>Ejemplo:</b> <code>[test](example.com)</code>
• <code>[buttontext](buttonurl:URL)</code><b>:</b> Esta es una mejora especial para permitir que los usuarios tengan botones con markdown. <code>buttontext</code> será lo que se muestra en el botón, y <code>URL</code>\
será la url que se abre.
<b>Ejemplo:</b> <code>[Este es un botón](buttonurl: example.com)</code>
Si desea varios botones en la misma línea, use :same, como tal:
<code>[uno](buttonurl://example.com)
[dos](buttonurl://google.com:same)</code>\n
Esto creará dos botones en una sola línea, en lugar de un botón por línea.
Tenga en cuenta que su mensaje <b>DEBE</b> contener algún texto que no sea solo un botón.!
"""


@run_async
@user_admin
def say(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True)
    else:
        message.reply_text(
            args[1],
            quote=False,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True)
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Intenta enviar el siguiente mensaje a mí, y verás, usa #test!"
    )
    update.effective_message.reply_text(
        "/save test Esta es una prueba de markdown. _cursiva_, *negrita*, `código`, "
        "[URL](ejemplo.com) [Botón](buttonurl:github.com) "
        "[Botón2](buttonurl://google.com:same)")


@run_async
def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            'Contactame en privado',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Ayuda de Markdown",
                    url=f"t.me/{context.bot.username}?start=markdownhelp")
            ]]))
        return
    markdown_help_sender(update)


__help__ = """
*Comandos disponibles:*

*Markdown:*
 •`/markdownhelp`*:* resumen rápido de cómo funciona Markdown en Telegram - solo se puede llamar en chats privados
*Pegar:*
 •`/paste`*:* Guarda el contenido respondido en` nekobin.com` y responde con una URL
*Reaccionar:*
 •`/react`*:* Reacciona con una reacción aleatoria
*Urban Dictonary(ENG):*
 •`/ud <palabra>` *:* Escriba la palabra o expresión que desea utilizar para la búsqueda
* Wikipedia: *
 •`/wiki <query>`*:* Busca en Wikipedia
*Convertidor de moneda:*
 •`/cash`*:* Convertidor de moneda
*Ejemplo:*
  `/cash 1 USD INR`
        O
  `/cash 1 usd inr`
*Salida:* `1.0 USD = 75.505 INR`
"""

SAY_HANDLER = DisableAbleCommandHandler("say", say, filters=Filters.group)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)

dispatcher.add_handler(SAY_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["say"]
__handlers__ = [
    SAY_HANDLER,
    MD_HELP_HANDLER,
]
