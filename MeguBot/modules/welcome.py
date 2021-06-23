import html
import random
import re
import time
from functools import partial

import MeguBot.modules.sql.welcome_sql as sql
from MeguBot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    FROG_USERS,
    WHITELIST_USERS,
    sw,
    dispatcher,
    MESSAGE_DUMP
)
from MeguBot.modules.helper_funcs.chat_status import (
    is_user_ban_protected,
    user_admin,
)
from MeguBot.modules.helper_funcs.misc import build_keyboard, revert_buttons
from MeguBot.modules.helper_funcs.msg_types import get_welcome_type
from MeguBot.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
)
from MeguBot.modules.log_channel import loggable
from MeguBot.modules.sql.global_bans_sql import is_user_gbanned
from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}

VERIFIED_USER_WAITLIST = {}


# do not async
def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    cleanserv = sql.clean_service(chat.id)
    reply = update.message.message_id
    # Clean service welcome
    if cleanserv:
        try:
            dispatcher.bot.delete_message(chat.id, update.message.message_id)
        except BadRequest:
            pass
        reply = False
    try:
        msg = update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            reply_to_message_id=reply,
        )
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            msg = update.effective_message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
                quote=False
            )
        elif excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNota: El mensaje actual tiene una URL no válida "
                    "en uno de sus botones. Por favor actualice."),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Protocolo de URL no admitido":
            msg = update.effective_message.reply_text(
                markdown_parser(backup_message +
                                "\nNota: el mensaje actual tiene botones que "
                                "utilizan protocolos de URL que no son compatibles con "
                                "Telegram. Por favor actualice."),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Host de URL incorrecto":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message +
                    "\nNota: el mensaje actual tiene algunas URL incorrectas. "
                    "Por favor actualice."),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("No se pudo analizar! obtuve errores de host de URL no válidas")
        else:
            msg = update.effective_message.reply_text(
                markdown_parser(backup_message +
                                "\nNota: Se produjo un error al enviar el "
                                "mensaje personalizado. Por favor actualice."),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.exception()

    return msg


@run_async
@loggable
def new_member(update: Update, context: CallbackContext):
    bot, job_queue = context.bot, context.job_queue
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(
        chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)

    new_members = update.effective_message.new_chat_members

    for new_mem in new_members:

        welcome_log = None
        res = None
        sent = None
        should_mute = True
        welcome_bool = True
        media_wel = False

        if sw != None:
            sw_ban = sw.get_ban(new_mem.id)
            if sw_ban:
                return

        if should_welc:

            reply = update.message.message_id
            cleanserv = sql.clean_service(chat.id)
            # Clean service welcome
            if cleanserv:
                try:
                    dispatcher.bot.delete_message(chat.id,
                                                  update.message.message_id)
                except BadRequest:
                    pass
                reply = False

            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "Oh, ¿que haces aquí Kazuma?.",
                    reply_to_message_id=reply)
                welcome_log = (f"{html.escape(chat.title)}\n"
                               f"#EntradaUsuario\n"
                               f"El propietario del bot acaba de unirse al chat!")
                continue

            # Welcome Devs
            elif new_mem.id in DEV_USERS:
                update.effective_message.reply_text(
                    "Eh! Un Demonio Carmesí acaba de unirse!",
                    reply_to_message_id=reply,
                )
                continue

            # Welcome Sudos
            elif new_mem.id in SUDO_USERS:
                update.effective_message.reply_text(
                    "Eh! ¡Un Destroyer acaba de unirse!",
                    reply_to_message_id=reply,
                )
                continue

            # Welcome Support
            elif new_mem.id in SUPPORT_USERS:
                update.effective_message.reply_text(
                    "Eh! Un Demonio acaba de unirse!",
                    reply_to_message_id=reply,
                )
                continue

            # Welcome Whitelisted
            elif new_mem.id in FROG_USERS:
                update.effective_message.reply_text(
                    "Uf! Una rana gigante acaba de unirse! xd",
                    reply_to_message_id=reply)
                continue

            # Welcome Frogs
            elif new_mem.id in WHITELIST_USERS:
                update.effective_message.reply_text(
                    "Uf! Un Sapo acaba de unirse! xd",
                    reply_to_message_id=reply)
                continue

            # Welcome yourself
            elif new_mem.id == bot.id:
                update.effective_message.reply_text(
                    "Hola! gracias por añadirme al grupo! :3", reply_to_message_id=reply)
                bot.send_message(MESSAGE_DUMP, "#NuevoGrupo\n<b>Nombre del grupo:</b> {}\n<b>ID:</b> <pre>{}</pre>".format(chat.title, chat.id), parse_mode=ParseMode.HTML)
                continue

            else:
                buttons = sql.get_welc_buttons(chat.id)
                keyb = build_keyboard(buttons)

                if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                    media_wel = True

                first_name = (
                    new_mem.first_name or "PersonWithNoName"
                )  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if cust_welcome == sql.DEFAULT_WELCOME:
                        cust_welcome = random.choice(
                            sql.DEFAULT_WELCOME_MESSAGES).format(
                                first=escape_markdown(first_name))

                    if new_mem.last_name:
                        fullname = escape_markdown(
                            f"{first_name} {new_mem.last_name}")
                    else:
                        fullname = escape_markdown(first_name)
                    count = chat.get_members_count()
                    mention = mention_markdown(new_mem.id,
                                               escape_markdown(first_name))
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome, VALID_WELCOME_FORMATTERS)
                    res = valid_format.format(
                        first=escape_markdown(first_name),
                        last=escape_markdown(new_mem.last_name or first_name),
                        fullname=escape_markdown(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=escape_markdown(chat.title),
                        id=new_mem.id,
                    )

                else:
                    res = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                        first=escape_markdown(first_name))
                    keyb = []

                backup_message = random.choice(
                    sql.DEFAULT_WELCOME_MESSAGES).format(
                        first=escape_markdown(first_name))
                keyboard = InlineKeyboardMarkup(keyb)

        else:
            welcome_bool = False
            res = None
            keyboard = None
            backup_message = None
            reply = None

        # User exceptions from welcomemutes
        if (is_user_ban_protected(chat, new_mem.id, chat.get_member(new_mem.id))
                or human_checks):
            should_mute = False
        # Join welcome: soft mute
        if new_mem.is_bot:
            should_mute = False

        if user.id == new_mem.id:
            if should_mute:
                if welc_mutes == "soft":
                    bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_add_web_page_previews=False,
                        ),
                        until_date=(int(time.time() + 24 * 60 * 60)),
                    )
                if welc_mutes == "strong":
                    welcome_bool = False
                    if not media_wel:
                        VERIFIED_USER_WAITLIST.update({
                            new_mem.id: {
                                "should_welc": should_welc,
                                "media_wel": False,
                                "status": False,
                                "update": update,
                                "res": res,
                                "keyboard": keyboard,
                                "backup_message": backup_message,
                            }
                        })
                    else:
                        VERIFIED_USER_WAITLIST.update({
                            new_mem.id: {
                                "should_welc": should_welc,
                                "chat_id": chat.id,
                                "status": False,
                                "media_wel": True,
                                "cust_content": cust_content,
                                "welc_type": welc_type,
                                "res": res,
                                "keyboard": keyboard,
                            }
                        })
                    new_join_mem = f"[{escape_markdown(new_mem.first_name)}](tg://user?id={user.id})"
                    message = msg.reply_text(
                        f"{new_join_mem}, Haz clic en el botón de abajo para demostrar que no eres un robot.\nTienes 2 minutos.",
                        reply_markup=InlineKeyboardMarkup([{
                            InlineKeyboardButton(
                                text="Soy un humano",
                                callback_data=f"user_join_({new_mem.id})",
                            )
                        }]),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=reply,
                    )
                    bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False,
                        ),
                    )
                    job_queue.run_once(
                        partial(check_not_bot, new_mem, chat.id,
                                message.message_id),
                        120,
                        name="welcomemute",
                    )

        if welcome_bool:
            if media_wel:
                sent = ENUM_FUNC_MAP[welc_type](
                    chat.id,
                    cust_content,
                    caption=res,
                    reply_markup=keyboard,
                    reply_to_message_id=reply,
                    parse_mode="markdown",
                )
            else:
                sent = send(update, res, keyboard, backup_message)
            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

        if welcome_log:
            return welcome_log

        return (f"{html.escape(chat.title)}\n"
                f"#EntradaUsuario\n"
                f"<b>Usuario</b>: {mention_html(user.id, user.first_name)}\n"
                f"<b>ID</b>: <code>{user.id}</code>")

    return ""


