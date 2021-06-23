from datetime import datetime
from functools import wraps

from MeguBot.modules.helper_funcs.misc import is_module_loaded
from telegram.ext import CallbackContext

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from MeguBot import GBAN_LOGS, LOGGER, dispatcher
    from MeguBot.modules.helper_funcs.chat_status import user_admin
    from MeguBot.modules.sql import log_channel_sql as sql
    from telegram import ParseMode, Update
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, JobQueue, run_async
    from telegram.utils.helpers import escape_markdown

    def loggable(func):

        @wraps(func)
        def log_action(update: Update,
                       context: CallbackContext,
                       job_queue: JobQueue = None,
                       *args,
                       **kwargs):
            if not job_queue:
                result = func(update, context, *args, **kwargs)
            else:
                result = func(update, context, job_queue, *args, **kwargs)

            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Evento Registrado</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">Click acá</a>'
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)
            elif result == "" or not result:
                pass
            else:
                LOGGER.warning(
                    "%s was set as loggable, but had no return statement.",
                    func)

            return result

        return log_action

    def gloggable(func):

        @wraps(func)
        def glog_action(update: Update, context: CallbackContext, *args,
                        **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Evento Registrado</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt))

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click acá</a>'
                log_chat = str(GBAN_LOGS)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)
            elif result == "" or not result:
                pass
            else:
                LOGGER.warning(
                    "%s was set as loggable to gbanlogs, but had no return statement.",
                    func)

            return result

        return glog_action

    def send_log(context: CallbackContext, log_chat_id: str, orig_chat_id: str,
                 result: str):
        bot = context.bot
        try:
            bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id,
                    "Este canal de registro ha sido eliminado - desarmando.")
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(
                    log_chat_id, result +
                    "\n\nEl formateo se ha deshabilitado debido a un error inesperado."
                )

    @run_async
    @user_admin
    def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                f"Este grupo tiene todos sus registros enviados a:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN)

        else:
            message.reply_text("No se ha establecido ningún canal de registro para este grupo!")

    @run_async
    @user_admin
    def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Ahora, reenvíe /setlog al grupo al que desea vincular este canal!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Mensaje para eliminar no encontrado":
                    pass
                else:
                    LOGGER.exception(
                        "Error al eliminar el mensaje en el canal de registro. Aunque debería funcionar de todos modos."
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    f"Este canal se ha configurado como canal de registro para {chat.title or chat.first_name}."
                )
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "Canal log establecido correctamente!")
                else:
                    LOGGER.exception("ERROR al configurar el canal log.")

            bot.send_message(chat.id, "Canal log establecido correctamente!")

        else:
            message.reply_text("Los pasos para configurar un canal de registro son:\n"
                               " - Agregar bot al canal deseado\n"
                               " - Enviar /setlog en el canal\n"
                               " - Reenviar el /setlog al grupo\n")

    @run_async
    @user_admin
    def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel,
                             f"El canal se ha desvinculado de {chat.title}")
            message.reply_text("El canal log se ha anulado.")

        else:
            message.reply_text("Aún no se ha establecido ningún canal de registro!")

    def __stats__():
        return f"{sql.num_logchannels()} canales log establecidos."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"Este grupo tiene todos sus registros enviados a: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No se ha configurado ningún canal de registro para este grupo!"

    __help__ = """
* Solo administradores: *
•`/logchannel`*:* Obtener información del canal log.
•`/setlog`*:* Establece el canal log.
•`/unsetlog`*:* Desactiva el canal log.

La configuración del canal de registro se realiza mediante:
• Agregar el bot al canal deseado (¡como administrador!)
• Enviar `/setlog` en el canal
• Reenviar el `/setlog` al grupo

"""

    __mod_name__ = "Canal Log"

    LOG_HANDLER = CommandHandler("logchannel", logging)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func