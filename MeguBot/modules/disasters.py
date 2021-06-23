import html
import json
import os
from typing import Optional

from MeguBot import (DEV_USERS, OWNER_ID, SUDO_USERS, SUPPORT_CHAT,
                          SUPPORT_USERS, FROG_USERS, WHITELIST_USERS,
                          dispatcher)
from MeguBot.modules.helper_funcs.chat_status import (dev_plus, sudo_plus,
                                                           whitelist_plus)
from MeguBot.modules.helper_funcs.extraction import extract_user
from MeguBot.modules.log_channel import gloggable
from telegram import ParseMode, TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

ELEVATED_USERS_FILE = os.path.join(os.getcwd(),
                                   'MeguBot/elevated_users.json')


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "Esto...es un grupo! baka ka omae?"

    elif user_id == bot.id:
        reply = "Eso no funciona de esa manera."

    else:
        reply = None
    return reply


#I added extra new lines
disasters = f"""Megu tiene niveles de acceso de bot:
\n*Demonios Carmesí:* Desarrolladores que pueden acceder al servidor del bot y pueden ejecutar, editar y modificar el código del bot. También puede gestionar otros problemas.
\n*CrimsonDemon:* Solo existe uno, el propietario del bot.
El propietario tiene acceso completo al bot, incluida la administración del bot en los chats en los que Megu está.
\n*Destroyers:* Tienen acceso de superusuario, pueden banear globalmente, administrar desastres menores que ellos y son administradores en Megu.
\n*Demonios:* Tienen acceso al baneo global de usuarios en Megu.
\n*Ranas Gigantes:* Igual que los Sapos Gigantes, pero pueden deshacerse si están baneados.
\n*Sapos Gigantes:* No se puede banear, si hace flood se silencia o kickea, pero los administradores pueden banearlo manualmente.
\n*Descargo de responsabilidad*: Los *Demonios*(Soporte) de Megu sirven para solucionar problemas, brindar asistencia y prohibir a los posibles estafadores.
Informar sobre abusos o preguntarnos más sobre estos en @{SUPPORT_CHAT}.
"""


