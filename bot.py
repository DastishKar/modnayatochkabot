import sqlite3
from datetime import datetime, timedelta
import random
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

# Клавиатура
main_keyboard = [
    ["Голосование", "Напоминалка"], 
    ["Гадание на день", "Команды"]
]

# Состояния для диалогов
VOTE_QUESTION, VOTE_OPTIONS, REMINDER_TIME, REMINDER_MESSAGE = range(4)

# Подключение к базе данных
conn = sqlite3.connect("telegram_bot.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если они не существуют
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        joined_at TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        options TEXT,
        created_at TEXT,
        created_by INTEGER,
        chat_id INTEGER
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS poll_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER,
        user_id INTEGER,
        option_index INTEGER,
        UNIQUE(poll_id, user_id)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        reminder_time TEXT,
        message TEXT,
        created_at TEXT
    )
""")

conn.commit()

# Предсказания для гадания
fortune_messages = [
    "Сегодня ты будешь чувствовать, что все идет как надо, но не расслабляйся.",
    "Ты окажешься в ситуации, которая заставит тебя усомниться в себе, но это лишь временно.",
    "Тебя ждет неожиданный поворот в делах, но ты справишься с этим.",
    "Сегодня звезды говорят, что стоит сделать перерыв и подумать о своих целях.",
    "Ты встретишь кого-то, кто изменит твои взгляды на жизнь, но не торопись с выводами.",
    "Сегодня твой день для того, чтобы преодолеть страхи и двигаться вперед.",
    "Ты поймешь, что успех зависит не только от действий, но и от настроя.",
    "Сегодня твоя уверенность будет на высоте, так что воспользуйся этим.",
    "Ты столкнешься с тем, что тебе нужно будет принять важное решение, но ты сделаешь правильный выбор.",
    "Ты получишь возможность сделать важный шаг, но важно действовать решительно.",
    "Сегодня твоя решимость поможет тебе преодолеть любые преграды.",
    "Ты обнаружишь, что то, что казалось невозможным, на самом деле вполне выполнимо.",
    "Звезды советуют тебе сделать шаг назад и пересмотреть свои цели.",
    "Ты увидишь результат своих усилий, но тебе нужно будет проявить терпение.",
    "Сегодня ты можешь столкнуться с небольшими трудностями, но они будут полезными для твоего роста.",
    "Ты почувствуешь, что наступает время перемен, но будь готов к тому, что они могут быть неожиданными.",
    "Сегодня ты будешь немного сбит с толку, но все встанет на свои места.",
    "Ты найдешь решение сложной задачи, если будешь немного более терпеливым.",
    "Сегодня ты окажешься в ситуации, где нужно будет довериться интуиции.",
    "Ты обнаружишь, что многое из того, что ты ищешь, уже рядом.",
    "Сегодня твоя энергия будет на высоком уровне, и это поможет тебе сделать важный шаг.",
    "Ты почувствуешь лёгкое беспокойство, но это будет сигналом к действию.",
    "Сегодня твоя решимость поможет тебе достичь цели, которую ты поставил давно.",
    "Ты столкнешься с вопросом, который ты долго откладывал, но сегодня ты решишь его раз и навсегда.",
    "Звезды советуют быть осторожным в финансовых вопросах — сегодня ты можешь получить неожиданные новости.",
    "Сегодня ты сможешь завершить давно начатое дело, если приложишь усилия.",
    "Ты найдешь решение проблемы, если подойдешь к ней с другой стороны.",
    "Сегодня тебе предстоит встреча с кем-то, кто вдохновит тебя на важное изменение.",
    "Ты почувствуешь, что наступает момент, когда нужно отпустить старое и двигаться к новому.",
    "Сегодня ты будешь на вершине, но важно помнить, что подъем — это не конец пути.",
    "Тебя ждёт неожиданный успех в том, что ты не ожидал начать.",
    "Сегодня твоя интуиция поможет тебе найти ответ на вопрос, который тебя давно мучил.",
    "Ты будешь окружён людьми, которые помогут тебе раскрыть твой потенциал.",
    "Звезды говорят, что твой путь не всегда будет прямым, но ты сможешь преодолеть все повороты.",
    "Ты встретишь кого-то, кто откроет тебе новые горизонты и идеи.",
    "Сегодня твой день для того, чтобы проявить терпение и настойчивость.",
    "Ты будешь чувствовать себя уверенно, но не забывай, что успех приходит с упорством.",
    "Сегодня ты откроешь для себя что-то новое, что кардинально изменит твою жизнь.",
    "Ты почувствуешь, что пришло время действовать, и не упустишь шанс.",
    "Сегодня тебе предстоит сделать выбор, который повлияет на твое будущее, но ты знаешь, что делать.",
    "Ты окажешься в нужное время в нужном месте, так что не переживай, если всё идет не по плану.",
    "Звезды говорят, что твоя решимость приведет к успеху, но нужно проявить гибкость.",
    "Сегодня ты увидишь, как твои усилия начинают приносить плоды.",
    "Ты столкнешься с вопросом, который давно откладывал, но сегодня будет время для его решения.",
    "Сегодня твоя энергия и энтузиазм помогут тебе завершить проект, к которому ты давно стремился.",
    "Ты почувствуешь, что всё становится на свои места, если будешь действовать уверенно.",
    "Тебя ждёт встреча, которая перевернёт твои взгляды на вещи.",
    "Сегодня ты получишь новости, которые заставят тебя пересмотреть свои цели.",
    "Ты столкнёшься с неожиданным вызовом, но сможешь справиться с ним благодаря своему опыту.",
    "Сегодня твои мысли будут ясными, и ты сможешь принять важное решение.",
    "Ты почувствуешь уверенность в своих силах, но не забывай, что важно не останавливаться на достигнутом.",
    "Сегодня твоя удача будет находиться в решениях, которые ты принимаешь.",
    "Ты встретишь человека, который станет для тебя источником вдохновения.",
    "Звезды говорят, что тебе предстоит сделать важный шаг вперед, но не торопись.",
    "Сегодня твои усилия принесут долгожданный результат, но нужно будет немного подождать.",
    "Ты столкнёшься с ситуацией, которая потребует от тебя гибкости, но ты справишься.",
    "Сегодня твоя интуиция подскажет тебе, как поступить в сложной ситуации.",
    "Ты будешь чувствовать, что твои усилия начинают приносить реальные результаты.",
    "Сегодня ты сможешь завершить проект, который давно откладывал.",
    "Ты почувствуешь, что наступает момент для перемен, и будешь готов их принять.",
    "Звезды говорят, что тебе предстоит сделать шаг, который приведет к новым возможностям.",
    "Сегодня ты сможешь найти решение задачи, которая давно тебя беспокоила.",
    "Ты будешь окружён возможностями, но важно выбрать ту, которая приведет к успеху.",
    "Сегодня тебе предстоит сделать выбор, но ты уже знаешь, что это правильное решение.",
    "Ты почувствуешь, что всё, что тебе нужно, уже есть рядом, нужно лишь сделать шаг вперед.",
    "Сегодня твои усилия приведут к успеху, если ты будешь верить в себя.",
    "Ты встретишь кого-то, кто поможет тебе на пути к твоим целям.",
    "Звезды говорят, что тебе предстоит найти решение проблемы, которая казалась нерешаемой.",
    "Сегодня твоя интуиция поможет тебе принять правильное решение в важном вопросе.",
    "Ты почувствуешь, что твои действия наконец начинают приносить результаты.",
    "Сегодня ты столкнешься с задачей, которую раньше считал невозможной, но теперь сможешь её решить.",
    "Ты обнаружишь, что ответы на вопросы, которые тебя беспокоили, уже давно у тебя перед глазами.",
    "Сегодня твоя настойчивость приведет к успеху в том, что ты давно хотел достичь.",
    "Ты почувствуешь, что все вокруг начинает складываться в твою пользу, если будешь действовать решительно.",
    "Звезды говорят, что ты получишь шанс сделать шаг вперед в своем профессиональном пути.",
    "Сегодня твоя решимость поможет тебе преодолеть любые препятствия на пути к цели.",
    "Ты будешь окружён людьми, которые помогут тебе сделать важное открытие.",
    "Сегодня ты почувствуешь уверенность, которая поможет тебе сделать важный шаг.",
    "Ты получишь шанс изменить свою жизнь, но важно принять его вовремя.",
    "Ты столкнешься с ситуацией, которая потребует от тебя храбрости, но ты справишься.",
    "Сегодня твоя уверенность поможет тебе справиться с любыми трудностями.",
    "Ты будешь чувствовать, что на твоем пути есть помощь, даже если она будет неочевидной.",
    "Сегодня ты сможешь завершить важный проект и почувствовать удовлетворение от достигнутого.",
    "Ты почувствуешь, что твоя жизнь начинает изменяться в лучшую сторону.",
    "Звезды говорят, что твоя упорная работа начнёт приносить долгожданные плоды.",
    "Сегодня ты сможешь завершить старую задачу и сосредоточиться на новых проектах.",
    "Ты столкнешься с проблемой, но это только проверка твоих сил, и ты справишься.",
    "Сегодня твои усилия будут вознаграждены, но важно сохранять терпение.",
    "Ты почувствуешь, что твои действия начинают приносить результаты, и это тебя вдохновит."
]

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.message.chat.type
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Добавляем пользователя в базу, если его там нет
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user.id, user.username, user.first_name, now))
    conn.commit()
    
    if chat_type in ["group", "supergroup"]:
        await update.message.reply_text(f"Привет, {user.first_name}! 👋 Я теперь в вашей группе!")
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋 Доступные функции:",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        )
# Добавление пользователя в базу данных
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    joined_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Проверяем, существует ли пользователь уже в базе
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        # Добавляем нового пользователя
        cursor.execute(
            "INSERT INTO users (user_id, first_name, joined_at) VALUES (?, ?, ?)",
            (user_id, first_name, joined_at)
        )
        conn.commit()
        await update.message.reply_text(f"Привет, {first_name}! Ты добавлен в список друзей.")
    else:
        await update.message.reply_text(f"{first_name}, ты уже в списке друзей!")


# Показать список друзей
async def show_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем информацию о всех пользователях, включая текущего
    cursor.execute("SELECT first_name, joined_at FROM users")
    rows = cursor.fetchall()
    
    if not rows:
        await update.message.reply_text("В списке друзей пока никого нет 😢")
    else:
        message = "👥 Список друзей:\n\n"
        for row in rows:
            first_name = row[0]
            joined_at = row[1]
            
            message += f"• {first_name} (присоединился: {joined_at})\n"
            
        await update.message.reply_text(message)

# Функция гадания на день
async def daily_fortune(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fortune = random.choice(fortune_messages)
    await update.message.reply_text(f"🔮 Гадание на сегодня:\n\n{fortune}")

# Начало процесса голосования
async def start_voting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Создание голосования\n\nВведите вопрос (например, 'Куда пойдём?' или 'Что смотрим?'):"
    )
    return VOTE_QUESTION

# Получение вопроса для голосования
async def get_vote_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vote_question'] = update.message.text
    await update.message.reply_text(
        "Теперь введите варианты ответов, разделяя их запятыми.\nНапример: Кино, Боулинг, Кафе"
    )
    return VOTE_OPTIONS

# Создание голосования
async def create_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options_text = update.message.text
    options = [opt.strip() for opt in options_text.split(',')]
    
    if len(options) < 2:
        await update.message.reply_text("Нужно минимум 2 варианта. Попробуйте еще раз:")
        return VOTE_OPTIONS
    
    question = context.user_data['vote_question']
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохраняем голосование в базу данных
    cursor.execute("""
        INSERT INTO polls (question, options, created_at, created_by, chat_id)
        VALUES (?, ?, ?, ?, ?)
    """, (question, options_text, now, user_id, chat_id))
    conn.commit()
    poll_id = cursor.lastrowid
    
    # Создаем клавиатуру с вариантами
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"vote_{poll_id}_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 ГОЛОСОВАНИЕ:\n\n{question}",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# Обработка голосов
async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    poll_id = int(data_parts[1])
    option_index = int(data_parts[2])
    user_id = query.from_user.id
    
    # Сохраняем или обновляем голос
    try:
        cursor.execute("""
            INSERT INTO poll_votes (poll_id, user_id, option_index)
            VALUES (?, ?, ?)
        """, (poll_id, user_id, option_index))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("""
            UPDATE poll_votes
            SET option_index = ?
            WHERE poll_id = ? AND user_id = ?
        """, (option_index, poll_id, user_id))
        conn.commit()
    
    # Получаем данные о голосовании
    cursor.execute("SELECT question, options FROM polls WHERE id = ?", (poll_id,))
    poll_data = cursor.fetchone()
    question = poll_data[0]
    options = [opt.strip() for opt in poll_data[1].split(',')]
    
    # Считаем голоса
    cursor.execute("""
        SELECT option_index, COUNT(*) as votes
        FROM poll_votes
        WHERE poll_id = ?
        GROUP BY option_index
    """, (poll_id,))
    vote_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Обновляем сообщение с текущими результатами
    result_text = f"📊 ГОЛОСОВАНИЕ:\n\n{question}\n\nРезультаты:\n"
    for i, option in enumerate(options):
        votes = vote_counts.get(i, 0)
        result_text += f"\n{option}: {votes} голос(ов)"
    
    # Пересоздаем клавиатуру
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"vote_{poll_id}_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=result_text,
        reply_markup=reply_markup
    )

# Начало процесса создания напоминания
async def start_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 Создание напоминания\n\nУкажите время напоминания в формате ЧЧ:ММ или через сколько минут (например, '30м'):"
    )
    return REMINDER_TIME

# Получение времени для напоминания
async def get_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_text = update.message.text.strip()
    now = datetime.now()
    
    try:
        if 'м' in time_text:
            # Формат в минутах
            minutes = int(time_text.replace('м', ''))
            reminder_time = now + timedelta(minutes=minutes)
        else:
            # Формат ЧЧ:ММ
            hour, minute = map(int, time_text.split(':'))
            reminder_time = now.replace(hour=hour, minute=minute)
            
            # Если время уже прошло, устанавливаем на завтра
            if reminder_time < now:
                reminder_time += timedelta(days=1)
    except:
        await update.message.reply_text("Некорректный формат времени. Попробуйте снова (например, 18:00 или 30м):")
        return REMINDER_TIME
    
    context.user_data['reminder_time'] = reminder_time
    
    await update.message.reply_text("Теперь введите текст напоминания:")
    return REMINDER_MESSAGE

# Создание напоминания
async def create_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_message = update.message.text
    reminder_time = context.user_data['reminder_time']
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохраняем напоминание в базу данных
    cursor.execute("""
        INSERT INTO reminders (chat_id, user_id, reminder_time, message, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (chat_id, user_id, reminder_time.strftime("%Y-%m-%d %H:%M:%S"), reminder_message, now))
    conn.commit()
    
    # Планируем напоминание
    time_diff = (reminder_time - datetime.now()).total_seconds()
    
    if time_diff > 0:
        context.job_queue.run_once(
            send_reminder,
            time_diff,
            chat_id=chat_id,
            data={'message': reminder_message, 'reminder_id': cursor.lastrowid}
        )
    
    await update.message.reply_text(
        f"✅ Напоминание установлено на {reminder_time.strftime('%H:%M')}:\n{reminder_message}"
    )
    
    return ConversationHandler.END

