import re
import random
from html import escape

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, Message, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    DispatcherHandlerStop,
    run_async,
    Filters,
)
from telegram.utils.helpers import mention_html, escape_markdown

from MeguBot import dispatcher, LOGGER, SUDO_USERS
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.handlers import MessageHandlerChecker
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.extraction import extract_text
from MeguBot.modules.helper_funcs.filters import CustomFilters
from MeguBot.modules.helper_funcs.misc import build_keyboard_parser
from MeguBot.modules.helper_funcs.msg_types import get_filter_type
from MeguBot.modules.helper_funcs.string_handling import (
    split_quotes,
    button_markdown_parser,
    escape_invalid_curly_brackets,
    markdown_to_html,
)
from MeguBot.modules.sql import cust_filters_sql as sql

from MeguBot.modules.connection import connected

from MeguBot.modules.helper_funcs.alternate import send_message, typing_action

HANDLER_GROUP = 10

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    # sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note
}


@run_async
@typing_action
def list_handlers(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        filter_list = "*Triggers en  {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
            filter_list = "*Triggers Locales:*\n"
        else:
            chat_name = chat.title
            filter_list = "*Triggers en {}*:\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        send_message(update.effective_message,
                     "No hay triggers guardados en{}!".format(chat_name))
        return

    for keyword in all_handlers:
        entry = " • `{}`\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            send_message(
                update.effective_message,
                filter_list.format(chat_name),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            filter_list = entry
        else:
            filter_list += entry

    send_message(
        update.effective_message,
        filter_list.format(chat_name),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = connected(context.bot, update, chat, user.id)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local filters"
        else:
            chat_name = chat.title

    if not msg.reply_to_message and len(args) < 2:
        send_message(
            update.effective_message,
            "Proporcione la palabra clave para que este trigger responda!",
        )
        return

    if msg.reply_to_message:
        if len(args) < 2:
            send_message(
                update.effective_message,
                "Proporcione la palabra clave para que este trigger responda!",
            )
            return
        else:
            keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if not text:
            send_message(
                update.effective_message,
                "No hay mensaje de nota: No puede SÓLO tener botones, necesita un mensaje para acompañarlo!",
            )
            return

    elif msg.reply_to_message and len(args) >= 2:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                    )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()

    elif not text and not file_type:
        send_message(
            update.effective_message,
            "Proporcione la palabra clave para que este trigger responda!",
        )
        return

    elif msg.reply_to_message:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                    )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if (msg.reply_to_message.text or
                msg.reply_to_message.caption) and not text:
            send_message(
                update.effective_message,
                "No hay mensaje de nota: No puede SÓLO tener botones, necesita un mensaje para acompañarlo!",
            )
            return

    else:
        send_message(update.effective_message, "Trigger no válido!")
        return

    sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)
    # This is an old method
    # sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video, buttons)

    send_message(
        update.effective_message,
        "Trigger '{}' guardado en *{}*!".format(keyword, chat_name),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def stop_filter(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
        else:
            chat_name = chat.title

    if len(args) < 2:
        send_message(update.effective_message, "Que trigger debo borrar?")
        return

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        send_message(update.effective_message, "No hay triggers aquí!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            send_message(
                update.effective_message,
                "Ok, dejaré de responder a ese trigger en *{}*.".format(
                    chat_name),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            raise DispatcherHandlerStop

    send_message(
        update.effective_message,
        "Ese no es un trigger actual: Pon /filters para ver todos los triggers activos.",
    )


@run_async
def reply_filter(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    if update.effective_user.id == 777000:
        return
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            if MessageHandlerChecker.check_user(update.effective_user.id):
                return
            filt = sql.get_filter(chat.id, keyword)
            if filt.reply == "there is should be a new reply":
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                VALID_WELCOME_FORMATTERS = [
                    "first",
                    "last",
                    "fullname",
                    "username",
                    "id",
                    "chatname",
                    "mention",
                ]
                if filt.reply_text:
                    if '%%%' in filt.reply_text:
                        text = random.choice(filt.reply_text.split('%%%'))
                    else:
                        text = filt.reply_text
                    if text.startswith('~!') and text.endswith('!~'):
                        sticker_id = text.replace('~!', '').replace('!~', '')
                        try:
                            context.bot.send_sticker(
                                chat.id,
                                sticker_id,
                                reply_to_message_id=message.message_id
                            )
                            return
                        except BadRequest as excp:
                            if excp.message == 'Wrong remote file identifier specified: wrong padding in the string':
                                context.bot.send_message(chat.id, "No se pudo enviar el mensaje. Es válido el Sticker ID?")
                                return
                            else:
                                LOGGER.exception("Error in filters: " + excp.message)
                                return
                    valid_format = escape_invalid_curly_brackets(
                        text, VALID_WELCOME_FORMATTERS)
                    if valid_format:
                        filtext = valid_format.format(
                            first=escape(message.from_user.first_name),
                            last=escape(message.from_user.last_name or
                                        message.from_user.first_name),
                            fullname=" ".join(
                                [
                                    escape(message.from_user.first_name),
                                    escape(message.from_user.last_name),
                                ] if message.from_user.last_name else
                                [escape(message.from_user.first_name)]),
                            username="@" + escape(message.from_user.username)
                            if message.from_user.username else mention_html(
                                message.from_user.id,
                                message.from_user.first_name),
                            mention=mention_html(message.from_user.id,
                                                 message.from_user.first_name),
                            chatname=escape(message.chat.title)
                            if message.chat.type != "private" else escape(
                                message.from_user.first_name),
                            id=message.from_user.id,
                        )
                    else:
                        filtext = ""
                else:
                    filtext = ""

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        context.bot.send_message(
                            chat.id,
                            markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        error_catch = get_exception(excp, filt, chat)
                        if error_catch == "noreply":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    markdown_to_html(filtext),
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Failed to send message: " +
                                                 excp.message)
                                pass
                else:
                    try:
                        ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            caption=markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest:
                        send_message(message, "No tengo permiso para enviar el contenido del trigger.")
                break
            else:
                if filt.is_sticker:
                    message.reply_sticker(filt.reply)
                elif filt.is_document:
                    message.reply_document(filt.reply)
                elif filt.is_image:
                    message.reply_photo(filt.reply)
                elif filt.is_audio:
                    message.reply_audio(filt.reply)
                elif filt.is_voice:
                    message.reply_voice(filt.reply)
                elif filt.is_video:
                    message.reply_video(filt.reply)
                elif filt.has_markdown:
                    buttons = sql.get_buttons(chat.id, filt.keyword)
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)

                    try:
                        send_message(
                            update.effective_message,
                            filt.reply,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        if excp.message == "Protocolo de URL no admitido":
                            try:
                                send_message(
                                    update.effective_message,
                                   "Parece que intentas utilizar un protocolo de URL no compatible. Telegram "
                                   "no admite botones para algunos protocolos, como tg://. Por favor, inténtalo "
                                    f"de nuevo, o pregunta en {SUPPORT_CHAT} por ayuda."
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                        elif excp.message == "Reply message not found":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    filt.reply,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    "Este mensaje no se pudo enviar porque tiene un formato incorrecto.",
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                            LOGGER.warning("Message %s could not be parsed",
                                           str(filt.reply))
                            LOGGER.exception(
                                "Could not parse filter %s in chat %s",
                                str(filt.keyword),
                                str(chat.id),
                            )

                else:
                    # LEGACY - all new filters will have has_markdown set to True.
                    try:
                        send_message(update.effective_message, filt.reply)
                    except BadRequest as excp:
                        LOGGER.exception("Error in filters: " + excp.message)
                        pass
                break


@run_async
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Solo el propietario del chat puede borrar todos los triggers.")
    else:
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="Eliminar Triggers", callback_data="filters_rmall")
        ], [
            InlineKeyboardButton(text="Cancelar", callback_data="filters_cancel")
        ]])
        update.effective_message.reply_text(
            f"¿Está seguro de que desea borrar *TODOS* los triggers en {chat.title}? Esta acción no se puede deshacer.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN)


@run_async
def rmall_callback(update, context):
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == 'filters_rmall':
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_triggers(chat.id)
            if not allfilters:
                msg.edit_text("Sin triggers en este chat, no hay nada para borrar!")
                return

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)

            for i in filterlist:
                sql.remove_filter(chat.id, i)

            msg.edit_text(f"{count} triggers borrados en {chat.title}")

        if member.status == "administrator":
            query.answer("Solo el propietario del grupo puede hacer esto.")

        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")
    elif query.data == 'filters_cancel':
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("Se canceló la eliminación de todos los triggers.")
            return
        if member.status == "administrator":
            query.answer("Solo el propietario del grupo puede hacer esto.")
        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")


# NOT ASYNC NOT A HANDLER
def get_exception(excp, filt, chat):
    if excp.message == "Protocolo de URL no admitido":
        return "Parece que intentas utilizar un protocolo de URL no compatible. Telegram no admite botones para algunos protocolos, como tg://. Por favor, inténtalo de nuevo"
    elif excp.message == "Reply message not found":
        return "noreply"
    else:
        LOGGER.warning("Message %s could not be parsed", str(filt.reply))
        LOGGER.exception("Could not parse filter %s in chat %s",
                         str(filt.keyword), str(chat.id))
        return "Estos datos no se pudieron enviar porque están formateados incorrectamente."


def __stats__():
    return "{} triggers, en {} chats.".format(sql.num_filters(),
                                                   sql.num_chats())


def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get("filters", {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "Hay `{}` triggers aquí.".format(len(cust_filters))


__help__ = """

•`/triggers`*:* Lista todos los triggers activos en este chat.

*Solo administradores:*
•`/settrigger <palabra clave> <mensaje de respuesta>`*:* Agrega un trigger a este chat. El bot ahora responderá ese mensaje siempre que una palabra clave \
sea mencionada. Si responde a un sticker/video/gif con una palabra clave, el bot responderá con ese medio.\
Si desea que su palabra clave sea una oración, use comillas.
*Ejemplo:*`/settrigger "Hola allí"¿Cómo estás?`
•`/delttriger <palabra clave de trigger>`*:* Detiene ese trigger.

Separe las respuestas random con `%%%` para obtener respuestas aleatorias 
*Ejemplo:*
`/trigger <nombredeltrigger>
Respuesta 1
%%%
Respuesta 2
%%%
Respuesta 3`

*Solo propietario del grupo:*
•`/removealltriggers`*:* Elimina todos los triggers del chat a la vez.

*Nota:* Los triggers también admiten markdown como: {firts}, {last}, etc. y botones.
¡Pon `/markdownhelp` para saber más!
"""

__mod_name__ = "Triggers"

FILTER_HANDLER = CommandHandler("settrigger", filters)
STOP_HANDLER = CommandHandler("deltrigger", stop_filter)
RMALLFILTER_HANDLER = CommandHandler(
    "rmalltriggers", rmall_filters, filters=Filters.group)
RMALLFILTER_CALLBACK = CallbackQueryHandler(rmall_callback, pattern=r"filters_.*")
LIST_HANDLER = DisableAbleCommandHandler(
    "triggers", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & ~Filters.update.edited_message, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
dispatcher.add_handler(RMALLFILTER_HANDLER)
dispatcher.add_handler(RMALLFILTER_CALLBACK)

__handlers__ = [
    FILTER_HANDLER, STOP_HANDLER, LIST_HANDLER,
    (CUST_FILTER_HANDLER, HANDLER_GROUP, RMALLFILTER_HANDLER)
]
