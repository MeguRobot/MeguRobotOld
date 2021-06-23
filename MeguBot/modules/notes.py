import re, ast
from io import BytesIO
from typing import Optional

import MeguBot.modules.sql.notes_sql as sql
from MeguBot import LOGGER, MESSAGE_DUMP, SUPPORT_CHAT, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.handlers import MessageHandlerChecker
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.misc import (build_keyboard,
                                                    revert_buttons)
from MeguBot.modules.helper_funcs.msg_types import get_note_type
from MeguBot.modules.helper_funcs.string_handling import escape_invalid_curly_brackets
from telegram import (MAX_MESSAGE_LENGTH, InlineKeyboardMarkup, Message,
                      ParseMode, Update)
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_markdown
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)
from telegram.ext.dispatcher import run_async

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
def get(update, context, notename, show_none=True, no_format=False):
    bot = context.bot
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=MESSAGE_DUMP,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Mensaje para reenviar no encontrado":
                        message.reply_text(
                            "Parece que este mensaje se ha perdido; lo eliminaré "
                            "de la lista de notas.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=chat_id,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Parece que se ha eliminado el remitente original de esta nota "
                            "su mensaje - ¡lo siento! Haga que su administrador de bot comience a usar un "
                            "guardado de mensajes para evitar esto. Eliminaré esta nota de "
                            "sus notas guardadas.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                'first', 'last', 'fullname', 'username', 'id', 'chatname',
                'mention'
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS)
            if valid_format:
                text = valid_format.format(
                    first=escape_markdown(message.from_user.first_name),
                    last=escape_markdown(message.from_user.last_name or
                                         message.from_user.first_name),
                    fullname=escape_markdown(
                        " ".join([
                            message.from_user.first_name, message.from_user
                            .last_name
                        ] if message.from_user.last_name else
                                 [message.from_user.first_name])),
                    username="@" + message.from_user.username
                    if message.from_user.username else mention_markdown(
                        message.from_user.id, message.from_user.first_name),
                    mention=mention_markdown(message.from_user.id,
                                             message.from_user.first_name),
                    chatname=escape_markdown(
                        message.chat.title if message.chat.type != "private"
                        else message.from_user.first_name),
                    id=message.from_user.id)
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(
                        chat_id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)
                else:
                    ENUM_FUNC_MAP[note.msgtype](
                        chat_id,
                        note.file,
                        caption=text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Parece que trataste de mencionar a alguien a quien nunca había visto antes. Si tú realmente "
                        "quieres mencionarlos, reenviarme uno de sus mensajes y podré "
                        "etiquetarlo!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "Esta nota era un archivo importado incorrectamente de otro bot; no puedo usar "
                        "eso. Si realmente lo necesita, tendrá que guardarlo nuevamente. Mientras"
                        "tanto, lo eliminaré de tu lista de notas.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text(
                        "Esta nota no se pudo enviar porque tiene un formato incorrecto. Entra a "
                        f"@{SUPPORT_CHAT} si no puedes entender por qué!")
                    LOGGER.exception("Could not parse message #%s in chat %s",
                                     notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Esta nota no existe")


@run_async
def cmd_get(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("")


@run_async
def hash_get(update: Update, context: CallbackContext):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    get(update, context, no_hash, show_none=False)


@run_async
def slash_get(update: Update, context: CallbackContext):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        get(update, context, note_name, show_none=False)
    except IndexError:
        update.effective_message.reply_text("ID de nota incorrecta")


@run_async
@user_admin
def save(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)
    note_name = note_name.lower()
    if data_type is None:
        msg.reply_text("Amigo, no hay nota")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content)

    msg.reply_text(
        f"Yas! Added `{note_name}`.\nConsíguelo con /get `{note_name}`, or `#{note_name}`",
        parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text(
                "Parece que estás intentando guardar un mensaje de un bot. Desafortunadamente, "
                "los bots no pueden reenviar mensajes de bot, por lo que no puedo guardar el mensaje exacto. "
                "\nGuardaré todo el texto que pueda, pero si quieres más, tendrás que "
                "reenvíar el mensaje y luego guárdarlo.")
        else:
            msg.reply_text(
                "Los bots están un poco discapacitados por telegram, lo que dificulta que los bots "
                "interactuar con otros bots, así que no puedo guardar este mensaje "
                "como lo haría normalmente, ¿te importaría reenviarlo y "
                "luego guardando ese nuevo mensaje? Gracias!")
        return


@run_async
@user_admin
def clear(update: Update, context: CallbackContext):
    args = context.args
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Nota eliminada con éxito.")
        else:
            update.effective_message.reply_text(
                "Esa no es una nota en mi base de datos!")


@run_async
def list_notes(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Obtén la nota con /get o #nombredenota \n\n  *ID*    *Notas* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if not note_list:
        try:
            update.effective_message.reply_text("No hay notas en este chat!")
        except BadRequest:
            update.effective_message.reply_text("No hay notas en este chat!", quote=False)

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata,
                                   sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end():].strip()
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.STICKER,
                    file=content)
        elif matchbtn:
            parse = notedata[matchbtn.end():].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end():].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.DOCUMENT,
                    file=content)
        elif matchphoto:
            photo = notedata[matchphoto.end():].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.PHOTO,
                    file=content)
        elif matchaudio:
            audio = notedata[matchaudio.end():].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.AUDIO,
                    file=content)
        elif matchvoice:
            voice = notedata[matchvoice.end():].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VOICE,
                    file=content)
        elif matchvideo:
            video = notedata[matchvideo.end():].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO,
                    file=content)
        elif matchvn:
            video_note = notedata[matchvn.end():].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO_NOTE,
                    file=content)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="Estos archivos/fotos no se pudieron importar debido a que se originaron "
                "de otro bot. Esta es una restricción de la API de telegram y no puede "
                "ser evitado. Lo siento por los inconvenientes!",
            )


