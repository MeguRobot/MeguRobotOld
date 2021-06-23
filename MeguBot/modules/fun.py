import html
import random
import time

import MeguBot.modules.fun_strings as fun_strings
from MeguBot import dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import (is_user_admin)
from MeguBot.modules.helper_funcs.extraction import extract_user
from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async

normiefont = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
]
weebyfont = [
    '卂', '乃', '匚', '刀', '乇', '下', '厶', '卄', '工', '丁', '长', '乚', '从', '𠘨', '口',
    '尸', '㔿', '尺', '丂', '丅', '凵', 'リ', '山', '乂', '丫', '乙'
]


@run_async
def weebify(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    string = ""

    if message.reply_to_message:
        string = message.reply_to_message.text.lower().replace(" ", "  ")

    if args:
        string = '  '.join(args).lower()

    if not string:
        message.reply_text(
            "El uso es `/weebify <texto>`", parse_mode=ParseMode.MARKDOWN)
        return

    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)

    if message.reply_to_message:
        message.reply_to_message.reply_text(string)
    else:
        message.reply_text(string)


@run_async
def runs(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.RUN_STRINGS))


@run_async
def slap(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat

    reply_text = message.reply_to_message.reply_text if message.reply_to_message else message.reply_text

    curr_user = html.escape(message.from_user.first_name)
    user_id = extract_user(message, args)

    if user_id == bot.id:
        temp = random.choice(fun_strings.SLAP_MEGU_TEMPLATES)

        if isinstance(temp, list):
            if temp[2] == "tmute":
                if is_user_admin(chat, message.from_user.id):
                    reply_text(temp[1])
                    return

                mutetime = int(time.time() + 60)
                bot.restrict_chat_member(
                    chat.id,
                    message.from_user.id,
                    until_date=mutetime,
                    permissions=ChatPermissions(can_send_messages=False))
            reply_text(temp[0])
        else:
            reply_text(temp)
        return

    if user_id:

        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        user2 = html.escape(slapped_user.first_name)

    else:
        user1 = bot.first_name
        user2 = curr_user

    temp = random.choice(fun_strings.SLAP_TEMPLATES)
    item = random.choice(fun_strings.ITEMS)
    hit = random.choice(fun_strings.HIT)
    throw = random.choice(fun_strings.THROW)

    reply = temp.format(
        user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(fun_strings.TOSS))


@run_async
def roll(update, context):
    bot = context.bot
    chat_id = update.message.chat_id
    bot.send_dice(chat_id, value=6, emoji="")
    

@run_async
def shrug(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    reply_text(r"¯\_(ツ)_/¯")


@run_async
def rlg(update: Update, context: CallbackContext):
    eyes = random.choice(fun_strings.EYES)
    mouth = random.choice(fun_strings.MOUTHS)
    ears = random.choice(fun_strings.EARS)

    if len(eyes) == 2:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[1] + ears[1]
    else:
        repl = ears[0] + eyes[0] + mouth[0] + eyes[0] + ears[1]
    update.message.reply_text(repl)


@run_async
def decide(update: Update, context: CallbackContext):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(fun_strings.DECIDE))


@run_async
def table(update: Update, context: CallbackContext):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text(random.choice(fun_strings.TABLE))


__help__ = """
•`/runs`*:* Responde una cadena aleatoria de una matriz de respuestas.
•`/slap`*:* Abofetear a un usuario, o recibir una bofetada si no hay a quien reponder.
•`/shrug`*:* Shrugs XD.
•`/table`*:* Obtener flip/unflip.
•`/decide`*:* Responde aleatoriamente sí/no/tal vez
•`/toss`*:* Lanza una moneda
•`/roll`*:* Tira un dado
•`/rlg`*:* Une oídos, nariz, boca y crea un emo ;-;
•`/shout <palabra clave>`*:* Escribe cualquier cosa que quieras dar un grito fuerte
•`/weebify <text>`*:* Devuelve un texto weebify
•`/police`*:* Envía una animación con emojis de sirena de policía.
"""


WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss)
ROLL_HANDLER = DisableAbleCommandHandler("roll", roll)
SHRUG_HANDLER = DisableAbleCommandHandler("shrug", shrug)
RLG_HANDLER = DisableAbleCommandHandler("rlg", rlg)
DECIDE_HANDLER = DisableAbleCommandHandler("decide", decide)
TABLE_HANDLER = DisableAbleCommandHandler("table", table)

dispatcher.add_handler(WEEBIFY_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)
dispatcher.add_handler(ROLL_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(RLG_HANDLER)
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(TABLE_HANDLER)

__mod_name__ = "Diversión"
__command_list__ = [
    "weebify", "runs", "slap", "toss", "roll", "shrug", "rlg", "decide",
    "table"
]
__handlers__ = [
    WEEBIFY_HANDLER, RUNS_HANDLER, SLAP_HANDLER, TOSS_HANDLER, ROLL_HANDLER, SHRUG_HANDLER, RLG_HANDLER, DECIDE_HANDLER, TABLE_HANDLER
]
