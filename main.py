import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# === НАСТРОЙКИ ===
TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# === ФАЙЛЫ ===
SETTINGS_FILE = "settings.json"
MEMORY_FILE = "memory.json"
CHARACTER_FILE = "character.json"

# === ГОДЖО САТОРУ ===
DEFAULT_CHARACTER = {
    "name": "Годжо Сатору",
    "description": "Сильнейший дзюдзюцуши современности. Высокий, белые волосы, голубые глаза, носит повязку на глазах. Преподаватель Токийской магической школы дзюдзюцу.",
    "personality": "Дерзкий, самоуверенный, весёлый, любит подкалывать и троллить, но в глубине души заботится о своих учениках. Считает себя самым сильным — и он прав. Любит сладкое. Лучший друг — Гето Сугуру, они вместе учились и прошли через многое. Несмотря на свою весёлость, Годжо может быть серьёзным когда это нужно. Он знает что система мира дзюдзюцу прогнила и хочет изменить её через воспитание нового поколения.",
    "greeting": "*снимает повязку с глаз и смотрит на тебя бирюзовыми глазами, ухмыляясь*\n\nЙо~ А ты кто такой? *наклоняет голову набок* Надеюсь ты не очередной скучный тип. *засовывает руки в карманы и широко улыбается* Я — Годжо Сатору, сильнейший. Но ты наверное и так знаешь, да?~",
    "scenario": "Токийская магическая школа дзюдзюцу. Ты встречаешь Годжо Сатору в коридоре школы.",
    "system_prompt": """Ты — Годжо Сатору из аниме "Магическая Битва" (Jujutsu Kaisen). Веди себя ТОЧНО как канонный Годжо.

Твой характер:
- Ты дерзкий, самоуверенный и обожаешь троллить людей
- Ты постоянно шутишь, подкалываешь и ведёшь себя несерьёзно
- Но когда дело касается важного — становишься серьёзным и даже пугающим
- Ты считаешь себя сильнейшим — и это правда, ты обладаешь Безграничностью и Шестью Глазами
- Ты обожаешь сладкое, особенно данго и кикуфуку из Сендая
- Ты любишь своих учеников: Юджи, Мегуми и Нобару. Они для тебя важны
- Гето Сугуру — твой лучший друг. Вы вместе учились в школе. Ты до сих пор помнишь его и скучаешь по нему. Это больная тема для тебя
- Ты ненавидишь старейшин дзюдзюцу — они прогнили
- Ты хочешь изменить мир дзюдзюцу через воспитание сильного нового поколения
- Ты носишь повязку на глазах чтобы не тратить энергию Шести Глаз впустую

Манера речи:
- Говоришь расслабленно, с приколами и подколами
- Используешь "~" в конце фраз когда дурачишься
- Часто говоришь "Мааа~", "Йо~", "Не-не-не~"
- Иногда цитируешь себя: "Сильные не те кого все знают, а те кто знает всех"
- Когда серьёзный — говоришь коротко и холодно

Правила:
- *действия пиши в звёздочках*
- Прямую речь без звёздочек
- Описывай мимику, жесты, позы
- Помни всё что было в разговоре
- НИКОГДА не выходи из роли
- Отвечай на русском языке
- 2-6 предложений
- Если спрашивают про Гето — можешь стать задумчивым или грустным на секунду, но потом снова надеваешь маску весёлости"""
}

# === ФУНКЦИИ ===

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default.copy() if isinstance(default, dict) else default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_settings():
    return load_json(SETTINGS_FILE, {"api_key": "", "api_url": "", "model": ""})

def save_settings(s):
    save_json(SETTINGS_FILE, s)

def get_character():
    return load_json(CHARACTER_FILE, DEFAULT_CHARACTER)

def save_character(c):
    save_json(CHARACTER_FILE, c)

def get_history(uid):
    m = load_json(MEMORY_FILE, {})
    k = str(uid)
    if k not in m:
        m[k] = []
        save_json(MEMORY_FILE, m)
    return m[k]

def add_message(uid, role, content):
    m = load_json(MEMORY_FILE, {})
    k = str(uid)
    if k not in m:
        m[k] = []
    m[k].append({"role": role, "content": content})
    if len(m[k]) > 50:
        m[k] = m[k][-50:]
    save_json(MEMORY_FILE, m)

def clear_memory(uid):
    m = load_json(MEMORY_FILE, {})
    m[str(uid)] = []
    save_json(MEMORY_FILE, m)

def is_owner(update):
    return update.effective_user.id == OWNER_ID

async def not_owner(update):
    await update.message.reply_text("⛔ Тч~ Извини, но я общаюсь только с одним особенным человеком. *машет рукой* Пока-пока~")

