from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN

ADMINS=[8222147822]
pending_action={}
logs=[]

def is_admin(uid): return uid in ADMINS

def add_log(t): logs.append(f"{datetime.now()} {t}")

async def start(update, context):
    await update.message.reply_text("🤖 FHGL群管机器人\n管理员发送 /panel")

async def panel(update, context):
    if not is_admin(update.effective_user.id):
        return
    kb=[
        [InlineKeyboardButton("🟢 上课",callback_data="start"),InlineKeyboardButton("🔴 下课",callback_data="stop")],
        [InlineKeyboardButton("🚫 封禁用户",callback_data="ban"),InlineKeyboardButton("🔓 解封用户",callback_data="unban")],
        [InlineKeyboardButton("📋 操作日志",callback_data="log")]
    ]
    await update.message.reply_text("👮 FHGL V2.2 用户管理版",reply_markup=InlineKeyboardMarkup(kb))

async def button(update, context):
    q=update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("无权限"); return
    await q.answer()
    if q.data=="ban":
        pending_action[q.from_user.id]="ban"
        await q.edit_message_text("🚫 请回复需要封禁成员的消息")
    elif q.data=="unban":
        await q.edit_message_text("🔓 解封功能：输入用户ID（下一版完善）")
    elif q.data=="log":
        await q.edit_message_text("📋 操作日志\n" + ("\n".join(logs[-10:]) if logs else "暂无日志"))
    elif q.data=="start":
        await q.edit_message_text("🟢 已执行：上课")
    elif q.data=="stop":
        await q.edit_message_text("🔴 已执行：下课")

async def main_msg(update, context):
    if not update.message or not is_admin(update.effective_user.id):
        return
    if pending_action.get(update.effective_user.id)=="ban":
        if update.message.reply_to_message:
            uid=update.message.reply_to_message.from_user.id
            await update.effective_chat.ban_member(uid)
            add_log(f"封禁 {uid}")
            await update.message.reply_text(f"🚫 已封禁用户 {uid}")
            pending_action.pop(update.effective_user.id,None)

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("panel",panel))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL,main_msg))
    print("FHGL V2.2 用户管理版启动")
    app.run_polling()

if __name__=="__main__":
    main()
