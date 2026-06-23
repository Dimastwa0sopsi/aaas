import asyncio
import logging
import secrets
import string
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8914142458:AAGdwsswgp7b0nN9f8OCyNs_IYMx2gQkK5Q"
OWNER_ID = 8415068937
SITE_URL = "https://dimastwa0sopsi.github.io/Banana/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

support_requests = {}
pending_codes = {}

class SupportStates(StatesGroup):
    waiting_for_problem = State()
    waiting_for_code = State()
    waiting_for_dev_message = State()

def generate_password():
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(12))

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 Поддержка игры", callback_data="game_support")],
    [InlineKeyboardButton(text="📩 Регистрация аккаунта", callback_data="register_account")],
    [InlineKeyboardButton(text="👨‍💻 Связь с разработчиком", callback_data="contact_dev")]
])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать в поддержку Banana Shooter! 🍌\n\n"
        "Я здесь чтобы помочь вам с:\n"
        "• Техническими проблемами и вопросами по игре!\n"
        "• Регистрацией и управлением аккаунтом!\n"
        "• Связью с главным разработчиком!\n\n"
        "Выберите пункт который вам нужен!",
        reply_markup=main_kb
    )

@dp.message(Command("menu"))
async def menu(message: types.Message, state: FSMContext):
    await state.clear()
    await start(message)

# 1. Поддержка игры
@dp.callback_query(F.data == "game_support")
async def support_btn(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Хорошо. Пожалуйста напишите суть проблемы, и отправьте нам, также вы можете приложить скриншот проблемы.")
    await state.set_state(SupportStates.waiting_for_problem)
    await callback.answer()

@dp.message(SupportStates.waiting_for_problem)
async def problem_msg(message: types.Message, state: FSMContext):
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    uid = message.from_user.id
    uname = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    
    text = f"🎮 <b>Новое обращение в поддержку!</b>\n\nОбращение: {message.text or 'Без текста'}\nВремя: {now}\nusername: {uname}\nuser_id: <code>{uid}</code>"
    
    if message.photo:
        msg = await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=text, parse_mode="HTML")
    else:
        msg = await bot.send_message(OWNER_ID, text, parse_mode="HTML")
    
    support_requests[msg.message_id] = uid
    await message.answer("Ваше обращение отправлено! Ожидайте ответа от поддержки.")
    await state.clear()

# 2. Регистрация
@dp.callback_query(F.data == "register_account")
async def reg_btn(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔗 Зайти на сайт", url=SITE_URL)]])
    await callback.message.answer(
        "Хорошо, нажмите на кнопку ниже и зайдите на сайт.\n\n"
        "На сайте укажите:\n• Ваш Telegram ID\n• Желаемый никнейм\n\n"
        "Затем нажмите «Сгенерировать код» и отправьте его сюда.",
        reply_markup=kb
    )
    await state.set_state(SupportStates.waiting_for_code)
    await callback.answer()

@dp.message(SupportStates.waiting_for_code)
async def code_msg(message: types.Message, state: FSMContext):
    code = message.text.strip()
    uid = message.from_user.id
    
    if code not in pending_codes:
        await message.answer("❌ Неверный или устаревший код.")
        return
    
    if pending_codes[code]["user_id"] != uid:
        await message.answer("❌ Этот код для другого пользователя!")
        return
    
    data = pending_codes.pop(code)
    pwd = generate_password()
    
    await message.answer(
        f"✅ <b>Вы зарегистрированы!</b>\n\nНикнейм: <code>{data['nickname']}</code>\nПароль: <tg-spoiler><code>{pwd}</code></tg-spoiler>\n\n<i>Нажмите на пароль, чтобы скопировать.</i>",
        parse_mode="HTML"
    )
    await state.clear()

@dp.message(F.text.startswith("/register_code"))
async def site_code(message: types.Message):
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer("❌ Формат: /register_code КОД user_id НИК")
        return
    
    _, code, uid_str, nick = parts
    try:
        uid = int(uid_str)
    except:
        await message.answer("❌ user_id должен быть числом")
        return
    
    pending_codes[code] = {"user_id": uid, "nickname": nick}
    
    async def delete_later():
        await asyncio.sleep(600)
        pending_codes.pop(code, None)
    asyncio.create_task(delete_later())
    
    await message.answer(f"✅ Код <code>{code}</code> сохранён!\nЖдёт пользователя ID: <code>{uid}</code>\nНик: <b>{nick}</b>\n<i>Активен 10 минут</i>", parse_mode="HTML")

# 3. Связь с разработчиком
@dp.callback_query(F.data == "contact_dev")
async def dev_btn(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Хорошо. Пожалуйста напишите ваше сообщение для разработчика, также вы можете приложить скриншот.")
    await state.set_state(SupportStates.waiting_for_dev_message)
    await callback.answer()

@dp.message(SupportStates.waiting_for_dev_message)
async def dev_msg(message: types.Message, state: FSMContext):
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    uid = message.from_user.id
    uname = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    
    text = f"👨‍💻 <b>Сообщение разработчику!</b>\n\nСообщение: {message.text or 'Без текста'}\nВремя: {now}\nusername: {uname}\nuser_id: <code>{uid}</code>"
    
    if message.photo:
        msg = await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=text, parse_mode="HTML")
    else:
        msg = await bot.send_message(OWNER_ID, text, parse_mode="HTML")
    
    support_requests[msg.message_id] = uid
    await message.answer("Ваше сообщение отправлено разработчику! Ожидайте ответа.")
    await state.clear()

# /chat
@dp.message(Command("chat"))
async def chat_cmd(message: types.Message, command: CommandObject):
    if message.from_user.id != OWNER_ID:
        return await message.answer("Нет доступа.")
    if not message.reply_to_message:
        return await message.answer("Ответьте на сообщение пользователя.")
    if not command.args:
        return await message.answer("/chat текст ответа")
    
    uid = support_requests.get(message.reply_to_message.message_id)
    if not uid:
        return await message.answer("Пользователь не найден.")
    
    try:
        await bot.send_message(uid, f"Ответ от поддержки!\n\n{command.args}")
        await message.answer(f"✅ Отправлено пользователю {uid}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
