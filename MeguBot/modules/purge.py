import time
from telethon import events

from MeguBot.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages, user_is_admin)
from MeguBot import telethn


async def purge_messages(event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(user_id=event.sender_id, message=event) and event.from_id not in [1087968824]:
        await event.reply("Solo los administradores pueden usar este comando.")
        return

    if not await can_delete_messages(message=event)and event.from_id not in [1087968824]:
        await event.reply("Parece que no puedo eliminar el mensaje")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "Responde a un mensaje para seleccionar desde dónde empezar a eliminar.")
        return
    messages = []
    message_id = reply_msg.id
    delete_to = event.message.id

    messages.append(event.reply_to_msg_id)
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        pass
    time_ = time.perf_counter() - start
    text = f"Eliminacion exitosa en {time_:0.2f} segundo(s)"
    await event.respond(text, parse_mode='markdown')


async def delete_messages(event):
    if event.from_id is None:
        return

    if not await user_is_admin(user_id=event.sender_id, message=event) and event.from_id not in [1087968824]:
        await event.reply("Solo los administradores pueden usar este comando.")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Parece que no puedes eliminar esto?")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply("Qué quieres eliminar?")
        return
    chat = await event.get_input_chat()
    del_message = [message, event.message]
    await event.client.delete_messages(chat, del_message)


__help__ = """
*Solo administradores:*
 •`/del`*:* Elimina el mensaje al que respondió
 •`/purge`*:* Elimina todos los mensajes entre este y el mensaje respondido.
 •`/purge <X>`*:* Elimina el mensaje respondido y los X mensajes que lo siguen si respondieron a un mensaje.
"""

PURGE_HANDLER = purge_messages, events.NewMessage(pattern="^[!/]purge$")
DEL_HANDLER = delete_messages, events.NewMessage(pattern="^[!/]del$")

telethn.add_event_handler(*PURGE_HANDLER)
telethn.add_event_handler(*DEL_HANDLER)

__mod_name__ = "Eliminacion"
__command_list__ = [
    "del", "purge"
]
__handlers__ = [
    PURGE_HANDLER, DEL_HANDLER
]
