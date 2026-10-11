
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from config import BOT_TOKEN


ADMINS = [8222147822]


def is_admin(uid):
    return uid in ADMINS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 FHGL群管机器人\n\n"
        "管理员发送 /panel 打开管理面板"
    )


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ 无权限")
        return

    keyboard = [
        [
            InlineKeyboardButton("🟢 上课", callback_data="start_class"),
            InlineKeyboardButton("🔴 下课", callback_data="stop_class"),
        ],
        [
            InlineKeyboardButton("🚫 封禁用户", callback_data="ban"),
            InlineKeyboardButton("🔓 解封用户", callback_data="unban"),
        ],
        [
            InlineKeyboardButton("📋 操作日志", callback_data="log")
        ]
    ]

    await update.message.reply_text(
        "👮 FHGL 管理员面板",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("无权限")
        return

    await query.answer()

    if query.data == "start_class":
        await query.edit_message_text("🟢 已执行：上课")

    elif query.data == "stop_class":
        await query.edit_message_text("🔴 已执行：下课")

    elif query.data == "ban":
        await query.edit_message_text("🚫 封禁功能开发中")

    elif query.data == "unban":
        await query.edit_message_text("🔓 解封功能开发中")

    elif query.data == "log":
        await query.edit_message_text("📋 日志功能开发中")


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button))

    print("FHGL V2.1 管理员面板启动")

    app.run_polling()


if __name__ == "__main__":
    main()
