import html

from MeguBot import (LOGGER, SUDO_USERS, FROG_USERS, WHITELIST_USERS,
                          dispatcher)
from MeguBot.modules.helper_funcs.chat_status import (user_admin,
                                                           user_not_admin)
from MeguBot.modules.log_channel import loggable
from MeguBot.modules.sql import reporting_sql as sql
from telegram import (Chat, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, Update)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          Filters, MessageHandler, run_async)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = SUDO_USERS + FROG_USERS + WHITELIST_USERS


@run_async
@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Reportes Activados! Recibirás una notificación cada vez que alguien reporte algo."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text(
                    "Reportes Desactivados! No recibirás ningún reporte.")
        else:
            msg.reply_text(
                f"Su configuración de reportes actual es: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Reportes activados! Los administradores que hayan activado los informes recibirán una notificación cuando alguien escriba /report "
                    "o @admin.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Reportes desactivados! No se notificará a ningún administrador con /report o @admin."
                )
        else:
            msg.reply_text(
                f"La configuración actual de este grupo es: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)


@run_async
@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if not args:
            message.reply_text("Agrega una razón para reportar primero.")
            return ""

        if user.id == reported_user.id:
            message.reply_text("Uh sí, seguro seguro... mucho más?")
            return ""

        if user.id == bot.id:
            message.reply_text("Buen intento.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("Eh? Estás reportando a los usuarios de la lista blanca?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} reportado {mention_html(reported_user.id, reported_user.first_name)} a los admins!"

            msg = (
                f"<b>⚠️ Reporte: </b>{html.escape(chat.title)}\n"
                f"<b> • Reportado por:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • Usuario reportado:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • Mensaje reportado:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">Click aquí</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        u"➡ Mensaje",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"⚠ Kickear",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}"
                    ),
                    InlineKeyboardButton(
                        u"⛔️ Banear",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"❎ Eliminar Mensaje",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = f"{mention_html(user.id, user.first_name)} reportado " \
                       f"{mention_html(reported_user.id, reported_user.first_name)} a los admins!"

            msg = f'{mention_html(user.id, user.first_name)} está llamando a los administradores en "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} mensaje reportado a los admins.",
            parse_mode=ParseMode.HTML)
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"Este chat está configurado para enviar informes de usuario a los administradores, a través de /report y @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        text = "Recibirás reportes de los grupos en los que eres administrador."
    else:
        text = "No recibirás reportes de los grupos en los que eres administrador."
    return text


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Expulsado exitosamente")
            return ""
        except Exception as err:
            query.answer("🛑 Falló al Kickear")
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅ Baneado exitosamente")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Falló al banear")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Mensaje eliminado")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Falló al eliminar mensaje!")


__help__ = """
•`/report <razón>`*:* Responde a un mensaje para informar a los administradores.
•`@admin`*:* Responde a un mensaje para informar a los administradores.
*NOTA:* Ninguno de estos se activará si lo utilizan los administradores.

*Solo administradores:*
 •`/reports <on/off>`*:* Cambiar la configuración del los reportes o ver el estado actual.
   • Si lo hace en privado, cambia su estado.
   • Si está en el grupo, cambia el estado de ese grupo.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admin(s)?"), report)

REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "Reportes"
__handlers__ = [(REPORT_HANDLER, REPORT_GROUP),
                (ADMIN_REPORT_HANDLER, REPORT_GROUP), (SETTING_HANDLER)]
