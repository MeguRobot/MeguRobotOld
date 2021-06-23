import asyncio
from asyncio import sleep

from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins

from MeguBot import telethn, OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS


BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

INMUNES = [OWNER_ID] + DEV_USERS + SUDO_USERS + SUPPORT_USERS

# Check if user has admin rights
async def is_administrator(user_id: int, message):
    admin = False
    async for user in telethn.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in INMUNES:
            admin = True
            break
    return admin



@telethn.on(events.NewMessage(pattern=f"^[!/]delacc ?(.*)"))
async def delacc(event):

    con = event.pattern_match.group(1).lower()
    del_u = 0
    del_status = "No se encontreron cuentas eliminadas, el grupo está limpio."

    if con != "clean":
        find_delacc = await event.respond("Buscando cuentas eliminadas...")
        async for user in event.client.iter_participants(event.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = f"`{del_u}` cuentas eliminadas en este grupo.\
            \nPuedes límpiarlas usando `/delacc clean`"
        await find_delacc.edit(del_status)
        return

    # Here laying the sanity check
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not await is_administrator(user_id=event.from_id, message=event):
        await event.respond("No eres un administrador!")
        return

    if not admin and not creator:
        await event.respond("No soy administradora aquí!")
        return

    cleaning_delacc = await event.respond("Limpiando cuentas eliminadas...")
    del_u = 0
    del_a = 0

    async for user in event.client.iter_participants(event.chat_id):
        if user.deleted:
            try:
                await event.client(
                    EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                await cleaning_delacc.edit("No tengo derechos para dar ban en este grupo.")
                return
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"`{del_u}` cuentas eliminadas borradas"

    if del_a > 0:
        del_status = f"`{del_u}` cuentas eliminadas borradas \
        \n`{del_a}` cuentas eliminadas con administrador no pudieron ser eliminadas!"

    await cleaning_delacc.edit(del_status)
