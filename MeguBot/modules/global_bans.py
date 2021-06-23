import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

import MeguBot.modules.sql.global_bans_sql as sql
from MeguBot.modules.sql.users_sql import get_user_com_chats
from MeguBot import (DEV_USERS, GBAN_LOGS, OWNER_ID, STRICT_GBAN,
                          SUDO_USERS, SUPPORT_CHAT, SPAMWATCH_SUPPORT_CHAT,
                          SUPPORT_USERS, FROG_USERS, WHITELIST_USERS, sw,
                          dispatcher)
from MeguBot.modules.helper_funcs.alternate import send_message
from MeguBot.modules.helper_funcs.chat_status import (is_user_admin,
                                                           support_plus,
                                                           user_admin)
from MeguBot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from MeguBot.modules.helper_funcs.misc import send_to_list
from MeguBot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "El usuario es administrador del grupo",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "Usuario no participante",
    "ID o alías no válido",
    "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Se requiere administrador en el chat",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Grupo/canal privado",
    "No está en el chat",
    "No se puede eliminar al propietario del chat",
}

UNGBAN_ERRORS = {
    "El usuario es administrador del grupo",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "Usuario no participante",
    "El método está disponible solo para supergrupos y chats de canal",
    "No está en el chat",
    "Grupo/canal privado",
    "Se requiere administrador en el grupo",
    "ID o alías no válido",
    "Usuario no encontrado",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "Este usuario es un Demonio Carmesí\nNo puedo actuar en contra de ellos."
        )
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text(
            "Espío, con mi ojito... un destroyer! Por qué se están volviendo el uno contra el otro?"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "¡Oooh, alguien está intentando superar a un Demonio! *agarra palomitas de maíz*")
        return

    if int(user_id) in FROG_USERS:
        message.reply_text("¡El es una rana! No puede ser baneado!")
        return

    if int(user_id) in WHITELIST_USERS:
        message.reply_text("¡El es un sapo! No puede ser baneado!")
        return

    if user_id == bot.id:
        message.reply_text("Tu uhh... quieres que me salga?")
        return
    if user_id in [777000, 1087968824]:
        message.reply_text(
            "Baka! No puedes hacer explotar la tecnología nativa de Telegram!"
        )
        return


    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            return

    if user_chat.type != 'private':
        message.reply_text("Eso no es un usuario!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "Este usuario ya está globalmente baneado; Cambiaría el motivo, pero no me has dado uno..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text(
                "Este usuario ya está baneado globalmente por la siguiente razón:\n"
                "<code>{}</code>\n"
                "Lo he actualizado con tu nueva razón!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)

        else:
            message.reply_text(
                "Este usuario ya está baneado globalmente, pero no se ha establecido ningún motivo; Lo he actualizado!"
            )

        return

    message.reply_text("En eso!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = "<b>{} ({})</b>\n".format(
            html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#BaneoGlobal\n"
        f"<b>Originado desde:</b> <code>{chat_origin}</code>\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario baneado:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>ID del usuario baneado:</b> <code>{user_chat.id}</code>\n"
        f"<b>Evento Registrado:</b> <code>{current_time}</code>")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f"\n<b>Razón:</b> <a href=\"https://telegram.me/{chat.username}/{message.message_id}\">{reason}</a>"
        else:
            log_message += f"\n<b>Razón:</b> <code>{reason}</code>"

    if GBAN_LOGS:
        try:
            log = bot.send_message(
                GBAN_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                GBAN_LOGS, log_message +
                "\n\nEl formateo se ha deshabilitado debido a un error inesperado.")

    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"No se pudo banear globalmente debido a: {excp.message}")
                if GBAN_LOGS:
                    bot.send_message(
                        GBAN_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                                 f"No se pudo banear globalmente debido a: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if GBAN_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Chats afectados:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(
            bot,
            SUDO_USERS + SUPPORT_USERS,
            f"Gban completo! (Usuario baneado en <code>{gbanned_chats}</code> chats)",
            html=True)

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("Hecho! baneado globalmente.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("Hecho! baneado globalmente.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id,
            "Ha sido expulsado globalmente de todos los grupos en los que tengo permisos administrativos."
            " Para ver el motivo haga clic en /info."
            f" Si cree que se trata de un error, puede apelar su prohibición aquí: @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass  # bot probably blocked by user


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("Eso no es un usuario!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Este usuario no está globalmente baneado!")
        return

    message.reply_text(
        f"Le daré a {user_chat.first_name} una segunda oportunidad, a nivel global.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#DesbaneoGlobal\n"
        f"<b>Originado desde:</b> <code>{chat_origin}</code>\n"
        f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Usuario desbaneado:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>ID de Usuario desbaneado:</b> <code>{user_chat.id}</code>\n"
        f"<b>Evento Registrado:</b> <code>{current_time}</code>")

    if GBAN_LOGS:
        try:
            log = bot.send_message(
                GBAN_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                GBAN_LOGS, log_message +
                "\n\nEl formateo se ha deshabilitado debido a un error inesperado.")
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_all_chats()
    ungbanned_chats = 0

    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"No se pudo cancelar el desbaneo global debido a: {excp.message}")
                if GBAN_LOGS:
                    bot.send_message(
                        GBAN_LOGS,
                        f"No se pudo cancelar el desbaneo global debido a: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        OWNER_ID, f"No se pudo cancelar el desbaneo global debido a: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if GBAN_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats afectados:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Desbaneo global completado!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(
            f"La persona ha sido desbaneada globalmente. Tomó {ungban_time} minuto's")
    else:
        message.reply_text(
            f"La persona ha sido desbaneada globalmente. Tomó {ungban_time} minuto's")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "No hay usuarios con baneados globalmente! Eres más amable de lo que esperaba...")
        return

    banfile = 'Lista de Bans Globales.\n'
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Razón: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Aquí está la lista de usuarios globalmente baneados actualmente.")


def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    try:
        sw_ban = sw.get_ban(int(user_id))
    except:
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            send_message(update.effective_message, 
                f"<b>Alerta</b>:\n"
                f"Este usuario está baneado a nivel global.\n"
                f"<b>Chat de apelación</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>ID de Usuario</b>: <code>{sw_ban.id}</code>\n"
                f"<b>Razón</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML)
            return
        else:
            return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = f"<b>Alerta</b>:\n" \
                   f"Este usuario está baneado a nivel global.\n" \
                   f"<b>Chat de apelación</b>: @{SUPPORT_CHAT}\n" \
                   f"<b>ID de usuario</b>: <code>{user_id}</code>"
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Razón:</b> <code>{html.escape(user.reason)}</code>"
            send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    try:
        restrict_permission = update.effective_chat.get_member(bot.id).can_restrict_members
    except Unauthorized:
        return
    if sql.does_chat_gban(
            update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "He habilitado bans globales en este grupo. Esto te ayudará a protegerte "
                "de spammers, personas desagradables y los trolls más grandes.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "He desactivado bans globales en este grupo. Los bans globales no afectará a sus usuarios "
                "Sin embargo, estarás menos protegido de los trolls y los spammers.")
    else:
        update.effective_message.reply_text(
            "Dame algunos argumentos para elegir una configuracion, on/off, yes/no!\n\n"
            "Tu configuración actual es: {}\n"
            "Cuando es 'True', cualquier baneo global que ocurra también ocurrirá en tu grupo. "
            "Cuando es 'False', no lo harán, dejándote a la posible merced de "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return f"{sql.num_gbanned_users()} usuarios baneados globalmente."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "<b>Baneado globalmente:</b> <code>{}</code>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS + FROG_USERS + WHITELIST_USERS:
        return ""
    if is_gbanned:
        text = text.format("Si")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Razón:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Chat de apelación:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Este chat está aplicando *baneos  globales*: `{sql.does_chat_gban(chat_id)}`."


__help__ = """
*Solo administradores:*
  •`/antispam <on/off/yes/no>`*:* Deshabilitará el efecto de los bans globales de en su grupo, o devolverá su configuración actual.

Los propietarios de bots utilizan gbans, también conocidos como baneos globales, para prohibir a los spammers en todos los grupos. Esto ayuda a proteger a \
usted y sus grupos eliminando los flooders de spam lo más rápido posible. Se pueden desactivar para su grupo llamando a \
`/antispam`
*Nota:* Los usuarios pueden apelar bans globales o denunciar spammers en *@{}*

Megu también integra la API de *@Spamwatch
* en gbans para eliminar los spammers tanto como sea posible de su sala de chat.
*¿Qué es SpamWatch?*
SpamWatch mantiene una gran lista de baneos constantemente actualizada de spambots, trolls, spammers de bitcoins y personajes desagradables[ㅤ](https://telegra.ph/file/f584b643c6f4be0b1de53.jpg)
Ayude constantemente a expulsar a los spammers de su grupo automáticamente. Por lo tanto, no tendrá que preocuparse de que los spammers asalten su grupo.
""".format(SUPPORT_CHAT, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
