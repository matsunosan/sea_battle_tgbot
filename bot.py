from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
from collections import defaultdict, deque
import time
from datetime import datetime
import os

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


# Включение логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация констант и переменных
SEA_EMOJI = '🌅'
USED_CELL_EMOJI = '✖️'
PRIZE_EMOJI = '🎁'
BOMB_EMOJI = '💣'
FIRE_EMOJI = '💥'

field = [[SEA_EMOJI for _ in range(10)] for _ in range(10)]
prizes = [['Нет приза' for _ in range(10)] for _ in range(10)]
used_cells = [[False for _ in range(10)] for _ in range(10)]
bomb_cells = [[False for _ in range(10)] for _ in range(10)]
player_shots = defaultdict(int)
admin_password = "+~hy+n828JPE"  # Установите ваш пароль
admin_chat_id = None

awaiting_shot_coordinates = False
awaiting_edit_coordinates = False
awaiting_prize_text = False
selected_cell = None

COMMAND_LIMIT = 20
COMMAND_TIME_FRAME = 10  # в секундах
BLOCK_DURATION = 300  # 5 минут в секундах


command_times = defaultdict(lambda: deque(maxlen=COMMAND_LIMIT))
blocked_users = defaultdict(lambda: 0)

# Функция для проверки блокировки пользователя
def is_user_blocked(user_id):
    current_time = time.time()
    if current_time < blocked_users[user_id]:
        return True
    times = command_times[user_id]
    if len(times) < COMMAND_LIMIT:
        times.append(current_time)
        return False
    if current_time - times[0] > COMMAND_TIME_FRAME:
        times.append(current_time)
        return False
    blocked_users[user_id] = current_time + BLOCK_DURATION
    return True

# Отправка уведомления администратору
async def notify_admin(context: ContextTypes.DEFAULT_TYPE, user, result, coordinates):
    if admin_chat_id:
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=(
                f"Айди: {user.id}\n"
                f"Юзернейм: @{user.username}\n"
                f"Имя и фамилия: {user.full_name}\n"
                f"Результат: {result}\n"
                f"Время: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"Координаты: {coordinates}"
            )
        )


# Функция для отображения текущего состояния поля с смайликами на ячейках
def show_field_with_emojis(show_prizes=False, show_bombs=False, check_mode=False) -> str:
    field_str = '⭐️ 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟\n'
    for i in range(10):
        row = f'{chr(65 + i)} '  # Буквы A-J
        for j in range(10):
            if used_cells[i][j] and prizes[i][j] != 'Нет приза':
                row += PRIZE_EMOJI
            elif used_cells[i][j] and field[i][j] == '💥':
                row += '💥'
            elif used_cells[i][j] and field[i][j] == BOMB_EMOJI:
                row += BOMB_EMOJI
            elif used_cells[i][j]:
                row += USED_CELL_EMOJI
            elif bomb_cells[i][j] and show_bombs:
                row += BOMB_EMOJI
            elif show_prizes and check_mode and prizes[i][j] != 'Нет приза':
                row += PRIZE_EMOJI
            elif show_bombs and check_mode and bomb_cells[i][j]:
                row += BOMB_EMOJI
            else:
                row += SEA_EMOJI
            row += ' '
        field_str += row + '\n'
    return field_str


# Основные команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_user_blocked(user.id):
        if update.message:
            await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        elif update.callback_query:
            await update.callback_query.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    if user.id not in player_shots:
        player_shots[user.id] = 0  # Начальный баланс выстрелов 0
    menu_buttons = [
        [InlineKeyboardButton("Правила", callback_data='rules'), InlineKeyboardButton("Chat DHL", url='https://t.me/+2aMfTMIUJkg4Nzc0')],
        [InlineKeyboardButton("Модератор", url='https://t.me/DHL_Battle'), InlineKeyboardButton("Магазин", url='https://t.me/+N3IM4ooRBV1jYjVk')],
        [InlineKeyboardButton("Морской Бой", callback_data='battlefield')]
    ]
    if update.message:
        await update.message.reply_text(f'Добро пожаловать в игру Морской бой, {user.first_name}!',
                                        reply_markup=InlineKeyboardMarkup(menu_buttons))
    elif update.callback_query:
        await update.callback_query.message.reply_text(f'Добро пожаловать в игру Морской бой, {user.first_name}!',
                                                      reply_markup=InlineKeyboardMarkup(menu_buttons))

