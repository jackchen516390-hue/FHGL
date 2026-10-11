
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMINS


def is_admin(uid):
    return uid in ADMINS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 FHGL群管机器人\n"
        "管理员群内回复消息使用 /ban"
    )


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ 无权限")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("请回复需要封禁成员的消息后发送 /ban")
        return

    target = update.message.reply_to_message.from_user

    try:
        await update.effective_chat.ban_member(target.id)
        await update.message.reply_text(
            f"🚫 已封禁用户\n\n"
            f"用户：{target.first_name}\n"
            f"ID：{target.id}\n"
            f"操作人：{update.effective_user.id}"
        )
    except Exception as e:
        await update.message.reply_text(f"执行失败：{e}")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ 无权限")
        return

    if not context.args:
        await update.message.reply_text("用法：/unban 用户ID")
        return

    try:
        uid = int(context.args[0])
        await update.effective_chat.unban_member(uid)
        await update.message.reply_text(
            f"🔓 已解除封禁\n用户ID：{uid}"
        )
    except Exception as e:
        await update.message.reply_text(f"执行失败：{e}")


async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 用户信息\n\n"
            f"用户名：{u.username}\n"
            f"ID：{u.id}"
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("user", user_info))

    print("FHGL V2.4 群内管理版启动")

    app.run_polling()


if __name__ == "__main__":
    main()
