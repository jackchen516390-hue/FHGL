"""FHGL V2.6.3: Chinese group commands and independent /gm_* commands."""
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ChatType
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, SUPER_ADMINS, DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('fhgl')
DB = Path(DATA_DIR) / 'fhgl_data.sqlite3'


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB), timeout=20)
    con.execute('PRAGMA busy_timeout=20000')
    con.execute('CREATE TABLE IF NOT EXISTS admins (uid INTEGER PRIMARY KEY, added_by INTEGER, created TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS blacklist (chat_id INTEGER, uid INTEGER, name TEXT, added_by INTEGER, created TEXT, PRIMARY KEY(chat_id, uid))')
    con.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, actor INTEGER, action TEXT, target INTEGER, created TEXT)')
    con.commit()
    return con


def stamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def audit(chat_id, actor, action, target=None):
    with connect() as con:
        con.execute('INSERT INTO audit(chat_id,actor,action,target,created) VALUES(?,?,?,?,?)', (chat_id, actor, action, target, stamp()))


def is_super(uid):
    return uid in SUPER_ADMINS


def is_admin(uid):
    if is_super(uid):
        return True
    with connect() as con:
        return con.execute('SELECT 1 FROM admins WHERE uid=?', (uid,)).fetchone() is not None


async def guard(update, super_only=False):
    msg, chat, user = update.effective_message, update.effective_chat, update.effective_user
    if not msg or not chat or chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        if msg:
            await msg.reply_text('请在 FHGL 管理的群内使用此命令。')
        return False
    if not user or not (is_super(user.id) if super_only else is_admin(user.id)):
        await msg.reply_text('❌ 无权限执行此操作。')
        return False
    return True


def target_from(update, context):
    msg = update.effective_message
    reply = msg.reply_to_message
    if reply and reply.from_user:
        u = reply.from_user
        return u.id, u.full_name
    if context.args and context.args[0].lstrip('-').isdigit():
        return int(context.args[0]), str(context.args[0])
    return None, None


async def protected(update, context, uid):
    if is_admin(uid):
        await update.effective_message.reply_text('❌ 不能封禁或拉黑机器人管理员。')
        return True
    bot_id = context.bot.id
    if uid == bot_id:
        await update.effective_message.reply_text('❌ 不能操作机器人自身。')
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, uid)
        if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
            await update.effective_message.reply_text('❌ 不能封禁或拉黑 Telegram 群主/群管理员。')
            return True
    except TelegramError as exc:
        logger.warning('Cannot check target membership: %s', exc)
        await update.effective_message.reply_text('❌ 无法核实目标身份，已取消操作。')
        return True
    return False


async def on(update, context):
    if not await guard(update): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True, can_invite_users=True))
    audit(update.effective_chat.id, update.effective_user.id, '上课')
    await update.effective_message.reply_text('🟢 已上课\n群内已解除禁言，成员可以正常发言。')


async def off(update, context):
    if not await guard(update): return
    await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False))
    audit(update.effective_chat.id, update.effective_user.id, '下课')
    await update.effective_message.reply_text('🔴 已下课\n群内已开启禁言，普通成员暂停发言。')


async def ban(update, context):
    if not await guard(update): return
    uid, name = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('请回复目标成员的消息发送「封禁」，或使用 /gm_ban 用户ID。')
        return
    if await protected(update, context, uid): return
    await context.bot.ban_chat_member(update.effective_chat.id, uid)
    audit(update.effective_chat.id, update.effective_user.id, '封禁', uid)
    await update.effective_message.reply_text(f'🚫 已封禁：{name}\n用户ID：{uid}')


async def unban(update, context):
    if not await guard(update): return
    uid, _ = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('用法：/gm_unban 用户ID，或「解封 用户ID」。')
        return
    await context.bot.unban_chat_member(update.effective_chat.id, uid, only_if_banned=True)
    audit(update.effective_chat.id, update.effective_user.id, '解封', uid)
    await update.effective_message.reply_text(f'🔓 已执行解封：{uid}')


async def black_add(update, context):
    if not await guard(update): return
    uid, name = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('回复目标成员发送「加黑名单」，或 /gm_black_add 用户ID。')
        return
    if await protected(update, context, uid): return
    # Ban first; do not claim blacklisting succeeded if Telegram rejected it.
    await context.bot.ban_chat_member(update.effective_chat.id, uid)
    with connect() as con:
        con.execute('INSERT OR REPLACE INTO blacklist VALUES(?,?,?,?,?)', (update.effective_chat.id, uid, name, update.effective_user.id, stamp()))
    audit(update.effective_chat.id, update.effective_user.id, '加入黑名单', uid)
    await update.effective_message.reply_text(f'📛 已加入本群黑名单并封禁：{name}\nID：{uid}')


async def black_del(update, context):
    if not await guard(update): return
    uid, _ = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('用法：/gm_black_del 用户ID，或「移除黑名单 用户ID」。')
        return
    with connect() as con:
        con.execute('DELETE FROM blacklist WHERE chat_id=? AND uid=?', (update.effective_chat.id, uid))
    audit(update.effective_chat.id, update.effective_user.id, '移除黑名单', uid)
    await update.effective_message.reply_text(f'✅ 已移除本群黑名单：{uid}\n如需允许重新进群，请另行执行解封。')


async def blacklist(update, context):
    if not await guard(update): return
    with connect() as con:
        rows = con.execute('SELECT uid,name FROM blacklist WHERE chat_id=? ORDER BY created DESC LIMIT 50', (update.effective_chat.id,)).fetchall()
    await update.effective_message.reply_text('📋 本群黑名单（最多显示50条）：\n' + ('\n'.join(f'{i}. {name}（{uid}）' for i,(uid,name) in enumerate(rows,1)) if rows else '暂无'))


