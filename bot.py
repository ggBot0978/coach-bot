import logging
import random
import json
import os
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ТОКЕН ---
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- СОСТОЯНИЯ ---
MAIN_MENU, EVENING_REPORT, SET_GOAL, CHECK_GOAL = range(4)

# --- ФАЙЛ ДЛЯ ХРАНЕНИЯ ДАННЫХ ---
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: str):
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "goals": [],
            "streak": 0,
            "last_check": None,
            "mood_history": [],
            "points": 0,
        }
        save_data(data)
    return data[user_id]

def update_user(user_id: str, user_data: dict):
    data = load_data()
    data[user_id] = user_data
    save_data(data)

# --- ШУТКИ И МОТИВАЦИЯ ---
MORNING_TASKS = [
    ("🏃 Сделай 10 прыжков на месте", "Потому что диван сам тебя не прокачает!"),
    ("💧 Выпей стакан воды прямо сейчас", "Ты на 60% состоишь из воды. Освежи себя!"),
    ("📖 Прочитай 5 страниц любой книги", "Даже инструкция к холодильнику считается. Почти."),
    ("🧘 Сделай 2 минуты глубокого дыхания", "Вдох... выдох... вдох... ты ещё здесь?"),
    ("✍️ Запиши 3 вещи, за которые ты благодарен", "Интернет и кофе точно в списке, не ври!"),
    ("🚶 Пройди 1000 шагов пешком", "Это всего лишь 4 круга вокруг дивана... или выйди на улицу!"),
    ("🎯 Напиши одну задачу, которую сделаешь сегодня", "Одну. Справишься? Верю в тебя!"),
    ("🌞 Посмотри в окно 2 минуты", "Солнце есть? Отлично. Нет? Ну и ладно, ты всё равно молодец."),
    ("📵 Не трогай телефон 15 минут", "Да, прямо сейчас... хотя подожди, прочитай это сначала."),
    ("🍎 Съешь что-нибудь полезное на завтрак", "Чипсы не считаются. Чипсы никогда не считаются."),
]

MOTIVATIONAL_JOKES = [
    "Помни: даже черепаха добралась до финиша. Правда, заяц проспал, но это детали! 🐢",
    "Ты можешь всё! Ну, почти всё. Летать без самолёта пока не пробуй. ✈️",
    "Каждый день — это новый шанс. Вчерашний провал? Забудь. Ну или запомни, но смейся! 😄",
    "Великие дела начинаются с маленьких шагов. А маленькие шаги — с того, чтобы встать с дивана. 🛋️",
    "Ты лучше, чем думаешь! Хотя думаешь ты иногда странно, но это добавляет шарм. 🌟",
    "Прогресс — это прогресс, даже если он маленький. Улитки тоже куда-то добираются! 🐌",
    "Сегодня хороший день, чтобы стать немного лучше. Или хотя бы поменять носки. 🧦",
    "Твой потенциал безграничен! Как Wi-Fi в хорошем кафе — иногда лагает, но в целом работает. 📶",
]

EVENING_PHRASES = [
    "Ну и как прошёл день, чемпион? 🏆",
    "Признавайся — что натворил сегодня полезного? 😏",
    "Вечер добрый! Диван уже ждёт, но сначала отчитайся! 🛋️",
    "Итоги дня! Хвались или исповедуйся — оба варианта принимаю. 😄",
]

GOOD_REPORT_REACTIONS = [
    "Красавчик! Так держать! 💪 +10 очков в копилку!",
    "Вот это я понимаю! Гордишься? Я горжусь! 🎉 +10 очков!",
    "Продуктивность зашкаливает! Ты точно не робот? +10 очков! 🤖",
    "Огонь! 🔥 Продолжай в том же духе! +10 очков!",
]

BAD_REPORT_REACTIONS = [
    "Ничего, завтра возьмёшь реванш! Диван проиграет! 💪",
    "Бывает! Даже супергерои иногда отдыхают. Ты в хорошей компании! 🦸",
    "Отдых — это тоже продуктивность. Я в это верю. Почти. 😅",
    "Окей, сегодня не задалось. Но ты всё равно крут за то, что открыл бота! 🙌",
]

# --- КЛАВИАТУРЫ ---
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("☀️ Задача дня"), KeyboardButton("🎯 Мои цели")],
        [KeyboardButton("😄 Анекдот"), KeyboardButton("📊 Моя статистика")],
        [KeyboardButton("💬 Мотивация"), KeyboardButton("🌙 Итоги дня")],
    ], resize_keyboard=True)