def check_not_bot(member, chat_id, message_id, context):
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop(member.id)
    member_status = member_dict.get("status")
    if not member_status:
        try:
            bot.unban_chat_member(chat_id, member.id)
        except:
            pass

        try:
            bot.edit_message_text(
                "*Kickea al usuario*\nSiempre pueden volver e intentar.",
                chat_id=chat_id,
                message_id=message_id,
            )
        except:
            pass


@run_async
def left_member(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)

    if user.id == bot.id:
        return

    if should_goodbye:
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        # Clean service welcome
        if cleanserv:
            try:
                dispatcher.bot.delete_message(chat.id,
                                              update.message.message_id)
            except BadRequest:
                pass
            reply = False

        left_mem = update.effective_message.left_chat_member
        if left_mem:

            # Thingy for spamwatched users
            if sw != None:
                sw_ban = sw.get_ban(left_mem.id)
                if sw_ban:
                    return

            # Dont say goodbyes to gbanned users
            if is_user_gbanned(left_mem.id):
                return

            # Ignore bot being kicked
            if left_mem.id == bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "Oh! Kazuma! Salió...", reply_to_message_id=reply)
                return

            # Give the devs a special goodbye
            elif left_mem.id in DEV_USERS:
                update.effective_message.reply_text(
                    "Nos vemos luego ^^!",
                    reply_to_message_id=reply,
                )
                return

            # if media goodbye, use appropriate function for it
            if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = (left_mem.first_name or "PersonaSinNombre"
                         )  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if cust_goodbye == sql.DEFAULT_GOODBYE:
                    cust_goodbye = random.choice(
                        sql.DEFAULT_GOODBYE_MESSAGES).format(
                            first=escape_markdown(first_name))
                if left_mem.last_name:
                    fullname = escape_markdown(
                        f"{first_name} {left_mem.last_name}")
                else:
                    fullname = escape_markdown(first_name)
                count = chat.get_members_count()
                mention = mention_markdown(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape_markdown(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS)
                res = valid_format.format(
                    first=escape_markdown(first_name),
                    last=escape_markdown(left_mem.last_name or first_name),
                    fullname=escape_markdown(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape_markdown(chat.title),
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = random.choice(
                    sql.DEFAULT_GOODBYE_MESSAGES).format(first=first_name)
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(
                update,
                res,
                keyboard,
                random.choice(
                    sql.DEFAULT_GOODBYE_MESSAGES).format(first=first_name),
            )


@run_async
@user_admin
def welcome(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    # if no args, show current replies.
    if not args or args[0].lower() == "noformat":
        noformat = True
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            f"Este chat tiene su configuración de bienvenida establecida en: `{pref}`.\n"
            f"*El mensaje de bienvenida (sin llenar los* `{{}}`*) es:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if welcome_type == sql.Types.BUTTON_TEXT or welcome_type == sql.Types.TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)
        else:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id, cust_content, caption=welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id,
                    cust_content,
                    caption=welcome_m,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "si"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "Bueno! Saludaré a los miembros cuando se unan.")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "Voy a holgazanear y no dar la bienvenida a nadie entonces.")

        else:
            update.effective_message.reply_text(
                "Solo entiendo 'on/si' y 'off/no'!")


@run_async
@user_admin
def goodbye(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat

    if not args or args[0] == "noformat":
        noformat = True
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            f"Este chat tiene su configuración de despedida configurada en: `{pref}`.\n"
            f"*El mensaje de despedida (sin llenar los {{}}) es:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN)

    elif len(args) >= 1:
        if args[0].lower() in ("on", "si"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text("Ok!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text("Ok!")

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "Solo entiendo 'on/si' y 'off/no'!")


@run_async
@user_admin
@loggable
def set_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("No especificaste con qué responder!")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    msg.reply_text("Mensaje de bienvenida personalizado configurado correctamente!")

    return (f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ConfiguracionBienvenda\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"Se estableció el mensaje de bienvenida.")


@run_async
@user_admin
@loggable
def reset_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user

    sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Se restableció correctamente el mensaje de bienvenida a los valores predeterminados!")

    return (f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ReinicioBienvenida\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"Se restableció el mensaje de bienvenida a los valores predeterminados.")


@run_async
@user_admin
@loggable
def set_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("No especificaste con qué responder!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Mensaje de despedida personalizado configurado correctamente!")
    return (f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ConfiguracionDespedida\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"Se estableció el mensaje de despedida.")


@run_async
@user_admin
@loggable
def reset_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user

    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Se restablecio correctamente el mensaje de despedida a los valores predeterminados!")

    return (f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ReinicioDespedida\n"
            f"<b>Administrador:</b> {mention_html(user.id, user.first_name)}\n"
            f"Se restableció el mensaje de despedida.")


@run_async
@user_admin
@loggable
def welcomemute(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            msg.reply_text("Ya no silenciaré a las personas al unirse!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#SilenciadoBienvenida\n"
                f"<b>• Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha puesto la bienvenida silenciada en <b>apagado</b>.")
        elif args[0].lower() in ["soft"]:
            sql.set_welcome_mutes(chat.id, "soft")
            msg.reply_text(
                "Restringiré el permiso de los usuarios para enviar contenido multimedia durante 24 horas.")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#SilenciadoBienvenida\n"
                f"<b>• Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha alternado bienvenida muda a <b>SOFT</b>.")
        elif args[0].lower() in ["strong"]:
            sql.set_welcome_mutes(chat.id, "strong")
            msg.reply_text(
                "Ahora silenciaré a las personas cuando se unan hasta que demuestren que no son un bot.\nTendrán 2 minutos antes de que los kickee."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#SilienciadoBienvenida\n"
                f"<b>• Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha alternado bienvenida muda a <b>STRONG</b>.")
        else:
            msg.reply_text(
                "Por favor escribe `off`/`no`/`soft`/`strong`!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = (
            f"\n Dame una configuracion!\nElija uno entre: `off`/`no` or `soft` or `strong`!\n"
            f"Configuración actual: `{curr_setting}`")
        msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
        return ""


@run_async
@user_admin
@loggable
def clean_welcome(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text(
                "Debería eliminar los mensajes de bienvenida con hasta dos días de antigüedad.")
        else:
            update.effective_message.reply_text(
                "Actualmente no estoy eliminando mensajes de bienvenida anteriores!")
        return ""

    if args[0].lower() in ("on", "si"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text(
            "Intentaré borrar los mensajes de bienvenida antiguos!")
        return (f"<b>{html.escape(chat.title)}:</b>\n"
                f"#LimpiezaBienvenida\n"
                f"<b>• Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha cambiado la limpieza de bienvenida a <code>ON</code>.")
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text(
            "No borraré los mensajes de bienvenida antiguos.")
        return (f"<b>{html.escape(chat.title)}:</b>\n"
                f"#CLEAN_WELCOME\n"
                f"<b>• Administrador:</b> {mention_html(user.id, user.first_name)}\n"
                f"Ha cambiado la limpieza de bienvenida a <code>OFF</code>.")
    else:
        update.effective_message.reply_text(
            "Solo entiendo 'on/yes' or 'off/no' solamente!")
        return ""


@run_async
@user_admin
def cleanservice(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var in ("no", "off"):
                sql.set_clean_service(chat.id, False)
                update.effective_message.reply_text(
                    "El servicio de limpieza de bienvenida está: Apagado")
            elif var in ("si", "on"):
                sql.set_clean_service(chat.id, True)
                update.effective_message.reply_text(
                    "El servicio de limpieza de bienvenida está: Encendido")
            else:
                update.effective_message.reply_text(
                    "Opción no válida", parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                "El uso es on/si o off/no", parse_mode=ParseMode.MARKDOWN)
    else:
        curr = sql.clean_service(chat.id)
        if curr:
            update.effective_message.reply_text(
                "El servicio de limpieza de bienvenida está: Encendido", parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                "El servicio de limpieza de bienvenida está: Apagado", parse_mode=ParseMode.MARKDOWN)


@run_async
def user_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    join_user = int(match.group(1))

    if join_user == user.id:
        sql.set_human_checks(user.id, chat.id)
        member_dict = VERIFIED_USER_WAITLIST.pop(user.id)
        member_dict["status"] = True
        VERIFIED_USER_WAITLIST.update({user.id: member_dict})
        query.answer(text="Eres un humano, des-silenciado!")
        bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        try:
            bot.deleteMessage(chat.id, message.message_id)
        except:
            pass
        if member_dict["should_welc"]:
            if member_dict["media_wel"]:
                sent = ENUM_FUNC_MAP[member_dict["welc_type"]](
                    member_dict["chat_id"],
                    member_dict["cust_content"],
                    caption=member_dict["res"],
                    reply_markup=member_dict["keyboard"],
                    parse_mode="markdown",
                )
            else:
                sent = send(
                    member_dict["update"],
                    member_dict["res"],
                    member_dict["keyboard"],
                    member_dict["backup_message"],
                )

            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

    else:
        query.answer(text="No tienes permitido hacer esto!")


WELC_HELP_TXT = (
    "Los mensajes de bienvenida/despedida de su grupo se pueden personalizar!"
    "Puedes usar estas variables:\n"
    " •`{first}`*:* El *nombre* del usuario.\n"
    " •`{last}`*:* El *apellido* del usuario. El predeterminado es *nombre* si el usuario no lo tiene"
    " •`{fullname}`*:* El *nombre completo* del usuario. Por defecto es su nombre si el usuario no lo tiene"
    " •`{username}`*:* Esto representa el alias del usuario. Por defecto es una mención del usuario."
    " •`{mention}`*:* Esto simplemente menciona al usuario, etiquetándolo con su nombre.\n"
    " •`{id}`*:* Esto representa el ID del usuario"
    " •`{count}`*:* Esto representa el número de miembro del usuario.\n"
    " •`{chatname}`*:* Esto representa el nombre del grupo.\n"
    "\nCada variable DEBE estar rodeada por `{}` para ser reemplazada.\n"
    "Los mensajes de bienvenida también admiten markdown, por lo que puede poner cualquier elemento en negrita, cursiva ,código y enlaces.\n"
    "Los botones también son compatibles, por lo que puede hacer que su bienvenida se vea increíble con botones\n"
    f"Para crear un botón que se vincule a sus reglas, use esto:`[Reglas](buttonurl://t.me/{dispatcher.bot.username}?start=group_id)`."
    "Simplemente reemplace `group_id` con la ID de su grupo, que se puede obtener a través de `/id`."
    "Incluso puede configurar imágenes/gifs/videos/mensajes de voz como mensaje de bienvenida "
    "respondiendo al medio deseado con `/setwelcome`.")

WELC_MUTE_HELP_TXT = (
     "Puede hacer que el bot silencie a las personas nuevas y así evitar que los spambots floodeen su grupo\n"
     "•`/welcomemute soft`*:* Impide que los nuevos envíen multimedia durante 24 horas.\n"
     "•`/welcomemute strong`*:* Silencia a los nuevos hasta que presionen el botón, verificando que son humanos.\n"
     "•`/welcomemute off`*:* Desactiva el mute de bienvenida.\n"
     "*Nota:* El modo `strong` expulsa a un usuario del chat si no verifica en 2 minutos. Aunque siempre puede volver a unirse.")


@run_async
@user_admin
def welcome_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)


@run_async
@user_admin
def welcome_mute_help(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        WELC_MUTE_HELP_TXT, parse_mode=
ParseMode.MARKDOWN
    )


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    return (
        
"Configuración de bienvenida establecida en `{}`.\n"
            "Configuración de despedida establecida en `{}`.".format(
                welcome_pref, goodbye_pref)
    )


__help__ = """
{}

*Solo administradores:*
 •`/welcome <on/off>`*:* Habilitar/deshabilitar los mensajes de bienvenida.
 •`/welcome`*:* Muestra la configuración de bienvenida actual.
 •`/welcome noformat`*:* Muestra la configuración de bienvenida actual, sin el formato, útil para cambiar sus mensajes de bienvenida!
 •`/goodbye`*:* (Despedidas) mismo uso que `/welcome`.
 •`/setwelcome <sometext>`*:* Establece un mensaje de bienvenida personalizado. Si quiere usar multimedia, responda al mensaje con el comando y texto.
 •`/setgoodbye <sometext>`*:* Establece un mensaje de despedida personalizado. Si quiere usar multimedia, responda al mensaje con el comando y texto.
 •`/resetwelcome`*:* Restablece el mensaje de bienvenida predeterminado.
 •`/resetgoodbye`*:* Restablece el mensaje de despedida predeterminado.
 •`/cleanwelcome <on/off>`*:* Si hay un miembro nuevo, elimina el mensaje de bienvenida anterior para evitar spam.
 •`/welcomemutehelp`*:* Proporciona información sobre el mute de bienvenida.
 •`/welcomehelp`*:* Ver más información de formato para mensajes personalizados de bienvenida/despedida.
 •`/cleanservice <on/off>`*:* Borra los mensajes de bienvenida/despedida de servicio de Telegram.
""".format(
    WELC_HELP_TXT
)

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members,
                                 new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member,
                                  left_member)
WELC_PREF_HANDLER = CommandHandler("welcome", welcome, filters=Filters.group)
GOODBYE_PREF_HANDLER = CommandHandler("goodbye", goodbye, filters=Filters.group)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_GOODBYE = CommandHandler("setgoodbye", set_goodbye, filters=Filters.group)
RESET_WELCOME = CommandHandler(
    "resetwelcome", reset_welcome, filters=Filters.group)
RESET_GOODBYE = CommandHandler(
    "resetgoodbye", reset_goodbye, filters=Filters.group)
WELCOMEMUTE_HANDLER = CommandHandler(
    "welcomemute", welcomemute, filters=Filters.group)
CLEAN_SERVICE_HANDLER = CommandHandler(
    "cleanservice", cleanservice, filters=Filters.group)
CLEAN_WELCOME = CommandHandler(
    "cleanwelcome", clean_welcome, filters=Filters.group)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)
WELCOME_MUTE_HELP = CommandHandler("welcomemutehelp", welcome_mute_help)
BUTTON_VERIFY_HANDLER = CallbackQueryHandler(user_button, pattern=r"user_join_")

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(WELCOME_HELP)
dispatcher.add_handler(WELCOMEMUTE_HANDLER)
dispatcher.add_handler(CLEAN_SERVICE_HANDLER)
dispatcher.add_handler(BUTTON_VERIFY_HANDLER)
dispatcher.add_handler(WELCOME_MUTE_HELP)

__mod_name__ = "Saludos"
__command_list__ = []
__handlers__ = [
    NEW_MEM_HANDLER,
    LEFT_MEM_HANDLER,
    WELC_PREF_HANDLER,
    GOODBYE_PREF_HANDLER,
    SET_WELCOME,
    SET_GOODBYE,
    RESET_WELCOME,
    RESET_GOODBYE,
    CLEAN_WELCOME,
    WELCOME_HELP,
    WELCOMEMUTE_HANDLER,
    CLEAN_SERVICE_HANDLER,
    BUTTON_VERIFY_HANDLER,
    WELCOME_MUTE_HELP,
]
