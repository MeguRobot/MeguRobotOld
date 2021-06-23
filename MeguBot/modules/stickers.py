import os
import math
import requests
import urllib.request as urllib
from PIL import Image
from html import escape
from bs4 import BeautifulSoup as bs

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError, Update
from telegram.ext import run_async, CallbackContext
from telegram.utils.helpers import mention_html

from MeguBot import dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler

combot_stickers_url = "https://combot.org/telegram/stickers?q="

@run_async
def stickerid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            "ID de sticker:\n <code>" +
            escape(msg.reply_to_message.sticker.file_id) + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text(
            "Responde al mensaje con el sticker para obtener el ID",
            parse_mode=ParseMode.HTML,
        )


@run_async
def cb_sticker(update: Update, context: CallbackContext):
    msg = update.effective_message
    split = msg.text.split(' ', 1)
    if len(split) == 1:
        msg.reply_text('Dame un nombre para buscar sticker packs.')
        return
    text = requests.get(combot_stickers_url + split[1]).text
    soup = bs(text, 'lxml')
    results = soup.find_all("a", {'class': "sticker-pack__btn"})
    titles = soup.find_all("div", "sticker-pack__title")
    if not results:
        msg.reply_text('No se han encontrado resultados :(')
        return
    reply = f"Stickers de: *{split[1]}*:"
    for result, title in zip(results, titles):
        link = result['href']
        reply += f"\n• [{title.get_text()}]({link})"
    msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


@run_async
def getsticker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        new_file = bot.get_file(file_id)
        new_file.download("sticker.png")
        bot.send_document(chat_id, document=open("sticker.png", "rb"))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text(
            "Responde a un sticker para que suba su PNG.")


