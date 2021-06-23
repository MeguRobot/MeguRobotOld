import datetime
import html
import textwrap

import bs4
import jikanpy
import requests
from MeguBot import DEV_USERS, OWNER_ID, SUDO_USERS, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async

info_btn = "Más Información"
kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"
prequel_btn = "⬅️ Precuela"
sequel_btn = "Continuación ➡️"
close_btn = "Cerrar ❌"


def shorten(description, info='anilist.co'):
    msg = ""
    if len(description) > 700:
        description = description[0:500] + '....'
        msg += f"\n*Descripción*:\n_{description}_[Leer más]({info})"
    else:
        msg += f"\n*Descripción*:\n_{description}_"
    return msg


#time formatter from uniborg
def t(milliseconds: int) -> str:
    """Introduce el tiempo en milisegundos, para embellecer el tiempo,
    como cuerda"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " Dias, ") if days else "") + \
        ((str(hours) + " Horas, ") if hours else "") + \
        ((str(minutes) + " Minutos, ") if minutes else "") + \
        ((str(seconds) + " Segundos, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]


airing_query = '''
    query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        episodes
        title {
          romaji
          english
          native
        }
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        } 
      }
    }
    '''

fav_query = """
query ($id: Int) { 
      Media (id: $id, type: ANIME) { 
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = '''
   query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site 
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
'''
character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               image {
                        large
               }
               description
        }
    }
