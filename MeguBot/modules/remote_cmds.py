from MeguBot import dispatcher
from MeguBot.modules.helper_funcs.chat_status import (
    bot_admin, is_bot_admin, is_user_ban_protected, is_user_in_chat)
from MeguBot.modules.helper_funcs.extraction import extract_user_and_text
from MeguBot.modules.helper_funcs.filters import CustomFilters
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async

RBAN_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat"
}

RUNBAN_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat"
}

RKICK_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat"
}

RMUTE_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat"
}

RUNMUTE_ERRORS = {
    "El usuario es administrador del grupo", "Chat not found",
    "No hay suficientes derechos para restringir/no restringir al miembro del chat",
    "User_not_participant", "Peer_id_invalid", "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private", "Not in the chat"
}


@run_async
@bot_admin
def rban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un grupo/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto"
        )
        return
    elif not chat_id:
        message.reply_text("Parece que no te refieres a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat no encontrado! Asegúrese de haber ingresado una ID de chat válida y yo sea parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Lo siento, pero es un chat privado!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "No puedo restringir a la gente allí! Asegúrate de que soy administradora y pueda bloquear usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder banear a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("Yo no voy a BANEAR, estás loco?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Baneado del chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Bueno maldita sea, no puedo prohibir a ese usuario.")


@run_async
@bot_admin
def runban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un grupo/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return
    elif not chat_id:
        message.reply_text("Parece que no te refieres a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat no encontrado! Asegúrese de haber ingresado una ID de chat válida y yo sea parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Lo siento, pero es un chat privado!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "¡No puedo dejar de restringir a la gente! Asegúrate de que soy administrador y puedo desbloquear usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario there")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Por qué intentas desbanear de forma remota a alguien que ya está en ese chat?"
        )
        return

    if user_id == bot.id:
        message.reply_text("No voy a DESBANEARME, soy administradora allí!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Ok, este usuario puede unirse a ese chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Desbaneado!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unbanning user %s in chat %s (%s) due to %s", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Well damn, I can't unban that user.")


@run_async
@bot_admin
def rkick(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un grupo/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return
    elif not chat_id:
        message.reply_text("Parece que no te refieres a un grupo.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat no encontrado! Asegúrese de haber ingresado una ID de chat válida y yo sea parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Lo siento, pero es un chat privado!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "¡No puedo restringir a la gente allí! Asegúrate de que sea administradora y pueda expulsar usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder kickear a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("No me voy a kickear, ¿estás loco??")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Kickeado del chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Kickeado!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR kicking user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Bueno maldita sea, no puedo expulsar a ese usuario.")


@run_async
@bot_admin
def rmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un grupo/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return
    elif not chat_id:
        message.reply_text("Parece que no te refieres a un grupo.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat no encontrado! Asegúrese de haber ingresado una ID de chat válida y yo sea parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Lo siento, pero es un chat privado!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "¡No puedo restringir a la gente allí! Asegúrate de que sea administradora y pueda silenciar a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder silenciar a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("No me voy a silenciar, estás loco?")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False))
        message.reply_text("Muteado en el chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Muteado!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR mute user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Bueno maldita sea, no puedo silenciar a ese usuario.")


@run_async
@bot_admin
def runmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un grupo/suario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se refiera a un usuario o el ID especificado es incorrecto."
        )
        return
    elif not chat_id:
        message.reply_text("Parece que no te refieres a un grupo.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text(
                "Chat no encontrado! Asegúrese de haber ingresado una ID de chat válida y yo sea parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Lo siento, pero es un chat privado!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "No puedo dejar de restringir a la gente! Asegúrate de que sea administradora y pueda desbloquear usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        if member.can_send_messages and member.can_send_media_messages \
           and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text(
                "Este usuario ya tiene derecho a hablar en ese chat.")
            return

    if user_id == bot.id:
        message.reply_text("No voy a DESMUTARME, soy un administradora allí!")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True))
        message.reply_text("Ok, este usuario puede hablar en ese chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Desmuteado!', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unmnuting user %s in chat %s (%s) due to %s", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Bueno maldita sea, no puedo silenciar a ese usuario.")



RBAN_HANDLER = CommandHandler("rban", rban, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler(
    "runban", runban, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler(
    "rkick", rkick, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler(
    "rmute", rmute, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler(
    "runmute", runmute, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