def __stats__():
    return f"{sql.num_notes()} notas, en {sql.num_chats()} chats."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"There are `{len(notes)}` notes in this chat."


__help__ = """
 •`/get <notename>`*:* Obtiene la nota con este notename.
 •`#<nombre>` *:* Igual que `/get`.
 •`/notes` o `/saved`*:* Lista todas las notas guardadas en este chat
 •`/<número>*:* Sacará la nota de ese número en la lista.
Si desea recuperar el contenido de una nota sin ningún formato, use `/get <nombrenota> noformat`. 
Esto puede ser útil al actualizar una nota actual.

*Solo administradores:*
 •`/save <nombre> <datos>`*:* Guarda los datos de la nota como una nota con un nombre
Se puede agregar un botón a una nota utilizando la sintaxis de enlace de markdown estándar; el enlace debe ir precedido de una \
`buttonurl:` sección, como tal: `[somelink](buttonurl:example.com)`. 
Consulte `/markdownhelp` para obtener más información.
 •`/save <NombredeNota>`*:* Guarda el mensaje respondido como una nota con el nombre de la nota.

Separe las respuestas con `%%%` para obtener respuestas aleatorias 
*Ejemplo:*
`/save <NombredeNota>
Respuesta 1
%%%
Respuesta 2
%%%
Respuesta 3`
 •`/clear <NombredeNota>`*:* Borrar nota con ese nombre
  *Nota:* Los nombres de las notas no distinguen entre mayúsculas y minúsculas y se convierten automáticamente a minúsculas antes de guardarse.
"""

__mod_name__ = "Notas"

GET_HANDLER = CommandHandler("get", cmd_get)
HASH_GET_HANDLER = MessageHandler(Filters.regex(r"^#[^\s]+"), hash_get)
SLASH_GET_HANDLER = MessageHandler(Filters.regex(r"^\/[0-9]*$"), slash_get)
SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"],
                                         list_notes,
                                         admin_ok=True)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(SLASH_GET_HANDLER)
