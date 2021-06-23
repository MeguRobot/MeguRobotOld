from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from MeguBot import (DEL_CMDS, DEV_USERS, SUDO_USERS, SUPPORT_CHAT, SUPPORT_USERS,
                          FROG_USERS, WHITELIST_USERS, dispatcher)

from telegram import Chat, ChatMember, ParseMode, Update
from telegram.ext import CallbackContext

# stores admemes in memory for 10 min.
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)
THREAD_LOCK = RLock()


def is_whitelist_plus(chat: Chat,
                      user_id: int,
                      member: ChatMember = None) -> bool:
    return any(user_id in user
               for user in [WHITELIST_USERS, FROG_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS])


def is_support_plus(chat: Chat,
                    user_id: int,
                    member: ChatMember = None) -> bool:
    return user_id in SUPPORT_USERS or user_id in SUDO_USERS or user_id in DEV_USERS


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in SUDO_USERS or user_id in DEV_USERS


def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if (chat.type == 'private' or user_id in SUDO_USERS or user_id in DEV_USERS or
            chat.all_members_are_administrators or
            user_id in [777000, 1087968824]):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        with THREAD_LOCK:
            # try to fetch from cache first.
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                # keyerror happend means cache is deleted,
                # so query bot api again and return user status
                # while saving it in cache for future useage...
                chat_admins = dispatcher.bot.getChatAdministrators(chat.id)
                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                if user_id in admin_list:
                    return True
                return False


def is_bot_admin(chat: Chat,
                 bot_id: int,
                 bot_member: ChatMember = None) -> bool:
    if chat.type == 'private' or chat.all_members_are_administrators:
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)

    return bot_member.status in ('administrator', 'creator')


def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages


def is_user_ban_protected(chat: Chat,
                          user_id: int,
                          member: ChatMember = None) -> bool:
    if (chat.type == 'private' or user_id in SUDO_USERS or user_id in DEV_USERS or
            user_id in WHITELIST_USERS or user_id in FROG_USERS or
            chat.all_members_are_administrators or
            user_id in [777000, 1087968824]):  # Count telegram and Group Anonymous as admin
        return True

    if not member:
        member = chat.get_member(user_id)

    return member.status in ('administrator', 'creator')


def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = chat.get_member(user_id)
    return member.status not in ('left', 'kicked')


def dev_plus(func):

    @wraps(func)
    def is_dev_plus_func(update: Update, context: CallbackContext, *args,
                         **kwargs):
        bot = context.bot
        user = update.effective_user

        if user.id in DEV_USERS:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "Este es un comando restringido por desarrolladores."
                " No tienes permisos para ejecutar este.")

    return is_dev_plus_func


def sudo_plus(func):

    @wraps(func)
    def is_sudo_plus_func(update: Update, context: CallbackContext, *args,
                          **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_sudo_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "No eres administrador y me dices qué hacer? Quieren que lo haga volar?")

    return is_sudo_plus_func


def support_plus(func):

    @wraps(func)
    def is_support_plus_func(update: Update, context: CallbackContext, *args,
                             **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_support_plus_func


def whitelist_plus(func):

    @wraps(func)
    def is_whitelist_plus_func(update: Update, context: CallbackContext, *args,
                               **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                f"No tienes acceso para usar esto.\nVisita @{SUPPORT_CHAT}")

    return is_whitelist_plus_func


def user_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()
        else:
            update.effective_message.reply_text(
                "No eres administrador y me dice qué hacer? Quieren que lo haga volar?")

    return is_admin


def user_admin_no_reply(func):

    @wraps(func)
    def is_not_admin_no_reply(update: Update, context: CallbackContext, *args,
                              **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        elif DEL_CMDS and " " not in update.effective_message.text:
            update.effective_message.delete()

    return is_not_admin_no_reply


def user_not_admin(func):

    @wraps(func)
    def is_not_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        user = update.effective_user
        chat = update.effective_chat

        if user and not is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass

    return is_not_admin


def bot_admin(func):

    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            not_admin = "No soy admin :("
        else:
            not_admin = f"No soy administrador en <b>{update_chat_title}</b>! :("

        if is_bot_admin(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                not_admin, parse_mode=ParseMode.HTML)

    return is_admin


def bot_can_delete(func):

    @wraps(func)
    def delete_rights(update: Update, context: CallbackContext, *args,
                      **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "No puedo borrar mensajes aquí!\nAsegúrate de que soy administradora y pueda eliminar los mensajes de otros usuarios."
        else:
            cant_delete = f"No puedo borrar mensajes en <b>{update_chat_title}</b>!\nMake sure I'm admin and can delete other user's messages there."

        if can_delete(chat, bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_delete, parse_mode=ParseMode.HTML)

    return delete_rights


def can_pin(func):

    @wraps(func)
    def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = "No puedo fijar mensajes aquí!\nAsegúrate de que soy administradora y pueda fijar mensajes."
        else:
            cant_pin = f"No puedo anclar mensajes en <b>{update_chat_title}</b>!\nAsegúrate de que soy administradora y pueda fijar mensajes allí."

        if chat.get_member(bot.id).can_pin_messages:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_pin, parse_mode=ParseMode.HTML)

    return pin_rights


def can_promote(func):

    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args,
                       **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_promote = "No puedo ascender/degradar personas aquí!\nAsegúrate de que soy administradora y pueda añadir nuevos administradores."
        else:
            cant_promote = (
                f"No puedo ascender/degradar a personas en <b>{update_chat_title}</b>!\n"
                f"Asegúrate de que soy administradora allí y puedoa añadir nuevos administradores.")

        if chat.get_member(bot.id).can_promote_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_promote, parse_mode=ParseMode.HTML)

    return promote_rights


def can_restrict(func):

    @wraps(func)
    def restrict_rights(update: Update, context: CallbackContext, *args,
                        **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_restrict = "No puedo restringir a la gente aquí!\nAsegúrate de que soy administradora y pueda restringir usuarios."
        else:
            cant_restrict = f"No puedo restringir a la gente en <b>{update_chat_title}</b>!\nAsegúrate de que soy administradora allí y puedas restringir a los usuarios."

        if chat.get_member(bot.id).can_restrict_members:
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text(
                cant_restrict, parse_mode=ParseMode.HTML)

    return restrict_rights


def user_can_ban(func):

    @wraps(func)
    def user_is_banhammer(update: Update, context: CallbackContext, *args,
                          **kwargs):
        bot = context.bot
        user = update.effective_user.id
        member = update.effective_chat.get_member(user)
        if not (member.can_restrict_members or member.status == "creator"
               ) and not user in SUDO_USERS and user not in [777000, 1087968824]:
            update.effective_message.reply_text(
                "Lo siento hijo, pero no eres digno de blandir el bastón.")
            return ""
        return func(update, context, *args, **kwargs)

    return user_is_banhammer


def connection_status(func):

    @wraps(func)
    def connected_status(update: Update, context: CallbackContext, *args,
                         **kwargs):
        conn = connected(
            context.bot,
            update,
            update.effective_chat,
            update.effective_user.id,
            need_admin=False)

        if conn:
            chat = dispatcher.bot.getChat(conn)
            update.__setattr__("_effective_chat", chat)
            return func(update, context, *args, **kwargs)
        else:
            if update.effective_message.chat.type == "private":
                update.effective_message.reply_text(
                    "Envía `/connect` en un grupo que tú y yo tenemos en común primero.",
                parse_mode=ParseMode.MARKDOWN)
                return connected_status

            return func(update, context, *args, **kwargs)

    return connected_status


# Workaround for circular import with connection.py
from MeguBot.modules import connection

connected = connection.connected