"""

manga_query = """
query ($id: Int,$search: String) { 
      Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""

url = 'https://graphql.anilist.co'


@run_async
def airing(update: Update, context: CallbackContext):
    message = update.effective_message
    search_str = message.text.split(' ', 1)
    if len(search_str) == 1:
        update.effective_message.reply_text(
            'Dime el nombre del anime :) (`/airing` <nombre del anime>)')
        return
    variables = {'search': search_str[1]}
    response = requests.post(
        url, json={
            'query': airing_query,
            'variables': variables
        }).json()['data']['Media']
    msg = f"*Nombre*: *{response['title']['romaji']}*(`{response['title']['native']}`)\n*ID*: `{response['id']}`"
    if response['nextAiringEpisode']:
        time = response['nextAiringEpisode']['timeUntilAiring'] * 1000
        time = t(time)
        msg += f"\n*Episodios*: `{response['nextAiringEpisode']['episode']}`\n*Transmitiendo en*: `{time}`"
    else:
        msg += f"\n*Episodios*:{response['episodes']}\n*Estado*: `N/A`"
    update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@run_async
def anime(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Formato : `/anime` <nombre del anime>')
        return
    else:
        search = search[1]
    variables = {'search': search}
    json = requests.post(
        url, json={
            'query': anime_query,
            'variables': variables
        }).json()
    if 'errors' in json.keys():
        update.effective_message.reply_text('No se encontró el anime')
        return
    if json:
        json = json['data']['Media']
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n*Tipo*: {json['format']}\n*Estado*: {json['status']}\n*Episodios*: {json.get('episodes', 'N/A')}\n*Duración*: {json.get('duration', 'N/A')} Per Ep.\n*Puntuación*: {json['averageScore']}\n*Géneros*: `"
        for x in json['genres']:
            msg += f"{x}, "
        msg = msg[:-2] + '`\n'
        msg += "*Estudios*: `"
        for x in json['studios']['nodes']:
            msg += f"{x['name']}, "
        msg = msg[:-2] + '`\n'
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        anime_id = json['id']
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube":
                trailer = 'https://youtu.be/' + trailer_id
        description = json.get('description', 'N/A').replace('<i>', '').replace(
            '</i>', '').replace('<br>', '')
        msg += shorten(description, info)
        image = json.get('bannerImage', None)
        if trailer:
            buttons = [[
                InlineKeyboardButton("Más Información", url=info),
                InlineKeyboardButton("Trailer 🎬", url=trailer)
            ]]
        else:
            buttons = [[InlineKeyboardButton("Más Información", url=info)]]
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def character(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text(
            'Formato : `/character` <nombre del personaje>')
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(
        url, json={
            'query': character_query,
            'variables': variables
        }).json()
    if 'errors' in json.keys():
        update.effective_message.reply_text('No se encontró el personaje')
        return
    if json:
        json = json['data']['Character']
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        site_url = json.get('siteUrl')
        msg += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            update.effective_message.reply_photo(
                photo=image, caption=msg, parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN)


@run_async
def manga(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Formato : `/manga` <nombre del manga>')
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(
        url, json={
            'query': manga_query,
            'variables': variables
        }).json()
    msg = ''
    if 'errors' in json.keys():
        update.effective_message.reply_text('No se encontró el manga')
        return
    if json:
        json = json['data']['Media']
        title, title_native = json['title'].get('romaji',
                                                False), json['title'].get(
                                                    'native', False)
        start_date, status, score = json['startDate'].get(
            'year', False), json.get('status',
                                     False), json.get('averageScore', False)
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n*Fecha de estreno* - `{start_date}`"
        if status:
            msg += f"\n*Estado* - `{status}`"
        if score:
            msg += f"\n*Púntuacion* - `{score}`"
        msg += '\n*Géneros* - '
        for x in json.get('genres', []):
            msg += f"{x}, "
        msg = msg[:-2]
        info = json['siteUrl']
        buttons = [[InlineKeyboardButton("Más Información", url=info)]]
        image = json.get("bannerImage", False)
        msg += f"_{json.get('description', None)}_"
        if image:
            try:
                update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons))
        else:
            update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def upcoming(update: Update, context: CallbackContext):
    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top('anime', page=1, subtype="upcoming")

    upcoming_list = [entry['title'] for entry in upcoming['top']]
    upcoming_message = "Próximos animes:\n\n"

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    update.effective_message.reply_text(upcoming_message)


def button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    message = query.message
    data = query.data.split(", ")
    query_type = data[0]
    original_user_id = int(data[1])

    user_and_admin_list = [original_user_id, OWNER_ID] + SUDO_USERS + DEV_USERS

    bot.answer_callback_query(query.id)
    if query_type == "anime_close":
        if query.from_user.id in user_and_admin_list:
            message.delete()
        else:
            query.answer("No tienes permitido usar esto.")
    elif query_type in ('anime_anime', 'anime_manga'):
        mal_id = data[2]
        if query.from_user.id == original_user_id:
            message.delete()
            progress_message = bot.sendMessage(message.chat.id,
                                               "Buscando...")
            caption, buttons, image = get_anime_manga(mal_id, query_type,
                                                      original_user_id)
            bot.sendPhoto(
                message.chat.id,
                photo=image,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=False)
            progress_message.delete()
        else:
            query.answer("No tienes permitido usar esto.")


def site_search(update: Update, context: CallbackContext, site: str):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    more_results = True

    try:
        search_query = args[1]
    except IndexError:
        message.reply_text("Dame algo para buscar")
        return

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {'class': "post-title"})

        if search_result:
            result = f"<b>Resultados de busqueda de</b> <code>{html.escape(search_query)}</code> <b>en</b> <code>AnimeKaizoku</code>: \n"
            for entry in search_result:
                post_link = entry.a['href']
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = f"<b>No se encontraron resultados para</b> <code>{html.escape(search_query)}</code> <b>en</b> <code>AnimeKaizoku</code>"

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {'class': "title"})

        result = f"<b>Resultados de búsqueda de</b> <code>{html.escape(search_query)}</code> <b>en</b> <code>AnimeKayo</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nada encontrado":
                result = f"<b>No se encontraron resultados para</b> <code>{html.escape(search_query)}</code> <b>en</b> <code>AnimeKayo</code>"
                more_results = False
                break

            post_link = entry.a['href']
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = [[InlineKeyboardButton("Mira todos los resultados", url=search_url)]]

    if more_results:
        message.reply_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)
    else:
        message.reply_text(
            result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
def kaizoku(update: Update, context: CallbackContext):
    site_search(update, context, "kaizoku")


@run_async
def kayo(update: Update, context: CallbackContext):
    site_search(update, context, "kayo")


__help__ = """
Obtén información sobre anime, manga o personajes de [AniList](anilist.co).

*Comandos disponibles:*

 •`/anime <anime>`*:* Devuelve información sobre el anime.
 •`/character <carácter>`*:* Devuelve información sobre el carácter.
 •`/manga <manga>`*:* Devuelve información sobre el manga.
 •`/upcoming`*: * Devuelve una lista de nuevos animes en las próximas temporadas.
 •`/kaizoku <anime>`*:* Busca un anime en animekaizoku.com
 •`/kayo <anime>`*:* Busca un anime en animekayo.com
 •`/airing <anime>`*:* Devuelve información de emisión de anime.
 •`/whatanime`*:* Busca un anime respondiendo a un GIF, vídeo o imagen de una captura de un capítulo del Anime.
 """

ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)
AIRING_HANDLER = DisableAbleCommandHandler("airing", airing)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming)
KAIZOKU_SEARCH_HANDLER = DisableAbleCommandHandler("kaizoku", kaizoku)
KAYO_SEARCH_HANDLER = DisableAbleCommandHandler("kayo", kayo)
BUTTON_HANDLER = CallbackQueryHandler(button, pattern='anime_.*')

dispatcher.add_handler(BUTTON_HANDLER)
dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(AIRING_HANDLER)
dispatcher.add_handler(KAIZOKU_SEARCH_HANDLER)
dispatcher.add_handler(KAYO_SEARCH_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)

__mod_name__ = "Anime"
__command_list__ = [
    "anime", "manga", "character", "upcoming", "kaizoku", "airing",
    "kayo"
]
__handlers__ = [
    ANIME_HANDLER, CHARACTER_HANDLER, MANGA_HANDLER,
    UPCOMING_HANDLER, KAIZOKU_SEARCH_HANDLER, KAYO_SEARCH_HANDLER,
    BUTTON_HANDLER, AIRING_HANDLER
]
