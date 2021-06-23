from typing import Optional

from telegram import Message, Update, User, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters, CallbackContext
from telegram.utils.helpers import escape_markdown

import MeguBot.modules.sql.rules_sql as sql
from MeguBot import dispatcher
from MeguBot.modules.helper_funcs.chat_status import user_admin
from MeguBot.modules.helper_funcs.string_handling import markdown_parser


@run_async
def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "¡Las reglas para este chat no se han configurado correctamente! Avisa a los administradores para "
                "que arreglen esto.")
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"Las reglas de *{escape_markdown(chat.title)}* son:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)
    elif from_pm:
        bot.send_message(
            user.id, "Los administradores del grupo aún no han puesto ninguna regla para este chat.\n\n "
            "Aunque esto probablemente no significa que se puedan hacer cosas ilegales...")
    elif rules:
        update.effective_message.reply_text("Contáctame en privado para ver las reglas de este grupo.",
                                            reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="Reglas",
                                                                    url=f"t.me/{bot.username}?start={chat_id}")]]))
    else:
        update.effective_message.reply_text(
            "Los administradores del grupo aún no han puesto ninguna regla para este chat.\n\n "
            "Aunque esto probablemente no significa que se puedan hacer cosas ilegales...")


@run_async
@user_admin
def set_rules(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    # use python's maxsplit to separate cmd and args
    args = raw_text.split(None, 1)
    if len(args) == 2:
        txt = args[1]
        # set correct offset relative to command
        offset = len(txt) - len(raw_text)
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset)

        chat_id = update.effective_chat.id
        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text(
            "Reglas del grupo establecidas exitosamente.")


@run_async
@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Reglas borradas exitosamente!")


def __stats__():
    return f"{sql.num_chats()} chats tienen las reglas establecidas."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get('info', {}).get('rules', "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _user_id):
    return f"This chat has had it's rules set: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
•`/rules`*:* Obtén las reglas del grupo.
*Solo administradores:*
•`/setrules <reglas aqui>`*:* Establece las reglas del grupo.
•`/clearrules`*:* Quita las reglas del grupo.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.group)
SET_RULES_HANDLER = CommandHandler(
    "setrules", set_rules, filters=Filters.group)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.group)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