async def admin_add(update, context):
    if not await guard(update, super_only=True): return
    uid, _ = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('回复成员发送「添加管理员」，或 /gm_admin_add 用户ID。')
        return
    with connect() as con:
        con.execute('INSERT OR IGNORE INTO admins VALUES(?,?,?)', (uid, update.effective_user.id, stamp()))
    audit(update.effective_chat.id, update.effective_user.id, '添加管理员', uid)
    await update.effective_message.reply_text(f'👤 已添加机器人管理员：{uid}')


async def admin_del(update, context):
    if not await guard(update, super_only=True): return
    uid, _ = target_from(update, context)
    if uid is None:
        await update.effective_message.reply_text('用法：/gm_admin_del 用户ID，或「删除管理员 用户ID」。')
        return
    if is_super(uid):
        await update.effective_message.reply_text('❌ 不能通过普通管理员命令移除超级管理员。')
        return
    with connect() as con:
        con.execute('DELETE FROM admins WHERE uid=?', (uid,))
    audit(update.effective_chat.id, update.effective_user.id, '删除管理员', uid)
    await update.effective_message.reply_text(f'👤 已取消机器人管理员：{uid}')


async def admins(update, context):
    if not await guard(update): return
    with connect() as con:
        rows = con.execute('SELECT uid FROM admins ORDER BY uid').fetchall()
    await update.effective_message.reply_text('👥 超级管理员：' + ', '.join(map(str, SUPER_ADMINS)) + '\n普通管理员：' + (', '.join(str(r[0]) for r in rows) or '暂无'))


async def logs(update, context):
    if not await guard(update): return
    with connect() as con:
        rows = con.execute('SELECT created,actor,action,target FROM audit WHERE chat_id=? ORDER BY id DESC LIMIT 15', (update.effective_chat.id,)).fetchall()
    await update.effective_message.reply_text('📜 最近15条操作：\n' + ('\n'.join(f'{dt} | {action} | 操作人:{actor}' + (f' | 目标:{target}' if target is not None else '') for dt,actor,action,target in rows) if rows else '暂无记录'))


HELP = '''FHGL 群管专用命令（仅本机器人）
上课 /gm_on；下课 /gm_off
封禁 /gm_ban；解封 /gm_unban 用户ID
加黑名单 /gm_black_add；移除黑名单 /gm_black_del 用户ID
黑名单 /gm_blacklist
添加管理员 /gm_admin_add；删除管理员 /gm_admin_del 用户ID
管理员列表 /gm_admins；操作日志 /gm_logs
群管帮助 /gm_help
封禁、加黑名单、添加管理员可回复目标消息操作。
普通管理员不能添加/删除管理员。'''


async def help_cmd(update, context):
    if not await guard(update): return
    await update.effective_message.reply_text(HELP)


ROUTES = {
    '上课': on, '下课': off, '封禁': ban, '解封': unban,
    '加黑名单': black_add, '添加黑名单': black_add,
    '移除黑名单': black_del, '删除黑名单': black_del,
    '黑名单': blacklist, '添加管理员': admin_add, '删除管理员': admin_del,
    '管理员列表': admins, '查看管理员': admins,
    '操作日志': logs, '群管帮助': help_cmd,
}


async def chinese(update, context):
    msg = update.effective_message
    if not msg or not msg.text: return
    value = msg.text.strip()
    name, _, tail = value.partition(' ')
    if name not in ROUTES: return
    # Reject free-form prose; only exact Chinese commands or commands with a numeric ID.
    if tail and not tail.strip().lstrip('-').isdigit(): return
    context.args = [tail.strip()] if tail else []
    await ROUTES[name](update, context)


async def join_check(update, context):
    msg = update.effective_message
    if not msg or not msg.new_chat_members: return
    with connect() as con:
        for member in msg.new_chat_members:
            exists = con.execute('SELECT 1 FROM blacklist WHERE chat_id=? AND uid=?', (update.effective_chat.id, member.id)).fetchone()
            if exists:
                if await protected(update, context, member.id): continue
                await context.bot.ban_chat_member(update.effective_chat.id, member.id)
                audit(update.effective_chat.id, context.bot.id, '黑名单进群拦截', member.id)


async def errors(update, context):
    logger.error('Handler error: %s', context.error, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text('❌ 操作失败，请检查机器人是否有禁言/封禁权限，或查看 Railway 日志。')
        except TelegramError:
            pass


def main():
    if not BOT_TOKEN or BOT_TOKEN == '你的机器人TOKEN':
        raise RuntimeError('请在 FHGL Railway Variables 中设置 BOT_TOKEN')
    if not SUPER_ADMINS:
        raise RuntimeError('至少设置一个 SUPER_ADMINS')
    with connect(): pass
    app = Application.builder().token(BOT_TOKEN).build()
    commands = {
        'gm_on': on, 'gm_off': off, 'gm_ban': ban, 'gm_unban': unban,
        'gm_black_add': black_add, 'gm_black_del': black_del, 'gm_blacklist': blacklist,
        'gm_admin_add': admin_add, 'gm_admin_del': admin_del, 'gm_admins': admins,
        'gm_logs': logs, 'gm_help': help_cmd,
    }
    for name, handler in commands.items():
        app.add_handler(CommandHandler(name, handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, chinese))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, join_check))
    app.add_error_handler(errors)
    logger.info('FHGL V2.6.3 started')
    app.run_polling()


if __name__ == '__main__':
    main()
