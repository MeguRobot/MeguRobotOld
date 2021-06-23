from datetime import datetime

from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import User, Message

from MeguBot import pyrogrm


def ReplyCheck(m: Message):
    reply_id = None

    if m.reply_to_message:
        reply_id = m.reply_to_message.message_id

    elif not m.from_user.is_self:
        reply_id = m.message_id

    return reply_id


infotext = (
    "**[{full_name}](tg://user?id={user_id})**\n"
    " • **ID de usuario:** `{user_id}`\n"
    " • **Nombre:** `{first_name}`\n"
    " • **Segundo Nombre:** `{last_name}`\n"
    " • **Alías:** `{username}`\n"
    " • **Última vez:** `{last_online}`\n"
    " • **Biografía:** \n__{bio}__")


def LastOnline(user: User):
    if user.is_bot:
        return ""
    elif user.status == 'recently':
        return "Recientemente"
    elif user.status == 'within_week':
        return "Hace una semana"
    elif user.status == 'within_month':
        return "Hace un mes"
    elif user.status == 'long_time_ago':
        return "Hace mucho tiempo :("
    elif user.status == 'online':
        return "En línea"
    elif user.status == 'offline':
        return datetime.fromtimestamp(user.status.date).strftime("%a, %d %b %Y, %H:%M:%S")


def FullName(user: User):
    return user.first_name + " " + user.last_name if user.last_name else user.first_name


@pyrogrm.on_message(filters.command('whois'))
async def whois(c: Client, m: Message):
    cmd = m.command
    if not m.reply_to_message and len(cmd) == 1:
        get_user = m.from_user.id
    elif len(cmd) == 1:
        get_user = m.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await c.get_users(get_user)
    except PeerIdInvalid:
        await m.reply("No conozco a ese usuario.")
        return
    desc = await c.get_chat(get_user)
    desc = desc.description
    await m.reply_text(
        infotext.format(
            full_name=FullName(user),
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name if user.last_name else "None",
            username=user.username if user.username else "None",
            last_online=LastOnline(user),
            bio=desc if desc else "`Sin biografía`"),
        disable_web_page_preview=True)