# Отправка напоминания
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    reminder_data = job.data
    reminder_message = reminder_data['message']
    reminder_id = reminder_data['reminder_id']
    
    await context.bot.send_message(
        job.chat_id,
        f"🔔 НАПОМИНАНИЕ:\n\n{reminder_message}"
    )
    
    # Удаляем из базы данных
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()

# Загрузка активных напоминаний при запуске
async def load_reminders(application):
    now = datetime.now()
    
    cursor.execute("SELECT id, chat_id, reminder_time, message FROM reminders")
    reminders = cursor.fetchall()
    
    for reminder in reminders:
        reminder_id, chat_id, reminder_time_str, message = reminder
        reminder_time = datetime.strptime(reminder_time_str, "%Y-%m-%d %H:%M:%S")
        
        # Планируем только будущие напоминания
        time_diff = (reminder_time - now).total_seconds()
        if time_diff > 0:
            application.job_queue.run_once(
                send_reminder,
                time_diff,
                chat_id=chat_id,
                data={'message': message, 'reminder_id': reminder_id}
            )

# Показать список команд
async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_text = """
📋 *Список доступных команд:*

*Основные команды:*
/start - Запустить бота
/menu - Показать главное меню
/commands - Показать список команд

*Функции бота:*
/vote - Создать новое голосование
/reminder - Установить напоминание
/fortune - Получить гадание на день
/friend - Показать список друзей

*Кнопки на клавиатуре:*
• Голосование - Создать опрос
• Напоминалка - Установить напоминание
• Гадание на день - Получить предсказание
• Команды - Показать этот список
    """
    
    await update.message.reply_text(
        commands_text,
        parse_mode="Markdown"
    )

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if "голосование" in text:
        return await start_voting(update, context)
    elif "напоминалка" in text:
        return await start_reminder(update, context)
    elif "гадание" in text:
        await daily_fortune(update, context)
    elif "друзья" in text:
        await show_friends(update, context)
    elif "команды" in text:
        await show_commands(update, context)

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END

