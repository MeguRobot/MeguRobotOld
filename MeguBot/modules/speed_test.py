import speedtest
from MeguBot import DEV_USERS, dispatcher
from MeguBot.modules.disable import DisableAbleCommandHandler
from MeguBot.modules.helper_funcs.chat_status import dev_plus
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async


def convert(speed):
    return round(int(speed) / 1048576, 2)


@dev_plus
@run_async
def speedtestxyz(update: Update, context: CallbackContext):
    buttons = [[
        InlineKeyboardButton("Imágen", callback_data="speedtest_image"),
        InlineKeyboardButton("Texto", callback_data="speedtest_text")
    ]]
    update.effective_message.reply_text(
        "Seleccione el modo de prueba de velocidad:", reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def speedtestxyz_callback(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = update.effective_message.edit_text('Corriendo prueba de velocidad...')
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = '*Resultados de Speedtest:*'

        if query.data == 'speedtest_image':
            speedtest_image = speed.results.share()
            update.effective_message.reply_photo(
                photo=speedtest_image, caption=replymsg)
            msg.delete()

        elif query.data == 'speedtest_text':
            result = speed.results.dict()
            replymsg += f"\nDescarga: `{convert(result['download'])}Mb/s`\nSubida: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            update.effective_message.edit_text(
                replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        query.answer(
            "Debes ser parte de la Asociación de Aventureros para usar este comando.")


SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(
    speedtestxyz_callback, pattern='speedtest_.*')

dispatcher.add_handler(SPEED_TEST_HANDLER)
dispatcher.add_handler(SPEED_TEST_CALLBACKHANDLER)

__mod_name__ = "SpeedTest"
__command_list__ = ["speedtest"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER]
