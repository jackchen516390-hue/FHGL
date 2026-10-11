from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN

ADMINS = [8222147822]

def is_admin(uid):
    return uid in ADMINS

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text
    chat = update.effective_chat

    if text == "上课":
        await chat.set_permissions(ChatPermissions(can_send_messages=True))
        await update.message.reply_text("🎓 已上课")
        return

    if text == "下课":
        await chat.set_permissions(ChatPermissions(can_send_messages=False))
        await update.message.reply_text("🔇 已下课")
        return

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    print("FHGL群管机器人启动")
    app.run_polling()

if __name__ == "__main__":
    main()