def mood_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("😎 Огонь, всё сделал!"), KeyboardButton("😐 Средненько")],
        [KeyboardButton("😴 Честно — ничего не сделал")],
    ], resize_keyboard=True)

def goal_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("➕ Добавить цель"), KeyboardButton("✅ Выполнить цель")],
        [KeyboardButton("🔙 Назад")],
    ], resize_keyboard=True)

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(update.effective_user.id)
    get_user(uid)  # инициализируем

    text = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я твой личный коуч с юмором — *КоучБот 3000*! 🤖✨\n\n"
        "Что умею:\n"
        "☀️ *Задача дня* — каждый день новое испытание\n"
        "🎯 *Цели* — ставь и выполняй\n"
        "📊 *Статистика* — следи за прогрессом\n"
        "😄 *Анекдоты* — потому что без смеха никуда\n"
        "🌙 *Итоги дня* — вечерний чек-ин\n\n"
        "Готов стать немного лучше? Или хотя бы посмеяться? Погнали! 🚀"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def daily_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task, joke = random.choice(MORNING_TASKS)
    uid = str(update.effective_user.id)
    user = get_user(uid)

    text = (
        f"*Задача дня:*\n\n"
        f"{task}\n\n"
        f"_{joke}_\n\n"
        f"🔥 Стрик: {user['streak']} дней подряд\n"
        f"⭐ Очков: {user['points']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "Почему программисты не любят природу?\nПотому что там слишком много багов! 🐛",
        "— Как называется пустой холодильник?\n— Холодильник без мотивации. Будь не как он! 🧊",
        "Учёные доказали, что лень — двигатель прогресса.\nЯ лично проверил это, лёжа на диване. 🛋️",
        "— Ты занимался спортом?\n— Да, я поднял пульт и переключил канал.\n— Это кардио! 📺",
        "Говорят, утро вечера мудренее.\nЗначит ли это, что я умнею пока сплю? Спрашиваю для друга. 😴",
        "Мотивация как зарядка телефона — кончается в самый неподходящий момент. 🔋",
        "— Как похудеть?\n— Не доедать.\n— А если не начинать есть?\n— Это уже буддизм. 🧘",
        "Позитивное мышление — это когда видишь стакан наполовину полным.\nНегативное — когда видишь, что кто-то уже отпил. 🥤",
        "Хочешь похудеть? Вставай из-за стола с лёгким чувством голода.\nИ с тяжёлым чувством несправедливости. 🍕",
        "— Сколько раз нужно упасть, чтобы научиться ходить?\nСтолько же, сколько раз ты упадёшь, прежде чем встанешь! 💪",
    ]
    await update.message.reply_text(random.choice(jokes), reply_markup=main_keyboard())
    return MAIN_MENU

async def motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = random.choice(MOTIVATIONAL_JOKES)
    await update.message.reply_text(text, reply_markup=main_keyboard())
    return MAIN_MENU

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = get_user(uid)

    goals_count = len(user["goals"])
    completed = sum(1 for g in user["goals"] if g.get("done"))

    # Звание по очкам
    points = user["points"]
    if points < 50:
        rank = "🥉 Новичок (диван ещё сопротивляется)"
    elif points < 150:
        rank = "🥈 Середнячок (прогресс есть!)"
    elif points < 300:
        rank = "🥇 Продвинутый (ты почти легенда)"
    else:
        rank = "👑 ЛЕГЕНДА (диван повержен!)"

    text = (
        f"*Твоя статистика:*\n\n"
        f"⭐ Очки: {points}\n"
        f"🔥 Стрик: {user['streak']} дней\n"
        f"🎯 Целей: {goals_count} (выполнено: {completed})\n"
        f"🏆 Звание: {rank}\n\n"
        f"_Продолжай в том же духе!_ 💪"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def evening_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phrase = random.choice(EVENING_PHRASES)
    await update.message.reply_text(phrase, reply_markup=mood_keyboard())
    return EVENING_REPORT

async def handle_evening_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    user = get_user(uid)

    if "Огонь" in text:
        user["streak"] += 1
        user["points"] += 10
        response = random.choice(GOOD_REPORT_REACTIONS)
        response += f"\n\n🔥 Стрик теперь: {user['streak']} дней!"
    elif "Средненько" in text:
        user["points"] += 5
        response = "Средненько — это честно! +5 очков за честность 😄\nЗавтра лучше!"
    else:
        user["streak"] = 0
        response = random.choice(BAD_REPORT_REACTIONS)
        response += "\n\n_(Стрик сброшен, но это не конец!)_"

    update_user(uid, user)
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def goals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = get_user(uid)

    if not user["goals"]:
        goals_text = "_Целей пока нет. Ты либо уже всего достиг, либо ещё не начал. Я верю в первое!_ 😄"
    else:
        goals_text = "\n".join([
            f"{'✅' if g.get('done') else '⬜'} {g['text']}"
            for g in user["goals"]
        ])

    text = f"*Твои цели:*\n\n{goals_text}"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=goal_menu_keyboard())
    return MAIN_MENU

