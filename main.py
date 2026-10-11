from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN
from datetime import datetime

ADMINS=[8222147822]
pending={}

def is_admin(uid): return uid in ADMINS

async def panel(update, context):
    if not is_admin(update.effective_user.id): return
    kb=[[InlineKeyboardButton("🟢 上课",callback_data="on"),InlineKeyboardButton("🔴 下课",callback_data="off")],
        [InlineKeyboardButton("🚫 封禁用户",callback_data="ban"),InlineKeyboardButton("🔓 解封用户",callback_data="unban")],
        [InlineKeyboardButton("📋 操作日志",callback_data="log")]]
    await update.message.reply_text("👮 FHGL 管理员面板",reply_markup=InlineKeyboardMarkup(kb))

async def button(update, context):
    q=update.callback_query
    if not is_admin(q.from_user.id): return
    await q.answer()
    if q.data=="ban":
        pending[q.from_user.id]="ban"
        await q.edit_message_text("🚫 请回复需要封禁成员的一条消息")
    elif q.data=="unban":
        pending[q.from_user.id]="unban"
        await q.edit_message_text("🔓 请发送需要解封的用户ID")
    elif q.data=="log":
        await q.edit_message_text("📋 操作日志功能已开启")
    else:
        await q.edit_message_text("操作完成")

async def msg(update, context):
    if not update.message or not is_admin(update.effective_user.id): return
    act=pending.get(update.effective_user.id)
    if act=="ban" and update.message.reply_to_message:
        uid=update.message.reply_to_message.from_user.id
        await update.effective_chat.ban_member(uid)
        await update.message.reply_text(f"🚫 已封禁用户 {uid}\n{datetime.now()}")
        pending.pop(update.effective_user.id,None)
    elif act=="unban":
        try:
            uid=int(update.message.text)
            await update.effective_chat.unban_member(uid)
            await update.message.reply_text(f"🔓 已解除封禁 {uid}")
        except: await update.message.reply_text("请输入正确ID")
        pending.pop(update.effective_user.id,None)

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("panel",panel))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg))
    app.run_polling()

if __name__=="__main__": main()
