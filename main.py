
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN

# 管理员ID
ADMINS = [8222147822]

def is_admin(uid):
    return uid in ADMINS


async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    text = update.message.text.strip()
    chat = update.effective_chat

    # 上课/下课
    if text == "上课":
        await chat.set_permissions(
            ChatPermissions(can_send_messages=True)
        )
        await update.message.reply_text(
            "🎓 已上课\n群成员可以正常发言"
        )
        return

    if text == "下课":
        await chat.set_permissions(
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(
            "🔕 已下课\n群成员暂时禁止发言"
        )
        return

    parts = text.split(maxsplit=1)

    if len(parts) != 2:
        return

    action, target = parts

    # 当前版本支持ID管理
    if not target.isdigit():
        await update.message.reply_text(
            "❌ 请使用用户ID\n例如：禁言 6144358438"
        )
        return

    uid = int(target)

    try:
        if action == "禁言":
            await chat.restrict_member(
                uid,
                ChatPermissions(can_send_messages=False),
                until_date=datetime.now()+timedelta(hours=1)
            )
            await update.message.reply_text(
                f"🔇 禁言成功\n用户ID：{uid}\n时间：1小时"
            )

        elif action == "解禁":
            await chat.restrict_member(
                uid,
                ChatPermissions(can_send_messages=True)
            )
            await update.message.reply_text(
                f"🔊 解禁成功\n用户ID：{uid}"
            )

        elif action == "踢出":
            await chat.ban_member(uid)
            await update.message.reply_text(
                f"🚫 已移除成员\n用户ID：{uid}"
            )

        elif action == "黑名单":
            await chat.ban_member(uid)
            await update.message.reply_text(
                f"🚷 已加入黑名单并移除\n用户ID：{uid}"
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ 执行失败\n{e}"
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handler)
    )

    print("FHGQ_Class_Switch_Bot_V1.6启动")
    app.run_polling()


if __name__ == "__main__":
    main()
