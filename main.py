
import json
from datetime import datetime
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, ADMINS

BLACK_FILE = "blacklist.json"
LOG_FILE = "logs.json"


def is_admin(uid):
    return uid in ADMINS


def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log(action, admin, target=""):
    logs = load_file(LOG_FILE)
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "admin": admin,
        "target": target
    })
    save_file(LOG_FILE, logs[-200:])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FHGL群管机器人运行中")


# 上课：解除全群禁言并提示
async def class_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True
    )

    await update.effective_chat.set_permissions(permissions=permissions)
    log("上课解除禁言", update.effective_user.id)

    await update.message.reply_text(
        "🟢 已上课\n\n群内恢复正常发言"
    )


# 下课：全群禁言并提示
async def class_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    permissions = ChatPermissions(
        can_send_messages=False
    )

    await update.effective_chat.set_permissions(permissions=permissions)
    log("下课开启禁言", update.effective_user.id)

    await update.message.reply_text(
        "🔴 已下课\n\n群内已开启禁言模式"
    )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("请回复需要封禁成员的消息后发送 /ban")
        return

    uid = update.message.reply_to_message.from_user.id
    await update.effective_chat.ban_member(uid)

    log("封禁用户", update.effective_user.id, uid)

    await update.message.reply_text(
        f"🚫 已封禁用户\nID: {uid}"
    )


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        return

    uid = int(context.args[0])
    await update.effective_chat.unban_member(uid)
    log("解封用户", update.effective_user.id, uid)


async def black(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not update.message.reply_to_message:
        return

    uid = update.message.reply_to_message.from_user.id
    data = load_file(BLACK_FILE)

    if uid not in data:
        data.append(uid)
        save_file(BLACK_FILE, data)

    log("加入黑名单", update.effective_user.id, uid)

    await update.message.reply_text(
        f"🚫 已加入黑名单\nID: {uid}"
    )


async def unblack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        return

    uid = int(context.args[0])
    data = load_file(BLACK_FILE)

    if uid in data:
        data.remove(uid)
        save_file(BLACK_FILE, data)

    log("移除黑名单", update.effective_user.id, uid)


async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        f"🚫 黑名单:\n{load_file(BLACK_FILE)}"
    )


async def check_black(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user and update.effective_user.id in load_file(BLACK_FILE):
        if update.message:
            await update.message.delete()


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text:
        return

    if update.message.text == "上课":
        await class_on(update, context)

    elif update.message.text == "下课":
        await class_off(update, context)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("black", black))
    app.add_handler(CommandHandler("unblack", unblack))
    app.add_handler(CommandHandler("blacklist", blacklist))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.ALL, check_black))

    print("FHGL V2.6.1 完整群管修正版启动")
    app.run_polling()


if __name__ == "__main__":
    main()