# do not async, not a handler
def send_disasters(update):
    update.effective_message.reply_text(
        disasters, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@run_async
@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        message.reply_text("Este miembro ya es un Destroyer")
        return ""

    if user_id in SUPPORT_USERS:
        rt += "Promoví un Demonio a Destroyer."
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Promoví un Sapo Gigante a Destroyer."
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data['sudos'].append(user_id)
    SUDO_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\nSe estableció correctamente el nivel de {} en Destroyer!".format(
            user_member.first_name))

    log_message = (
        f"#SuperUsuario\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addsupport(
    update: Update,
    context: CallbackContext,
) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Rebajé al Destroyer a Demonio"
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        message.reply_text("Este usuario ya es un Demonio.")
        return ""

    if user_id in WHITELIST_USERS:
        rt += "Promoví un Sapo Gigante a demonio"
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data['supports'].append(user_id)
    SUPPORT_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\n{user_member.first_name} fue agregado como un demonio!")

    log_message = (
        f"#Soporte\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Este miembro ya no es un Destroyer, rebajado a Sapo Gigante."
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        rt += "Este usuario ya no es un demonío, rebajado a Sapo Gigante."
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        message.reply_text("Este usuario ya es un Sapo Gigante.")
        return ""

    data['whitelists'].append(user_id)
    WHITELIST_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\n{user_member.first_name} ascendió con éxito a Sapo Gigante!")

    log_message = (
        f"#ListaBlanca\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addfrog(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Este miembro ya no es un Destroyer, rebajado a Rana Gigante."
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        rt += "Este usuario ya no es un demonio, rebajado a Rana Gigante."
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Este usuario ya no es un Sapo Gigante, rebajado a Rana Gigante."
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    if user_id in FROG_USERS:
        message.reply_text("Este usuario ya es una Rana Gigante.")
        return ""

    data['frogs'].append(user_id)
    FROG_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\n{user_member.first_name} ascendió con éxito a Rana Gigante!"
    )

    log_message = (
        f"#Rana\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}")

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        message.reply_text("Rebajé a este usuario a Humano")
        SUDO_USERS.remove(user_id)
        data['sudos'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#QuitaSuperusuario\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}"
        )

        if chat.type != 'private':
            log_message = "<b>{}:</b>\n".format(html.escape(
                chat.title)) + log_message

        return log_message

    else:
        message.reply_text("Este usuario no es un Destroyer!")
        return ""


@run_async
@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in SUPPORT_USERS:
        message.reply_text("Rebajé a este usuario a Humano")
        SUPPORT_USERS.remove(user_id)
        data['supports'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#QuitaSoporte\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("Este usuario no es un demonio!")
        return ""


@run_async
@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in WHITELIST_USERS:
        message.reply_text("Rebajado a usuario normal")
        WHITELIST_USERS.remove(user_id)
        data['whitelists'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#QuitaListaBlanca\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("Este usuario no es un Sapo Gigante!")
        return ""


@run_async
@sudo_plus
@gloggable
def removefrog(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in FROG_USERS:
        message.reply_text("Rebajado a usuario normal")
        FROG_USERS.remove(user_id)
        data['frogs'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#QuitaRana\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Usuario:</b> {mention_html(user_member.id, user_member.first_name)}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("Este usuario no es una Rana Gigante!")
        return ""


@run_async
@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    reply = "<b>Sapos Gigantes :</b>\n"
    bot = context.bot
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def froglist(update: Update, context: CallbackContext):
    reply = "<b>Ranas Gigantes 🐸:</b>\n"
    bot = context.bot
    for each_user in FROG_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Demonios 👺:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    true_sudo = list(set(SUDO_USERS) - set(DEV_USERS))
    reply = "<b>Destroyers  🕷:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "<b>Demonios Carmesí 💥:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = f"""
*⚠️ Aviso:*
Los comandos que se enumeran aquí solo funcionan para usuarios con acceso especial y se utilizan principalmente para solucionar problemas y depurar.
Los propietarios/administradores de grupo no necesitan estos comandos.

•`/cardemons`*:* Lista de todos los Demonios Carmesí(desarrolladores).
•`/destroyers`*:* Lista de todos los Destroyers(Superusuarios).
•`/demons`*:* Lista de todos los demonios(Soporte).
•`/frogs`*:* Lista de todos las Ranas Gigantes(ListaBlanca V1)
•`/gianttoads `*:* Lista de todos los Sapos Gigantes(Listablanca V2).

*Ping:*
 •`/ping`*:* Obtiene el tiempo de ping del bot al servidor de telegram.
 •`/pingall`*:* Obtiene todos los tiempos de ping listados
*Transmisión: (solo propietario del bot)*

*Nota:* Esto admite markdown básico.

 •`/broadcastall <mensajeaquí>`*:* Transmite el mensaje a todas partes.
 •`/broadcastusers <mensajeaquí>`*:* Transmite el mensaje también a todos los usuarios del bot.
 •`/broadcastgroups <mensajeaquí>`*:* Transmite el mensaje también a todos los grupos del bot.
*Obtener Chats:*
 •`/getchats ID`*:* Obtiene una lista de nombres de grupos en los que se ha visto al usuario. Solo propietario del bot.
*Lista negra:*
 •`/ignore`*:* Lista negra de un usuario para que no utilice el bot por completo.
 •`/notice`*:* Incluye al usuario en la lista blanca para permitir el uso del bot.

*Nota:* Estos comandos enumeran a los usuarios con privilegios especiales del bot y solo pueden ser utilizados por ellos.
 Puede visitar @{SUPPORT_CHAT} para consultar más sobre estos.
"""

SUDO_HANDLER = CommandHandler(("addsudo", "adddestroyer"), addsudo)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport)
FROG_HANDLER = CommandHandler(("addfrog"), addfrog)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addgianttoad"), addwhitelist)
UNSUDO_HANDLER = CommandHandler(("removesudo", "removedestroyer"), removesudo)
UNSUPPORT_HANDLER = CommandHandler(("removesupport", "removedemon"),
                                   removesupport)
UNFROG_HANDLER = CommandHandler(("removefrog"), removefrog)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist", "removegianttoad"),
                                     removewhitelist)

WHITELISTLIST_HANDLER = CommandHandler(["whitelistlist", "gianttoads"],
                                       whitelistlist)
FROGLIST_HANDLER = CommandHandler(["frogs"], froglist)
SUPPORTLIST_HANDLER = CommandHandler(["supportlist", "demons"], supportlist)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "destroyers"], sudolist)
DEVLIST_HANDLER = CommandHandler(["devlist", "cardemons"], devlist)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(FROG_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNFROG_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(FROGLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Aventureros"
__handlers__ = [
    SUDO_HANDLER, SUPPORT_HANDLER, FROG_HANDLER, WHITELIST_HANDLER,
    UNSUDO_HANDLER, UNSUPPORT_HANDLER, UNFROG_HANDLER, UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER, FROGLIST_HANDLER, SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER, DEVLIST_HANDLER
]