# Установка команд бота в меню Telegram
async def setup_commands(application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("menu", "Показать главное меню"),
        BotCommand("vote", "Создать голосование"),
        BotCommand("reminder", "Установить напоминание"),
        BotCommand("fortune", "Гадание на день"),
        BotCommand("friend", "Список друзей"),
        BotCommand("commands", "Список команд")
    ]
    
    await application.bot.set_my_commands(commands)

async def post_init(application: Application):
    # Загружаем напоминания после запуска бота
    await load_reminders(application)
    # Устанавливаем команды в меню
    await setup_commands(application)

def main():
    # Настройка приложения с очередью задач
    app = Application.builder().token("7599952186:AAG3e72f5Glf5dN15YQcubtx0dkXJev3kmM").post_init(post_init).build()
    
    # Добавляем обработчики диалогов
    vote_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("vote", start_voting),
                     MessageHandler(filters.Regex(r"(?i)голосование"), start_voting)],
        states={
            VOTE_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vote_question)],
            VOTE_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_vote)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    reminder_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reminder", start_reminder),
                     MessageHandler(filters.Regex(r"(?i)напоминалка"), start_reminder)],
        states={
            REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reminder_time)],
            REMINDER_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_reminder)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("friend", show_friends))
    app.add_handler(CommandHandler("fortune", daily_fortune))
    app.add_handler(CommandHandler("commands", show_commands))
    # В основной части программы добавьте:
    app.add_handler(CommandHandler("join", add_user))
    app.add_handler(vote_conv_handler)
    app.add_handler(reminder_conv_handler)
    app.add_handler(CallbackQueryHandler(handle_vote, pattern="^vote_"))
    
    # Добавляем обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()