@run_async
def steal(update: Update, context: CallbackContext):
    msg = update.effective_message
    user = update.effective_user
    args = context.args
    packnum = 0
    packname = "a" + str(user.id) + "_by_" + context.bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = context.bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = ("a" + str(packnum) + "_" + str(user.id) + "_by_" +
                            context.bot.username)
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    stealsticker = "stealsticker.png"
    is_animated = False
    file_id = ""

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            if msg.reply_to_message.sticker.is_animated:
                is_animated = True
            file_id = msg.reply_to_message.sticker.file_id

        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Hmm, no puedo robar eso.")

        steal_file = context.bot.get_file(file_id)
        if not is_animated:
            steal_file.download("stealsticker.png")
        else:
            steal_file.download("stealsticker.tgs")

        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"

        if not is_animated:
            try:
                im = Image.open(stealsticker)
                maxsize = (512, 512)
                if (im.width and im.height) < 512:
                    size1 = im.width
                    size2 = im.height
                    if im.width > im.height:
                        scale = 512 / size1
                        size1new = 512
                        size2new = size2 * scale
                    else:
                        scale = 512 / size2
                        size1new = size1 * scale
                        size2new = 512
                    size1new = math.floor(size1new)
                    size2new = math.floor(size2new)
                    sizenew = (size1new, size2new)
                    im = im.resize(sizenew)
                else:
                    im.thumbnail(maxsize)
                if not msg.reply_to_message.sticker:
                    im.save(stealsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("stealsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                msg.reply_text(
                    f"Sticker agregado exitosamente al sticker pack."
                    + f"\nEl emoji es: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN, 
                    reply_markup=InlineKeyboardMarkup(keyb)
                )

            except OSError as e:
                msg.reply_text("Solo puedo robar imágenes.")
                print(e)
                return

            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        png_sticker=open("stealsticker.png", "rb"),
                    )
                elif e.message == "Sticker_png_dimensions":
                    im.save(stealsticker, "PNG")
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=packname,
                        png_sticker=open("stealsticker.png", "rb"),
                        emojis=sticker_emoji,
                    )
                    keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                    msg.reply_text(
                        f"Sticker agregado exitosamente al sticker pack."
                        + f"\nEl emoji es: {sticker_emoji}",
                        parse_mode=ParseMode.MARKDOWN, 
                        reply_markup=InlineKeyboardMarkup(keyb)
                    )
                elif e.message == "Emoji de sticker no válido":
                    msg.reply_text("Emoji de válido.")
                elif e.message == "Stickers_too_much":
                    msg.reply_text(
                        "Se alcanzó el tamaño máximo del stickerpack.\nF...")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                    msg.reply_text(
                        "Sticker agregado exitosamente al sticker pack."
                        % packname + "\n"
                        "El emoji es:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN, 
                        reply_markup=InlineKeyboardMarkup(keyb)
                    )
                print(e)

        else:
            packname = "animated" + str(user.id) + "_by_" + context.bot.username
            packname_found = 0
            max_stickers = 50
            while packname_found == 0:
                try:
                    stickerset = context.bot.get_sticker_set(packname)
                    if len(stickerset.stickers) >= max_stickers:
                        packnum += 1
                        packname = ("animated" + str(packnum) + "_" +
                                    str(user.id) + "_by_" +
                                    context.bot.username)
                    else:
                        packname_found = 1
                except TelegramError as e:
                    if e.message == "Stickerset_invalid":
                        packname_found = 1
            try:
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    tgs_sticker=open("stealsticker.tgs", "rb"),
                    emojis=sticker_emoji,
                )
                keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                msg.reply_text(
                    f"Sticker agregado exitosamente al sticker pack."
                    + f"\nEl emoji es: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN, 
                    reply_markup=InlineKeyboardMarkup(keyb)
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        tgs_sticker=open("stealsticker.tgs", "rb"),
                    )
                elif e.message == "Emoji de sticker no válido":
                    msg.reply_text("Emoji no válido.")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                    msg.reply_text(
                        "Sticker agregado exitosamente al sticker pack."
                        % packname + "\n"
                        "El emoji es:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN, 
                        reply_markup=InlineKeyboardMarkup(keyb)
                    )
                print(e)

    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🤔"
            urllib.urlretrieve(png_sticker, stealsticker)
            im = Image.open(stealsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(stealsticker, "PNG")
            msg.reply_photo(photo=open("stealsticker.png", "rb"))
            context.bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open("stealsticker.png", "rb"),
                emojis=sticker_emoji,
            )
            keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
            msg.reply_text(
                f"Sticker agregado exitosamente al sticker pack."
                + f"\nEl emoji es: {sticker_emoji}",
                parse_mode=ParseMode.MARKDOWN, 
                reply_markup=InlineKeyboardMarkup(keyb)
            )
        except OSError as e:
            msg.reply_text("Solo puedo robar imágenes.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    update,
                    context,
                    msg,
                    user,
                    sticker_emoji,
                    packname,
                    packnum,
                    png_sticker=open("stealsticker.png", "rb"),
                )
            elif e.message == "Sticker_png_dimensions":
                im.save(stealsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("stealsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                msg.reply_text(
                    "Sticker agregado exitosamente al sticker pack."
                    % packname + "\n" + "El emoji es:" + " " + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN, 
                    reply_markup=InlineKeyboardMarkup(keyb)
                )
            elif e.message == "Emoji de sticker no válido":
                msg.reply_text("Emoji no válido.")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Se alcanzó el tamaño máximo del stickerpack.\nF...")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                keyb = [[InlineKeyboardButton('Steal Pack', url=f'https://t.me/addstickers/{packname}')]]
                msg.reply_text(
                    "Sticker agregado exitosamente al sticker pack."
                    % packname + "\n"
                    "El emoji es:" + " " + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN, 
                    reply_markup=InlineKeyboardMarkup(keyb)
                )
            print(e)
    else:
        packs = "Por favor, responda a un sticker o imagen para robarlo!\n\nAh, por cierto. Aquí están tus Stickerspacks:\n\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_" + context.bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"• [Steal Pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"• [Steal Pack {i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"• [Steal Pack](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("stealsticker.png"):
        os.remove("stealsticker.png")
    elif os.path.isfile("stealsticker.tgs"):
        os.remove("stealsticker.tgs")


def makepack_internal(
    update,
    context,
    msg,
    user,
    emoji,
    packname,
    packnum,
    png_sticker=None,
    tgs_sticker=None,
):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        if png_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name} Steal Pack" + extra_version,
                png_sticker=png_sticker,
                emojis=emoji,
            )
        if tgs_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name} Animated Steal Pack" + extra_version,
                tgs_sticker=tgs_sticker,
                emojis=emoji,
            )

    except TelegramError as e:
        print(e)
        if e.message == "El nombre del stickerpack ya está ocupado":
            msg.reply_text(
                "Nuevo Sticker Pack creado exitosamente.Puedes encontrarlo [aquí](https://t.me/addstickers/%s" % packname,
                parse_mode=ParseMode.MARKDOWN,
            )
        elif e.message in ("Peer_id_invalid", "El bot ha sido bloqueado por el usuario"):
            msg.reply_text(
                "Contáctame en privado primero.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="Iniciar", url=f"t.me/{context.bot.username}")
                ]]),
            )
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            msg.reply_text(
                "Stickerpack creado correctamente. Puedes encontrarlo [aquí](https://t.me/addstickers/%s" % packname,
                parse_mode=ParseMode.MARKDOWN,
        )  
        return

    if success:
        msg.reply_text(
            "Stickerpack creado correctamente. Puedes encontrarlo [aquí](https://t.me/addstickers/%s" % packname,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        msg.reply_text(
            "No se pudo crear el paquete de Stickers. Posiblemente debido a la magia negra.")


__help__ = """
•`/stickerid`*:* Responde a un sticker para decirte su ID de archivo.
•`/getsticker`*:* Responde a un sticker para subir su archivo PNG sin formato.
•`/steal`*:* Responde a un sticker para agregarlo a tu Stickerpack.
"""

__mod_name__ = "Stickers"
STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
STICKERS_HANDLER = DisableAbleCommandHandler("stickers", cb_sticker)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
STEAL_HANDLER = DisableAbleCommandHandler("steal", steal, admin_ok=True)

dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(STICKERS_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(STEAL_HANDLER)