async def add_goal_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Напиши свою цель! Только конкретно — не 'стать лучше', а 'пробегать 5км три раза в неделю'. Мозг любит конкретику! 🎯",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True)
    )
    return SET_GOAL

async def save_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        await update.message.reply_text("Окей, возвращаемся!", reply_markup=main_keyboard())
        return MAIN_MENU

    uid = str(update.effective_user.id)
    user = get_user(uid)
    user["goals"].append({"text": text, "done": False})
    update_user(uid, user)

    reactions = [
        f"Записал! 📝 '{text}' — звучит серьёзно! Не подведи меня!",
        f"Цель принята! 🎯 '{text}' — верю, что справишься!",
        f"Огонь! 🔥 '{text}' добавлена. Теперь назад дороги нет... ну или есть, но стыдно!",
    ]
    await update.message.reply_text(random.choice(reactions), reply_markup=main_keyboard())
    return MAIN_MENU

async def complete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user = get_user(uid)

    active = [g for g in user["goals"] if not g.get("done")]
    if not active:
        await update.message.reply_text(
            "Все цели выполнены! 🏆 Ты либо продуктивный гений, либо ставишь слишком простые цели. Оба варианта ок!",
            reply_markup=main_keyboard()
        )
        return MAIN_MENU

    buttons = [[KeyboardButton(g["text"])] for g in active]
    buttons.append([KeyboardButton("🔙 Назад")])
    await update.message.reply_text(
        "Какую цель отмечаем выполненной? 🎉",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )
    return CHECK_GOAL

async def mark_goal_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔙 Назад":
        await update.message.reply_text("Окей!", reply_markup=main_keyboard())
        return MAIN_MENU

    uid = str(update.effective_user.id)
    user = get_user(uid)

    for goal in user["goals"]:
        if goal["text"] == text and not goal.get("done"):
            goal["done"] = True
            user["points"] += 20
            break

    update_user(uid, user)
    reactions = [
        f"🎉 ВЫПОЛНЕНО! '{text}' — ты это сделал! +20 очков! Горжусь!",
        f"💪 Да! '{text}' покорена! +20 очков! Следующая жертва?",
        f"🏆 ЛЕГЕНДА! '{text}' — в топку! +20 очков! Что дальше?",
    ]
    await update.message.reply_text(random.choice(reactions), reply_markup=main_keyboard())
    return MAIN_MENU

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "☀️ Задача дня" in text:
        return await daily_task(update, context)
    elif "🎯 Мои цели" in text:
        return await goals_menu(update, context)
    elif "😄 Анекдот" in text:
        return await joke(update, context)
    elif "📊 Моя статистика" in text:
        return await stats(update, context)
    elif "💬 Мотивация" in text:
        return await motivation(update, context)
    elif "🌙 Итоги дня" in text:
        return await evening_checkin(update, context)
    elif "➕ Добавить цель" in text:
        return await add_goal_prompt(update, context)
    elif "✅ Выполнить цель" in text:
        return await complete_goal(update, context)
    elif "🔙 Назад" in text:
        await update.message.reply_text("Возвращаемся в главное меню!", reply_markup=main_keyboard())
        return MAIN_MENU
    else:
        funny = [
            "Хм, не понял. Нажми кнопку, я не телепат... хотя иногда хотелось бы! 🔮",
            "Это не в моём словаре! Попробуй кнопки, они умнее меня. 😄",
            "Я бы ответил умно, но лучше используй кнопки! 👇",
        ]
        await update.message.reply_text(random.choice(funny), reply_markup=main_keyboard())
        return MAIN_MENU

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            EVENING_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_evening_report)],
            SET_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_goal)],
            CHECK_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, mark_goal_done)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)

    print("🤖 КоучБот 3000 запущен! Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
