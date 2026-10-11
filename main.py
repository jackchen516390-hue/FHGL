from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters
from config import BOT_TOKEN

ADMINS = [8222147822]


def is_admin(uid):
    return uid in ADMINS


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [
            InlineKeyboardButton("🟢 上课", callback_data="start"),
            InlineKeyboardButton("🔴 下课", callback_data="stop"),
        ],
        [
            InlineKeyboardButton("🚫 封禁用户", callback_data="ban"),
            InlineKeyboardButton("🔓 解封用户", callback_data="unban"),
        ],
        [
            InlineKeyboardButton("📋 操作日志", callback_data="log"),
        ],
    ]

    await update.message.reply_text(
        "👮 FHGL 管理员面板",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_admin(query.from_user.id):
        return

    await query.answer()

    if query.data == "start":
        await query.edit_message_text("🟢 已选择：上课")

    elif query.data == "stop":
        await query.edit_message_text("🔴 已选择：下课")

    elif query.data == "ban":
        await query.edit_message_text("🚫 封禁功能开发中")

    elif query.data == "unban":
        await query.edit_message_text("🔓 解封功能开发中")

    elif query.data == "log":
        await query.edit_message_text("📋 操作日志开发中")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button))

    print("FHGL V2 管理员面板启动")

    app.run_polling()


if __name__ == "__main__":
    main()
