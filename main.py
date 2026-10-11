
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, ADMINS


def is_admin(uid):
    return uid in ADMINS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("FHGL群管机器人运行中")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("请回复成员消息后发送 /ban")
        return

    user = update.message.reply_to_message.from_user
    await update.effective_chat.ban_member(user.id)

    await update.message.reply_text(
        f"🚫 已封禁用户\nID: {user.id}\n操作人: {update.effective_user.id}"
    )


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        return

    uid = int(context.args[0])
    await update.effective_chat.unban_member(uid)
    await update.message.reply_text(f"🔓 已解除封禁\nID: {uid}")


async def class_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if update.message.text in ["上课", "下课"]:
        # 静默执行，不回复消息
        return


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, class_status))

    print("FHGL V2.5.1 群内管理优化版启动")
    app.run_polling()


if __name__ == "__main__":
    main()
