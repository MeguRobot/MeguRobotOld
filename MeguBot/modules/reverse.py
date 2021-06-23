import os
from datetime import datetime
import shlex

import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional
from os.path import basename
import asyncio

from pyrogram import filters

from MeguBot import pyrogrm, logging


screen_shot = "root/temp/"

_LOG = logging.getLogger(__name__)


async def run_cmd(cmd: str) -> Tuple[str, str, int, int]:
    """run command in terminal."""
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )


async def take_screen_shot(
    video_file: str, duration: int, path: str = ""
) -> Optional[str]:
    """take a screenshot."""
    ttl = duration // 2
    thumb_image_path = path or os.path.join(screen_shot, f"{basename(video_file)}.jpg")
    command = f"ffmpeg -ss {ttl} -i '{video_file}' -vframes 1 '{thumb_image_path}'"
    err = (await run_cmd(command))[1]
    if err:
        _LOG.error(err)
    return thumb_image_path if os.path.exists(thumb_image_path) else None


@pyrogrm.on_message(filters.command('reverse'))
async def google_rs(client, message):
    start = datetime.now()
    dis_loc = ""
    out_str = "Responde a un GIF, vídeo o imagen"
    if message.reply_to_message:
        message_ = message.reply_to_message
        if message_.sticker and message_.sticker.file_name.endswith(".tgs"):
            await message.reply_text("No puedo buscar Stickers animados!")
            return
        if message_.photo or message_.animation or message_.sticker:
            dis = await client.download_media(message=message_, file_name=screen_shot)
            dis_loc = os.path.join(screen_shot, os.path.basename(dis))
        if message_.animation or message_.video:
            await message.reply_text("Buscando este GIF...")
            img_file = os.path.join(screen_shot, "grs.jpg")
            await take_screen_shot(dis_loc, 0, img_file)
            if not os.path.lexists(img_file):
                await message.reply_text("Algo salió mal en la busqueda")
                return
            dis_loc = img_file
        base_url = "http://www.google.com"
        if dis_loc:
            search_url = "{}/searchbyimage/upload".format(base_url)
            multipart = {
                "encoded_image": (dis_loc, open(dis_loc, "rb")),
                "image_content": "",
            }
            google_rs_response = requests.post(
                search_url, files=multipart, allow_redirects=False
            )
            the_location = google_rs_response.headers.get("Location")
            os.remove(dis_loc)
        else:
            await message.delete()
            return
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0"
        }
        response = requests.get(the_location, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        prs_div = soup.find_all("div", {"class": "r5a77d"})[0]
        prs_anchor_element = prs_div.find("a")
        prs_url = base_url + prs_anchor_element.get("href")
        prs_text = prs_anchor_element.text
        end = datetime.now()
        ms = (end - start).seconds
        out_str = f"""<b>Tiempo tomado</b>: <code>{ms}</code> segundos
<b>Búsqueda relacionada</b>: <a href="{prs_url}">{prs_text}</a>
<b>Más información</b>: <a href="{the_location}">Link</a>
"""
    await message.reply_text(text=out_str, parse_mode="HTML", disable_web_page_preview=True)