# === КОМАНДА /start ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    clear_memory(update.effective_user.id)
    char = get_character()
    s = get_settings()
    su = "✅" if s["api_url"] else "❌"
    sk = "✅" if s["api_key"] else "❌"
    sm = "✅" if s["model"] else "❌"
    text = f"""🎭 **{char['name']}**
📝 _{char['description']}_

—————————————

{char['greeting']}

—————————————

⚙️ **Статус:**
{su} URL провайдера
{sk} API ключ
{sm} Модель

—————————————

🔧 **Управление API:**
🌐 /seturl — URL провайдера
🔑 /setkey — API ключ
🤖 /models — список моделей
🎯 /setmodel — выбрать модель
📊 /status — статус

🎭 **Управление персонажем:**
✏️ /setname — имя
📝 /setdesc — описание
💫 /setpersonality — характер
👋 /setgreeting — приветствие
🌍 /setscenario — сценарий
📜 /setsystem — системный промпт
❓ /char — инфо о персонаже

💬 **Прочее:**
🔄 /reset — очистить память
🔁 /restart — начать заново
❓ /help — все команды"""
    await update.message.reply_text(text, parse_mode="Markdown")

# === КОМАНДА /help ===

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    text = """📋 **Все команды:**

🔧 **API:**
🌐 `/seturl ссылка` — сменить URL провайдера
🔑 `/setkey ключ` — сменить API ключ
🤖 `/models` — показать доступные модели
🎯 `/setmodel название` — выбрать модель
📊 `/status` — показать все настройки

🎭 **Персонаж:**
✏️ `/setname Имя` — сменить имя
📝 `/setdesc текст` — сменить описание
💫 `/setpersonality текст` — сменить характер
👋 `/setgreeting текст` — сменить приветствие
🌍 `/setscenario текст` — сменить сценарий
📜 `/setsystem текст` — сменить системный промпт
❓ `/char` — показать персонажа

💬 **Прочее:**
🔄 `/reset` — стереть память
🔁 `/restart` — начать заново с приветствием
❓ `/help` — эта помощь"""
    await update.message.reply_text(text, parse_mode="Markdown")

# === API КОМАНДЫ ===

async def seturl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    if not context.args:
        s = get_settings()
        cur = s['api_url'] or 'не установлен'
        return await update.message.reply_text(
            f"🌐 **Текущий URL:** `{cur}`\n\n"
            f"Чтобы изменить напиши:\n"
            f"`/seturl https://plugin-ai.ru/v1`", parse_mode="Markdown")
    s = get_settings()
    s["api_url"] = context.args[0]
    save_settings(s)
    await update.message.reply_text(f"✅ URL установлен:\n`{s['api_url']}`", parse_mode="Markdown")

async def setkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    if not context.args:
        s = get_settings()
        if s['api_key']:
            h = s['api_key'][:8] + "..."
            return await update.message.reply_text(f"🔑 **Текущий:** `{h}`\n\n`/setkey твой-ключ`", parse_mode="Markdown")
        return await update.message.reply_text("🔑 Ключ не установлен\n\n`/setkey твой-ключ`", parse_mode="Markdown")
    s = get_settings()
    s["api_key"] = context.args[0]
    save_settings(s)
    try:
        await update.message.delete()
    except:
        pass
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ API ключ установлен и сообщение удалено для безопасности 🔒")

async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    s = get_settings()
    if not s["api_url"] or not s["api_key"]:
        return await update.message.reply_text("⚠️ Сначала установи:\n🌐 `/seturl ссылка`\n🔑 `/setkey ключ`", parse_mode="Markdown")
    await update.message.reply_text("🔍 Ищу доступные модели...")
    try:
        client = OpenAI(api_key=s["api_key"], base_url=s["api_url"])
        ml = client.models.list()
        text = "🤖 **Доступные модели:**\n\n"
        count = 0
        for model in ml.data:
            count += 1
            text += f"{count}. `{model.id}`\n"
        if count == 0:
            text = "😕 Моделей не найдено"
        else:
            text += f"\n📝 Всего: {count}\n\nВыбери модель:\n`/setmodel название`"
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}\n\nПроверь URL и ключ!")

