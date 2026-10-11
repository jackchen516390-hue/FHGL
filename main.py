
import json
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMINS

BLACK_FILE = "blacklist.json"
LOG_FILE = "logs.json"


def is_admin(uid):
    return uid in ADMINS


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_log(action, admin, target=""):
    logs = load_json(LOG_FILE)
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "admin": admin,
        "target": target
    })
    save_json(LOG_FILE, logs[-200:])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FHGL完整群管机器人运行中")


async def text_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not is_admin(update.effective_user.id):
        return

    if update.message.text == "下课":
        await update.effective_chat.set_permissions(
            ChatPermissions(can_send_messages=False)
        )
        add_log("下课禁言", update.effective_user.id)

    elif update.message.text == "上课":
        await update.effective_chat.set_permissions(
            ChatPermissions(can_send_messages=True)
        )
        add_log("上课解禁", update.effective_user.id)


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        return

    uid = update.message.reply_to_message.from_user.id
    await update.effective_chat.ban_member(uid)
    add_log("封禁用户", update.effective_user.id, uid)
    await update.message.reply_text(f"🚫 已封禁\nID:{uid}")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args:
        return
    uid = int(context.args[0])
    await update.effective_chat.unban_member(uid)
    add_log("解封用户", update.effective_user.id, uid)


async def black(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        return

    user = update.message.reply_to_message.from_user
    data = load_json(BLACK_FILE)

    if user.id not in data:
        data.append(user.id)
        save_json(BLACK_FILE, data)

    add_log("加入黑名单", update.effective_user.id, user.id)
    await update.message.reply_text(f"🚫 黑名单加入\nID:{user.id}")


async def unblack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args:
        return

    uid = int(context.args[0])
    data = load_json(BLACK_FILE)

    if uid in data:
        data.remove(uid)
        save_json(BLACK_FILE, data)

    add_log("移除黑名单", update.effective_user.id, uid)


async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    data = load_json(BLACK_FILE)
    await update.message.reply_text(f"🚫 黑名单:\n{data}")


async def check_black(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        data = load_json(BLACK_FILE)
        if update.effective_user.id in data:
            await update.message.delete()


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("black", black))
    app.add_handler(CommandHandler("unblack", unblack))
    app.add_handler(CommandHandler("blacklist", blacklist))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_manage))
    app.add_handler(MessageHandler(filters.ALL, check_black))

    print("FHGL V2.6 完整群管版启动")
    app.run_polling()


if __name__ == "__main__":
    main()
