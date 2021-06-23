import aiohttp
from datetime import datetime
from asyncio import sleep

from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
from MeguBot import pyrogrm


class AioHttp:
    @staticmethod
    async def get_json(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.json()

    @staticmethod
    async def get_text(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.text()

    @staticmethod
    async def get_raw(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.read()


@pyrogrm.on_message(filters.command("spbinfo"))
async def lookup(client, message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        if message.reply_to_message.forward_from:
            get_user = message.reply_to_message.forward_from.id
        else:
            get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await client.get_chat(get_user)
    except PeerIdInvalid:
        await message.reply_text("No conozco a ese usuario.")
        sleep(2)
        return
    url = f"https://api.intellivoid.net/spamprotection/v1/lookup?query={user.id}"
    a = await AioHttp().get_json(url)
    response = a["success"]
    if response == True:
        date = a["results"]["last_updated"]
        stats = f"**◢ Intellivoid• SpamProtection Info**:\n"
        stats += f' • **Actualizado**: `{datetime.fromtimestamp(date).strftime("%Y-%m-%d %I:%M:%S %p")}`\n'
        stats += (
            f" • **Información de chat**: [Link](t.me/SpamProtectionBot/?start=00_{user.id})\n"
        )

        if a["results"]["attributes"]["is_potential_spammer"] == True:
            stats += f" • **Usuario**: `USERxSPAM`\n"
        elif a["results"]["attributes"]["is_operator"] == True:
            stats += f" • **Usuario**: `USERxOPERATOR`\n"
        elif a["results"]["attributes"]["is_agent"] == True:
            stats += f" • **Usuario**: `USERxAGENT`\n"
        elif a["results"]["attributes"]["is_whitelisted"] == True:
            stats += f" • **Usuario**: `USERxWHITELISTED`\n"

        stats += f' • **Tipo**: `{a["results"]["entity_type"]}`\n'
        stats += (
            f' • **Idioma**: `{a["results"]["language_prediction"]["language"]}`\n'
        )
        stats += f' • **Predicción de Idioma**: `{a["results"]["language_prediction"]["probability"]}`\n'
        stats += f"**Predicción de Spam**:\n"
        stats += f' • **Predicción de Ham**: `{a["results"]["spam_prediction"]["ham_prediction"]}`\n'
        stats += f' • **Predicción de Spam**: `{a["results"]["spam_prediction"]["spam_prediction"]}`\n'
        stats += f'**En la lista negra**: `{a["results"]["attributes"]["is_blacklisted"]}`\n'
        if a["results"]["attributes"]["is_blacklisted"] == True:
            stats += (
                f' • **Razón**: `{a["results"]["attributes"]["blacklist_reason"]}`\n'
            )
            stats += f' • **Bandera**: `{a["results"]["attributes"]["blacklist_flag"]}`\n'
        stats += f'**ID Privado**:\n\n`{a["results"]["private_telegram_id"]}`\n'
        await message.reply_text(stats, disable_web_page_preview=True)
    else:
        await message.reply_text("`No pude acceder a la API de SpamProtection`")
        await sleep(3)