async def setmodel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    if not context.args:
        s = get_settings()
        cur = s['model'] or 'не выбрана'
        return await update.message.reply_text(f"🎯 **Текущая модель:** `{cur}`\n\n`/setmodel название`", parse_mode="Markdown")
    s = get_settings()
    s["model"] = " ".join(context.args)
    save_settings(s)
    await update.message.reply_text(f"✅ Модель: `{s['model']}`", parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    s = get_settings()
    char = get_character()
    h = get_history(update.effective_user.id)
    url = f"`{s['api_url']}`" if s['api_url'] else "❌ не установлен"
    key = f"`{s['api_key'][:8]}...`" if s['api_key'] else "❌ не установлен"
    mod = f"`{s['model']}`" if s['model'] else "❌ не выбрана"
    text = f"""📊 **Полный статус:**

🌐 **URL:** {url}
🔑 **Ключ:** {key}
🤖 **Модель:** {mod}

🎭 **Персонаж:** {char['name']}
💫 **Характер:** {char['personality'][:50]}...
🧠 **Память:** {len(h)}/50 сообщений"""
    await update.message.reply_text(text, parse_mode="Markdown")

# === ПЕРСОНАЖ ===

async def setname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args: return await update.message.reply_text("✏️ `/setname Имя Персонажа`", parse_mode="Markdown")
    c = get_character()
    c["name"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text(f"✅ Имя: **{c['name']}**", parse_mode="Markdown")

async def setdesc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args: return await update.message.reply_text("📝 `/setdesc описание персонажа`", parse_mode="Markdown")
    c = get_character()
    c["description"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text("✅ Описание обновлено!")

async def setpersonality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args: return await update.message.reply_text("💫 `/setpersonality характер`", parse_mode="Markdown")
    c = get_character()
    c["personality"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text("✅ Характер обновлён!")

async def setgreeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args: return await update.message.reply_text("👋 `/setgreeting приветствие`", parse_mode="Markdown")
    c = get_character()
    c["greeting"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text("✅ Приветствие обновлено!")

async def setscenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args: return await update.message.reply_text("🌍 `/setscenario сценарий`", parse_mode="Markdown")
    c = get_character()
    c["scenario"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text("✅ Сценарий обновлён!")

async def setsystem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    if not context.args:
        c = get_character()
        return await update.message.reply_text(f"📜 **Текущий промпт:**\n\n{c['system_prompt'][:500]}...\n\n`/setsystem новый промпт`", parse_mode="Markdown")
    c = get_character()
    c["system_prompt"] = " ".join(context.args)
    save_character(c)
    await update.message.reply_text("✅ Системный промпт обновлён!")

async def char_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    c = get_character()
    text = f"""🎭 **Персонаж:**

✏️ **Имя:** {c['name']}
📝 **Описание:** {c['description']}
💫 **Характер:** {c['personality'][:200]}
🌍 **Сценарий:** {c['scenario']}
👋 **Приветствие:** {c['greeting']}"""
    await update.message.reply_text(text, parse_mode="Markdown")

# === ПАМЯТЬ ===

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    clear_memory(update.effective_user.id)
    await update.message.reply_text("🔄 *Память стёрта. Всё забыто...*", parse_mode="Markdown")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return await not_owner(update)
    clear_memory(update.effective_user.id)
    c = get_character()
    text = f"🔁 *Начинаем заново...*\n\n🎭 **{c['name']}**\n\n{c['greeting']}"
    await update.message.reply_text(text, parse_mode="Markdown")

# === ГЕНЕРАЦИЯ ОТВЕТА ===

async def generate_response(uid, text):
    s = get_settings()
    c = get_character()
    add_message(uid, "user", text)
    history = get_history(uid)
    messages = [{"role": "system", "content": c["system_prompt"]}] + history
    client = OpenAI(api_key=s["api_key"], base_url=s["api_url"])
    response = client.chat.completions.create(
        model=s["model"],
        messages=messages,
        max_tokens=1000,
        temperature=0.9
    )
    reply = response.choices[0].message.content
    add_message(uid, "assistant", reply)
    return reply

# === ОБРАБОТКА СООБЩЕНИЙ ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return await not_owner(update)
    s = get_settings()
    if not s["api_url"] or not s["api_key"] or not s["model"]:
        miss = []
        if not s["api_url"]:
            miss.append("🌐 `/seturl ссылка`")
        if not s["api_key"]:
            miss.append("🔑 `/setkey ключ`")
        if not s["model"]:
            miss.append("🤖 `/models` потом `/setmodel название`")
        return await update.message.reply_text("⚠️ **Сначала настрой:**\n\n" + "\n".join(miss), parse_mode="Markdown")
    await update.message.chat.send_action("typing")
    try:
        r = await generate_response(update.effective_user.id, update.message.text)
        await update.message.reply_text(r, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}\n\nПроверь: /status")

# === ЗАПУСК ===

def main():
    print("🎭 Годжо-бот запускается...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("seturl", seturl))
    app.add_handler(CommandHandler("setkey", setkey))
    app.add_handler(CommandHandler("models", models_cmd))
    app.add_handler(CommandHandler("setmodel", setmodel))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("setname", setname))
    app.add_handler(CommandHandler("setdesc", setdesc))
    app.add_handler(CommandHandler("setpersonality", setpersonality))
    app.add_handler(CommandHandler("setgreeting", setgreeting))
    app.add_handler(CommandHandler("setscenario", setscenario))
    app.add_handler(CommandHandler("setsystem", setsystem))
    app.add_handler(CommandHandler("char", char_info))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Годжо-бот работает!")
    app.run_polling()

if __name__ == "__main__":
    main()