async def battlefield(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    balance_info = f"Игрок: {user.first_name}\nБаланс выстрелов: {player_shots.get(user.id, 0)}"
    battlefield_buttons = [
        [InlineKeyboardButton("Совершить выстрел", callback_data='make_shot')],
        [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
    ]
    if update.message:
        await update.message.reply_text(f'{balance_info}\n\nТекущая карта:\n{show_field_with_emojis()}',
                                        reply_markup=InlineKeyboardMarkup(battlefield_buttons))
    elif update.callback_query:
        await update.callback_query.message.edit_text(f'{balance_info}\n\nТекущая карта:\n{show_field_with_emojis()}',
                                                      reply_markup=InlineKeyboardMarkup(battlefield_buttons))

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    rules_text = (
        "📝 Правила игры в Sea Battle:\n\n"
        "При покупке от 100зл и выше, теперь можно сыграть в ежедневную рулетку.\n\n"
        "На карте спрятаны призы, ваша задача найти их и не попасть на мины.\n\n"
        "Ввод координат производится латинской буквой и цифрой без пробела, например: F5.\n\n"
        "Для пополнения выстрелов свяжитесь с оператором рулетки.\n"
        "Оператор должен проверить оплату!\n\n"
        "🔁 Призы и их расстановка будут обновляться раз в неделю!\n\n"
        "Напомним, каждый новый чек от 100зл в заказе это – 1 ход 🎟️\n\n"
        "Желаем удачи каждому! 🍀"
    )
    if update.message:
        await update.message.reply_text(rules_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))
    elif update.callback_query:
        await update.callback_query.message.edit_text(rules_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    global admin_chat_id
    if admin_chat_id is None:
        await update.message.reply_text('Введите пароль для доступа к админ панели.')
        return

    if user.id == admin_chat_id:
        admin_menu_buttons = [
            [InlineKeyboardButton("Добавить выстрелы", callback_data='add_shots')],
            [InlineKeyboardButton("Редактировать карту", callback_data='edit_map')],
            [InlineKeyboardButton("Очистить карту", callback_data='clear_map')],
            [InlineKeyboardButton("Проверить состояние карты", callback_data='check_map')],
            [InlineKeyboardButton("Главное меню", callback_data='main_menu')]
        ]
        if update.message:
            await update.message.reply_text('Добро пожаловать в админ панель!',
                                            reply_markup=InlineKeyboardMarkup(admin_menu_buttons))
        elif update.callback_query:
            await update.callback_query.message.edit_text('Добро пожаловать в админ панель!',
                                                          reply_markup=InlineKeyboardMarkup(admin_menu_buttons))
    else:
        await update.message.reply_text('У вас нет доступа к админ панели.')

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    text = update.message.text.split()
    global admin_chat_id
    if len(text) == 2 and text[1] == admin_password:
        admin_chat_id = user.id
        await update.message.reply_text('Вы получили доступ к админ панели.',
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))
    else:
        await update.message.reply_text('Неверный пароль.')

async def add_shots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if user.id == admin_chat_id:
        await query.message.edit_text("Введите ID игрока и количество выстрелов через пробел (например, '12345 5').",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def add_shots_by_id(update: Update, context) -> None:
    user = update.message.from_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    if user.id != admin_chat_id:
        return
    try:
        player_id, shots = map(int, update.message.text.split())
        player_shots[player_id] += shots
        await update.message.reply_text(f"Игроку {player_id} добавлено {shots} выстрелов. Текущий баланс: {player_shots[player_id]}.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))
    except ValueError:
        await update.message.reply_text("Неверный формат. Введите ID игрока и количество выстрелов через пробел (например, '12345 5').",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def add_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell, awaiting_prize_text
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        awaiting_prize_text = True
        await update.callback_query.message.edit_text(f'Введите текст приза для ячейки ({selected_cell}).',
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def save_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell, awaiting_prize_text
    user = update.message.from_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    if awaiting_prize_text:
        text = update.message.text
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        prizes[row][col] = text
        awaiting_prize_text = False
        await update.message.reply_text(f'Приз "{text}" добавлен на ячейку {selected_cell}.',
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def remove_prize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        prizes[row][col] = 'Нет приза'
        await update.callback_query.message.edit_text(f'Приз удален с ячейки ({selected_cell}).',
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def mark_used(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        used_cells[row][col] = True
        await update.callback_query.message.edit_text(f'Ячейка ({selected_cell}) отмечена как использованная.',
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def mark_free(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        used_cells[row][col] = False
        await update.callback_query.message.edit_text(f'Ячейка ({selected_cell}) отмечена как свободная.',
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def clear_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if user.id == admin_chat_id:
        global field, prizes, used_cells, bomb_cells
        field = [[SEA_EMOJI for _ in range(10)] for _ in range(10)]
        prizes = [['Нет приза' for _ in range(10)] for _ in range(10)]
        used_cells = [[False for _ in range(10)] for _ in range(10)]
        bomb_cells = [[False for _ in range(10)] for _ in range(10)]
        await query.message.edit_text('Карта очищена.',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Доступные команды:\n"
        "/start - Начать игру\n"
        "/battlefield - Показать текущее состояние карты\n"
        "/rules - Показать правила игры\n"
    )
    await update.message.reply_text(help_text)
async def check_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if user.id == admin_chat_id:
        await query.message.edit_text(f'Текущее состояние карты:\n{show_field_with_emojis(show_prizes=True, show_bombs=True, check_mode=True)}',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def add_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        bomb_cells[row][col] = True
        await update.callback_query.message.edit_text(f'Бомба добавлена на ячейку ({selected_cell}).',
                                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

async def handle_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global awaiting_shot_coordinates, awaiting_edit_coordinates, selected_cell
    user = update.message.from_user
    if is_user_blocked(user.id):
        await update.message.reply_text('Вы заблокированы на 5 минут за слишком частые команды.')
        return
    coordinates = update.message.text.strip().upper()

    if len(coordinates) < 2 or len(coordinates) > 3 or not coordinates[0].isalpha() or not coordinates[1:].isdigit():
        await update.message.reply_text('Неверный формат координат. Введите координаты (например, A1):')
        if awaiting_shot_coordinates:
            awaiting_shot_coordinates = True
        elif awaiting_edit_coordinates:
            awaiting_edit_coordinates = True
        return

    row = ord(coordinates[0]) - ord('A')
    col = int(coordinates[1:]) - 1

    if row < 0 or row >= 10 or col < 0 or col >= 10:
        await update.message.reply_text('Координаты вне диапазона. Введите координаты (например, A1):')
        if awaiting_shot_coordinates:
            awaiting_shot_coordinates = True
        elif awaiting_edit_coordinates:
            awaiting_edit_coordinates = True
        return

    selected_cell = coordinates

    if awaiting_shot_coordinates:
        awaiting_shot_coordinates = False
        if player_shots[user.id] > 0:
            if used_cells[row][col]:
                await update.message.reply_text('Эта ячейка уже использована. Введите другие координаты:',
                                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))
                awaiting_shot_coordinates = True
                return

            player_shots[user.id] -= 1
            used_cells[row][col] = True
            image_path = ''
            if bomb_cells[row][col]:
                for i in range(max(0, row - 1), min(10, row + 2)):
                    for j in range(max(0, col - 1), min(10, col + 2)):
                        used_cells[i][j] = True
                        if i == row and j == col:
                            field[i][j] = BOMB_EMOJI
                        else:
                            field[i][j] = '💥'
                result_message = f'Вы попали в бомбу на ячейке ({coordinates}). Все ячейки вокруг также взорваны!'
                image_path = os.path.join('C:\\Users\\glory hole\\Documents\\seabattlebot\\image', 'bomb_image.jpg')
                await notify_admin(context, user, 'Взорвал бомбу', coordinates)
            elif prizes[row][col] != 'Нет приза':
                field[row][col] = PRIZE_EMOJI
                result_message = f'Вы выстрелили в ячейку ({coordinates}).\nПоздравляем! Вы нашли приз: {prizes[row][col]}'
                image_path = os.path.join('C:\\Users\\glory hole\\Documents\\seabattlebot\\image', 'prize_image.jpg')
                await notify_admin(context, user, f'Выиграл приз: {prizes[row][col]}', coordinates)
            else:
                result_message = f'Вы выстрелили в ячейку ({coordinates}).\nМимо.'
                image_path = os.path.join('C:\\Users\\glory hole\\Documents\\seabattlebot\\image', 'miss_image.jpg')
                await notify_admin(context, user, 'Мимо', coordinates)
            
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_path, caption=f'{result_message}',
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))
        else:
            await update.message.reply_text('У вас нет выстрелов.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))

    if awaiting_edit_coordinates:
        awaiting_edit_coordinates = False
        await update.message.reply_text(f'Выбрана ячейка ({coordinates}). Что вы хотите сделать?',
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("Добавить приз", callback_data='add_prize')],
                                            [InlineKeyboardButton("Добавить бомбу", callback_data='add_bomb')],
                                            [InlineKeyboardButton("Очистить ячейку", callback_data='clear_cell')],
                                            [InlineKeyboardButton("Отметить как использованную", callback_data='mark_used')],
                                            [InlineKeyboardButton("Отметить как свободную", callback_data='mark_free')],
                                            [InlineKeyboardButton("Админ панель", callback_data='admin_panel')]
                                        ]))




async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    global awaiting_shot_coordinates, awaiting_edit_coordinates, selected_cell
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return

    if query.data == 'make_shot':
        if player_shots[user.id] > 0:
            awaiting_shot_coordinates = True
            await query.message.edit_text('Введите координаты выстрела (например, A1):',
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data='main_menu')]]))
        else:
            await query.answer("У вас нет выстрелов!", show_alert=True)

    elif query.data == 'edit_map':
        awaiting_edit_coordinates = True
        await query.message.edit_text('Введите координаты ячейки для редактирования (например, A1):',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

    elif query.data == 'rules':
        await rules(update, context)

    elif query.data == 'battlefield':
        await battlefield(update, context)

    elif query.data == 'main_menu':
        await start(update, context)

    elif query.data == 'add_prize':
        await add_prize(update, context)

    elif query.data == 'add_bomb':
        await add_bomb(update, context)

    elif query.data == 'clear_cell':
        await clear_cell(update, context)

    elif query.data == 'mark_used':
        await mark_used(update, context)

    elif query.data == 'mark_free':
        await mark_free(update, context)

    elif query.data == 'admin_panel':
        await admin_panel(update, context)

    elif query.data == 'add_shots':
        await add_shots(update, context)

    elif query.data == 'check_map':
        await check_map(update, context)

    elif query.data == 'clear_map':
        await clear_map(update, context)

    await query.answer()


async def clear_cell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global selected_cell
    query = update.callback_query
    user = query.from_user
    if is_user_blocked(user.id):
        await query.answer('Вы заблокированы на 5 минут за слишком частые команды.', show_alert=True)
        return
    if selected_cell:
        row = ord(selected_cell[0]) - ord('A')
        col = int(selected_cell[1:]) - 1
        prizes[row][col] = 'Нет приза'
        bomb_cells[row][col] = False
        used_cells[row][col] = False
        selected_cell = None
        await query.message.edit_text(f'Ячейка ({selected_cell}) очищена.',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Админ панель", callback_data='admin_panel')]]))

# Запуск бота
if __name__ == '__main__':
    application = Application.builder().token("TELEGRAM_BOT_TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("battlefield", battlefield))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("admin_panel", admin_panel))
    application.add_handler(CommandHandler("set_admin", set_admin))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^[A-Ja-j][1-9]0?$'), handle_coordinates))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^[0-9]+ [0-9]+$'), add_shots_by_id))
    application.add_handler(MessageHandler(filters.TEXT, save_prize))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()
