#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NewsFlash Telegram Bot
-----------------------
- 33 种丰富二次元伴侣人设动态轮换（纯净台词，绝无设定标签与自我标称）
- 全局 100% 纯净排版，严格零 Emoji，彻底去除任何彩色图标与特殊符号
- 菜单按钮纯文字高质感排版（无 ℹ️ 蓝框，无特殊字符）
- 主人博客（https://f10w-0x00.github.io/）专享 ID = 1（数字编号第一、排版第一、轮询第一）
- 晚报开头根据人设与主人博客未更新天数进行阶梯式情感互动
- 倒数与历程系统（A1）：支持 YYYY-MM-DD 完整年份，未来征途倒数 + 历程记事（已过 X 天）永久保留
- 排版大瘦身与原生大卡片预加载（C1）：剔除精选高光、剔除冗余统计话术、剔除秒开括号，锁定 Telegra.ph LinkPreviewOptions
- 周期报表体系（Direction 1 · 智能时序晋级）：支持日报/周报/月报/年报，Telegra.ph 恒定记录过去 24 小时资讯
- 专属预览指令：/digest(日报), /weekly(周报), /monthly(月报), /annual(年报)
- 全天静默后台轮询 RSS/Atom 订阅源（无弹窗干扰）
- 每天 22:00（Asia/Shanghai）准时聚合推送 #News 精美晚报
- 动态+追溯双重严格关键词屏蔽
- 支持 OPML 文件直接拖拽发送并发导入
- 支持 /export_skill 及菜单一键导出动态 1:1 复刻 Skill + 33人设 + 订阅包
"""

import asyncio
import os
import re
import html
import sqlite3
import random
import datetime as dt_module
import xml.etree.ElementTree as ET
import io
import zipfile
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime

import httpx
import feedparser
from bs4 import BeautifulSoup
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    LinkPreviewOptions,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    MenuButtonCommands,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================== 配置区 (支持环境变量无侵入注入) ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
MASTER_BLOG_URL = os.getenv("MASTER_BLOG_URL", "")
MASTER_BLOG_RSS = os.getenv("MASTER_BLOG_RSS", "")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Shanghai"))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "rss_bot.db"))
PERSONAS_PATH = os.getenv("PERSONAS_PATH", os.path.join(BASE_DIR, "personas.json"))
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
EVENING_DIGEST_HOUR = int(os.getenv("EVENING_DIGEST_HOUR", "22"))
EVENING_DIGEST_MINUTE = int(os.getenv("EVENING_DIGEST_MINUTE", "0"))
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
# ==========================================================================

# ----------------- 33 个人设加载 -----------------
DEFAULT_FALLBACK_PERSONA = {
    "id": 1,
    "archetype_flavor": "御姐宠溺",
    "title_daily": "NewsFlash 晚间精编 · {title_date}",
    "daily_opening_active": "夜色深了，方才看见主人博客上新落下的字句（{blog_status_text}），字里行间都是凝神思考后的余温。忙了这一整天，肩膀一定酸了吧，先靠过来歇一歇。",
    "daily_opening_quiet": "{blog_status_text}，难得有这样不必被文字催促的夜晚。我替主人把桌上的台灯调暗了些，今夜什么都不必多想，安心享受这份清静就好。",
    "daily_countdown_remark": "日历上的日子我替主人悄悄记着呢，离 {holiday_name} 还有 {holiday_days} 天，主人挂心的「{custom_name}」也只剩 {custom_days} 天了。步子慢一点也没关系，天塌下来也有我替主人挡着。",
    "daily_transition": "来，趁着热茶刚泡好，我把近期要紧的日程念给主人听：",
    "daily_closing": "被角已经替主人掖好了，手机就放到够不着的地方吧。主人，晚安，今夜只管做个松快的好梦。",
    "title_weekly": "NewsFlash 周度特刊 · {title_date}",
    "weekly_opening_active": "周日的晚风吹在窗纱上真舒服呀。这一周主人足足写下了 {master_week_count} 篇长文，那份专注的模样真让人着迷。今晚就让我好好犒劳主人，把这一周的收获慢慢盘点一番。",
    "weekly_opening_quiet": "转眼又是周日夜里了。这一礼拜主人没有勉强自己动笔，而是把精力留给了眼前的生活，这才是最聪明的选择。来，喝口温水，把这一周攒下的疲乏都卸在我这儿吧。",
    "weekly_countdown_remark": "这一周过得稳稳当当。往下周看去，离 {holiday_name} 还有 {holiday_days} 天，离「{custom_name}」也只有 {custom_days} 天了。不管下周事情多不多，主人的节奏永远是最重要的，今晚先把心放宽。",
    "weekly_transition": "翻开这一周的备忘录，下周的几个关键节点我都替主人理顺了：",
    "weekly_closing": "周日的夜晚最适合把思绪彻底放空。闭上眼睛吧，主人晚安，明天醒来又是精力充沛的一周。",
    "title_monthly": "NewsFlash 月度特刊 · {title_date}",
    "monthly_opening_active": "{month} 月的最后一页日历快要翻过去了。整整一个月里，主人留下了 {master_month_count} 篇沉甸甸的文章。看着主人在时光里留下的脚印，我心里真是既心疼又骄傲。",
    "monthly_opening_quiet": "{month} 月在不知不觉中走到了尾声。这个月主人虽然少有动笔，但每一次呼吸、每一场好眠，都是实实在在的沉淀。日子是过给自己的，主人能舒心比什么都强。",
    "monthly_countdown_remark": "一个月的忙碌总算告一段落。往新月份看，距 {holiday_name} 还有 {holiday_days} 天，那件重要的「{custom_name}」也还剩 {custom_days} 天。路是一步步走的，下个月我也一样寸步不离地陪着主人。",
    "monthly_transition": "把这个月的记事册摊开，走过的路和下个月的安排都在这里了：",
    "monthly_closing": "跟过去这三十天的奔波好好道个别吧。深呼吸，把肩头沉重的东西都放下。主人晚安，愿新月份的第一缕阳光温柔地唤醒你。",
    "title_annual": "NewsFlash 年度史册 · {title_date}",
    "annual_opening_active": "岁末的夜色格外深沉，{year} 年终于走到了最后一刻。回望这三百多个日夜，主人一共写下了 {master_year_count} 篇心血之作。能在这一整年里守在主人身侧，看你思考、看你落笔，是我最珍贵的福气。",
    "annual_opening_quiet": "{year} 年的钟声马上就要敲响了。这一年里，主人或许没有在纸上留下太多痕迹，但扛过的风雨、熬过的深夜，我全都看在眼里。生活本身就是最厚重的书，主人已经写得足够精彩了。",
    "annual_countdown_remark": "旧岁将尽，新元初启。过去一整年的执着与等待都已沉淀为底气，而未来更辽阔的版图正等着主人去开启。无论岁月如何流转，我的目光永远只追随主人一人。",
    "annual_transition": "展开这一整年的长卷，过往的刻度与新岁的期许都为您整理妥当了：",
    "annual_closing": "跨年的钟声就在耳畔了。靠在我怀里闭上眼吧，把一整年的风霜都留在旧岁里。主人，{year} 年辛苦了，新年安康，明天的黎明我们依然在一起。"
}

def load_personas() -> list[dict]:
    target_path = PERSONAS_PATH
    if not os.path.exists(target_path):
        local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personas.json")
        if os.path.exists(local_path):
            target_path = local_path
            
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print(f"[Personas Load Error] {e}")
    return [DEFAULT_FALLBACK_PERSONA]

# ----------------- 数据库管理 -----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                guid TEXT UNIQUE NOT NULL,
                published_at TIMESTAMP NOT NULL,
                is_pushed INTEGER DEFAULT 0,
                is_in_digest INTEGER DEFAULT 0,
                FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feed_filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(feed_id, keyword),
                FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS countdown_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target_date TEXT NOT NULL,
                remark TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor = conn.execute("PRAGMA table_info(countdown_targets)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        if "remark" not in existing_cols:
            conn.execute("ALTER TABLE countdown_targets ADD COLUMN remark TEXT DEFAULT ''")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        conn.commit()

# ----------------- 关键词过滤逻辑 -----------------
def is_title_blocked(feed_id: int, title: str, conn: sqlite3.Connection) -> bool:
    if not title:
        return False
    filters_list = conn.execute(
        "SELECT keyword FROM feed_filters WHERE feed_id = ?", (feed_id,)
    ).fetchall()
    title_lower = title.lower()
    for row in filters_list:
        kw = row["keyword"].strip().lower()
        if kw and kw in title_lower:
            return True
    return False

# ----------------- 网络拉取与解析 -----------------
async def fetch_feed(url: str, timeout: float = 12.0):
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                if resp.status_code == 403:
                    return None, "HTTP 403 Forbidden（被目标防爬拦截）"
                return None, f"HTTP {resp.status_code} ({resp.reason_phrase})"
            
            feed = await asyncio.to_thread(feedparser.parse, resp.content)
            if not feed.entries and not getattr(feed.feed, "title", None):
                return None, "返回内容不是标准的 RSS/Atom XML 结构。"
            return feed, None
    except httpx.TimeoutException:
        return None, "请求超时，目标服务器未能在限时内响应。"
    except Exception as e:
        return None, f"网络请求异常: {str(e)}"

def parse_entry_datetime(entry, fallback_now: datetime) -> tuple[datetime, bool]:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t_struct = getattr(entry, attr, None)
        if t_struct:
            try:
                dt = datetime(*t_struct[:6], tzinfo=ZoneInfo("UTC")).astimezone(TIMEZONE)
                return dt, True
            except Exception:
                pass
    return fallback_now, False

# ----------------- 主人博客状态侦测 -----------------
async def get_master_blog_stats() -> dict:
    now = datetime.now(TIMEZONE)
    stats = {
        "days": -1,
        "latest_title": "",
        "week_count": 0,
        "month_count": 0,
        "year_count": 0
    }
    if not MASTER_BLOG_RSS:
        return stats
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers={"User-Agent": DEFAULT_USER_AGENT}) as client:
            resp = await client.get(MASTER_BLOG_RSS)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                if items:
                    first = items[0]
                    title_elem = first.find("title")
                    pubdate_elem = first.find("pubDate")
                    if title_elem is not None and title_elem.text:
                        stats["latest_title"] = title_elem.text.strip()
                    if pubdate_elem is not None and pubdate_elem.text:
                        pub_dt = parsedate_to_datetime(pubdate_elem.text.strip())
                        now_utc = datetime.now(dt_module.timezone.utc)
                        stats["days"] = max(0, (now_utc.date() - pub_dt.date()).days)
                for it in items:
                    p_elem = it.find("pubDate")
                    if p_elem is not None and p_elem.text:
                        try:
                            p_dt = parsedate_to_datetime(p_elem.text.strip())
                            delta_days = (now.date() - p_dt.date()).days
                            if 0 <= delta_days <= 7:
                                stats["week_count"] += 1
                            if p_dt.year == now.year and p_dt.month == now.month:
                                stats["month_count"] += 1
                            if p_dt.year == now.year:
                                stats["year_count"] += 1
                        except Exception:
                            pass
    except Exception as e:
        print(f"[Master Blog Stats Error] {e}")
    return stats

# ----------------- 节假日与倒数/历程系统 (A1) -----------------
async def get_next_holiday() -> tuple[str, int]:
    now = datetime.now(TIMEZONE).date()
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            resp = await client.get("https://timor.tech/api/holiday/next")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 0 and data.get("holiday"):
                    name = data["holiday"].get("name", "节假日")
                    h_date_str = data["holiday"].get("date")
                    if h_date_str:
                        h_date = datetime.strptime(h_date_str, "%Y-%m-%d").date()
                        days = (h_date - now).days
                        if days >= 0:
                            return name, days
    except Exception as e:
        print(f"[Holiday API Error] {e}")
        
    curr_year = now.year
    fixed_holidays = [
        ("元旦", f"{curr_year}-01-01"),
        ("春节", f"{curr_year}-02-10"),
        ("清明节", f"{curr_year}-04-04"),
        ("劳动节", f"{curr_year}-05-01"),
        ("端午节", f"{curr_year}-06-19"),
        ("中秋节", f"{curr_year}-09-25"),
        ("国庆节", f"{curr_year}-10-01"),
        ("元旦", f"{curr_year + 1}-01-01"),
        ("春节", f"{curr_year + 1}-01-29"),
    ]
    for name, date_str in fixed_holidays:
        try:
            h_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if h_date >= now:
                return name, (h_date - now).days
        except Exception:
            continue
    return "元旦", (datetime(curr_year + 1, 1, 1).date() - now).days

def get_all_targets() -> tuple[list[dict], list[dict]]:
    """获取所有倒数与历程：返回 (upcoming, passed)"""
    now = datetime.now(TIMEZONE).date()
    with get_db() as conn:
        rows = conn.execute("SELECT id, title, target_date, COALESCE(remark, '') AS remark FROM countdown_targets ORDER BY target_date ASC").fetchall()
    
    upcoming = []
    passed = []
    for r in rows:
        try:
            t_date = datetime.strptime(r["target_date"], "%Y-%m-%d").date()
            diff = (t_date - now).days
            item = {
                "id": r["id"],
                "title": r["title"],
                "target_date": r["target_date"],
                "remark": r["remark"],
                "days": diff
            }
            if diff >= 0:
                upcoming.append(item)
            else:
                item["passed_days"] = abs(diff)
                passed.append(item)
        except Exception:
            continue
            
    # 过期历程按最近过去的排在前面
    passed.sort(key=lambda x: x["days"], reverse=True)
    return upcoming, passed

def parse_target_date(date_str: str) -> tuple[str | None, str | None]:
    now = datetime.now(TIMEZONE).date()
    s = date_str.replace("月", "-").replace("日", "").replace(".", "-").replace("/", "-").strip()
    parts = s.split("-")
    try:
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            m, d = int(parts[0]), int(parts[1])
            target_this_year = datetime(now.year, m, d).date()
            y = now.year + 1 if target_this_year < now else now.year
        else:
            return None, "日期格式不支持，请使用如 2026-11-14 或 11-14"
        target_date = datetime(y, m, d).date()
        return target_date.strftime("%Y-%m-%d"), None
    except Exception as e:
        return None, f"日期解析失败: {e}"

# ----------------- 鉴权校验 -----------------
async def auth_check(update: Update) -> bool:
    user = update.effective_user
    if not user or user.id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text("未授权访问。")
        return False
    return True

# ----------------- 菜单与帮助 -----------------
HELP_TEXT = (
    "<b>NewsFlash 指令与功能完整指南</b>\n\n"
    "<b>一、 晚报与周期特刊</b>\n"
    "• <code>/digest</code>（或 <code>/daily</code>）\n"
    "  随时手动生成今日晚报预览。\n\n"
    "• <code>/weekly</code>\n"
    "  预览周度特刊（每周日晚 22:00 自动触发）。\n\n"
    "• <code>/monthly</code>\n"
    "  预览月度特刊（每月最后一天晚 22:00 自动触发）。\n\n"
    "• <code>/annual</code>\n"
    "  预览年度史册特刊（每年 12 月 31 日晚 22:00 自动触发）。\n\n"
    "<b>二、 倒数日与历程管理（A1）</b>\n"
    "• <code>/target &lt;日期&gt; &lt;事项名称&gt;</code>\n"
    "  添加一个重要日子目标（支持完整年份，到期后自动沉淀为历程记事）。\n"
    "  <i>例：<code>/target 2026-11-14 计算机考试</code> 或 <code>/target 12-12 英语四级</code></i>\n\n"
    "• <code>/targets</code>\n"
    "  查看进行中的【未来征途】与已度过的【历程记事】双分区看板。\n\n"
    "• <code>/deltarget &lt;编号&gt;</code>\n"
    "  从数据库中彻底移除指定的日程或历程记录。\n\n"
    "<b>三、 订阅管理</b>\n"
    "• <code>/add &lt;URL&gt;</code> - 添加 RSS/Atom 源\n"
    "• <code>/list</code> - 查看订阅列表（主人博客永远排第 1 位）\n"
    "• <code>/del &lt;编号&gt;</code> - 取消指定订阅\n"
    "• <b>直接发送 .opml 文件</b> - 并发探测连通性并批量导入\n"
    "• <code>/export</code> - 导出标准 .opml 文件\n"
    "• <code>/export_skill</code> - 一键打包导出包含当前订阅、33人设与屏蔽词的复刻 Skill 压缩包\n\n"
    "<b>四、 关键词屏蔽</b>\n"
    "• <code>/block &lt;源编号&gt; &lt;关键词...&gt;</code> - 添加标题屏蔽词\n"
    "• <code>/blocklist</code> - 查看屏蔽词列表\n"
    "• <code>/unblock &lt;规则ID&gt;</code> - 解除屏蔽词\n\n"
    "<i>全天静默后台轮询采集；每晚 22:00 准时聚合推送精编长报。</i>"
)

def build_menu_keyboard():
    """纯文字高质感按钮，无任何特殊符号或 Emoji"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("订阅列表", callback_data="menu_list"),
            InlineKeyboardButton("预览日报", callback_data="menu_digest"),
        ],
        [
            InlineKeyboardButton("预览周报", callback_data="menu_weekly"),
            InlineKeyboardButton("预览月报", callback_data="menu_monthly"),
        ],
        [
            InlineKeyboardButton("预览年报", callback_data="menu_annual"),
            InlineKeyboardButton("倒数管理", callback_data="menu_targets"),
        ],
        [
            InlineKeyboardButton("屏蔽过滤", callback_data="menu_blocklist"),
            InlineKeyboardButton("导出 OPML", callback_data="menu_export"),
        ],
        [
            InlineKeyboardButton("导出 Skill", callback_data="menu_export_skill"),
            InlineKeyboardButton("指令指南", callback_data="menu_help"),
        ]
    ])

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    welcome = (
        "<b>NewsFlash 控制中心</b>\n\n"
        "主人晚上好！系统已就绪，正在全天静默采集中，每晚 22:00 会准时为主人送达精编晚报喵~\n\n"
        "点击下方按钮进行快捷操作，或点击左下角 <code>Menu</code> 查看指令列表："
    )
    await update.effective_message.reply_text(welcome, parse_mode=ParseMode.HTML, reply_markup=build_menu_keyboard())

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text("<b>NewsFlash 控制中心</b>", parse_mode=ParseMode.HTML, reply_markup=build_menu_keyboard())

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)

# ----------------- 订阅基础指令 -----------------
async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args:
        await update.effective_message.reply_text("格式错误，请使用：<code>/add https://example.com/feed.xml</code>", parse_mode=ParseMode.HTML)
        return
    url = context.args[0].strip()
    msg = await update.effective_message.reply_text("正在探测订阅源...")
    
    feed, err = await fetch_feed(url)
    if err:
        await msg.edit_text(f"无法添加该订阅源喵\n\n原因：<code>{html.escape(err)}</code>", parse_mode=ParseMode.HTML)
        return
    
    title = getattr(feed.feed, "title", url).strip()
    now = datetime.now(TIMEZONE)
    since_24h = now - timedelta(days=1)

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO feeds (title, url) VALUES (?, ?)", (title, url))
            feed_id = cur.lastrowid
            
            inserted_count = 0
            for entry in feed.entries:
                link = getattr(entry, "link", "").strip()
                art_title = getattr(entry, "title", "无标题").strip()
                guid = getattr(entry, "id", link) or link
                if not link or not guid:
                    continue
                pub_dt, _ = parse_entry_datetime(entry, now)
                if pub_dt >= since_24h:
                    if is_title_blocked(feed_id, art_title, conn):
                        continue
                    try:
                        cur.execute("""
                            INSERT OR IGNORE INTO articles (feed_id, title, link, guid, published_at, is_pushed, is_in_digest)
                            VALUES (?, ?, ?, ?, ?, 0, 0)
                        """, (feed_id, art_title, link, guid, pub_dt.strftime("%Y-%m-%d %H:%M:%S")))
                        if cur.rowcount > 0:
                            inserted_count += 1
                    except Exception:
                        pass
            conn.commit()

        await msg.edit_text(
            f"成功添加订阅源喵！\n\n"
            f"<b>[{feed_id}]</b> {html.escape(title)}\n"
            f"<code>{url}</code>\n\n"
            f"<i>已同步存入过去 24 小时内的 {inserted_count} 篇最新文章，将在今晚 22:00 晚报中送达。</i>",
            parse_mode=ParseMode.HTML
        )
    except sqlite3.IntegrityError:
        await msg.edit_text("该订阅源已经存在于列表中，无需重复添加喵。")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    with get_db() as conn:
        feeds = conn.execute("SELECT id, title, url FROM feeds ORDER BY id ASC").fetchall()
        
    if not feeds:
        await update.effective_message.reply_text("当前暂无任何订阅，发送 <code>/add &lt;URL&gt;</code> 或直接发送 <code>.opml</code> 文件开始添加喵。", parse_mode=ParseMode.HTML)
        return
    
    lines = ["<b>已订阅博客列表：</b>\n"]
    for f in feeds:
        if f["id"] == 1 or (MASTER_BLOG_URL and MASTER_BLOG_URL.lower() in f["url"].lower()):
            lines.append(f"<b>[{f['id']}]</b> {html.escape(f['title'])} <i>(主人博客)</i>\n<code>{f['url']}</code>")
        else:
            lines.append(f"<b>[{f['id']}]</b> {html.escape(f['title'])}\n<code>{f['url']}</code>")
            
    await update.effective_message.reply_text("\n\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def cmd_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args:
        await update.effective_message.reply_text("格式错误，请使用：<code>/del &lt;编号&gt;</code>（编号可通过 /list 查看）", parse_mode=ParseMode.HTML)
        return
    feed_id = context.args[0].strip()
    with get_db() as conn:
        conn.execute("DELETE FROM feed_filters WHERE feed_id = ?", (feed_id,))
        conn.execute("DELETE FROM articles WHERE feed_id = ?", (feed_id,))
        res = conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
        conn.commit()
        if res.rowcount > 0:
            await update.effective_message.reply_text(f"已移除编号为 <code>{feed_id}</code> 的订阅源及其过滤规则喵。", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text("未找到该编号的订阅源，请发送 <code>/list</code> 核对编号喵。", parse_mode=ParseMode.HTML)

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    with get_db() as conn:
        feeds = conn.execute("SELECT title, url FROM feeds ORDER BY id ASC").fetchall()
    
    if not feeds:
        await update.effective_message.reply_text("当前没有订阅，无需导出喵。")
        return
    
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    title_elem = ET.SubElement(head, "title")
    title_elem.text = "NewsFlash RSS Subscriptions"
    date_elem = ET.SubElement(head, "dateCreated")
    date_elem.text = datetime.now(TIMEZONE).strftime("%a, %d %b %Y %H:%M:%S %z")
    
    body = ET.SubElement(root, "body")
    outline_group = ET.SubElement(body, "outline", text="Feeds", title="Feeds")
    
    for f in feeds:
        ET.SubElement(
            outline_group, "outline",
            type="rss",
            text=f["title"],
            title=f["title"],
            xmlUrl=f["url"],
            htmlUrl=""
        )
    
    opml_bytes = io.BytesIO(ET.tostring(root, encoding="utf-8", xml_declaration=True))
    filename = f"subscriptions_{datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')}.opml"
    
    await update.effective_message.reply_document(
        document=opml_bytes,
        filename=filename,
        caption="这是导出的标准 .opml 订阅文件，可导入任意第三方 RSS 阅读器喵。",
        parse_mode=ParseMode.HTML
    )

# ----------------- 倒数日与历程记事指令 (A1) -----------------
async def cmd_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args or len(context.args) < 2:
        await update.effective_message.reply_text(
            "格式错误，请使用：<code>/target &lt;日期&gt; &lt;事项名称&gt; [| 备注内容]</code>\n"
            "<i>示例：<code>/target 2026-11-14 计算机考试 | 提前打印准考证</code></i>\n"
            "<i>或者：<code>/target 12-12 英语四级 备注: 带听力耳机</code></i>",
            parse_mode=ParseMode.HTML
        )
        return
        
    date_str = context.args[0].strip()
    raw_rest = " ".join(context.args[1:]).strip()
    
    remark = ""
    if "|" in raw_rest:
        parts = raw_rest.split("|", 1)
        title = parts[0].strip()
        remark = parts[1].strip()
    elif "备注:" in raw_rest:
        parts = raw_rest.split("备注:", 1)
        title = parts[0].strip()
        remark = parts[1].strip()
    elif "备注：" in raw_rest:
        parts = raw_rest.split("备注：", 1)
        title = parts[0].strip()
        remark = parts[1].strip()
    elif "附:" in raw_rest or "附：" in raw_rest:
        sep = "附:" if "附:" in raw_rest else "附："
        parts = raw_rest.split(sep, 1)
        title = parts[0].strip()
        remark = parts[1].strip()
    else:
        title = raw_rest
        
    target_date, err = parse_target_date(date_str)
    if err:
        await update.effective_message.reply_text(err, parse_mode=ParseMode.HTML)
        return
        
    now = datetime.now(TIMEZONE).date()
    t_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    diff_days = (t_date - now).days
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO countdown_targets (title, target_date, remark) VALUES (?, ?, ?)", (title, target_date, remark))
        conn.commit()
        new_id = cur.lastrowid
        
    if diff_days >= 0:
        desc = f"倒计时 <b>{diff_days}</b> 天"
    else:
        desc = f"历程记事 · 距今已过 <b>{abs_val}</b> 天".replace("abs_val", str(abs(diff_days)))
        
    msg_lines = [
        f"已成功为主人记入日程看板：",
        f"<b>[{new_id}] {html.escape(title)}</b> · <code>{target_date}</code>（{desc}）"
    ]
    if remark:
        msg_lines.append(f"<b>备注：</b>{html.escape(remark)}")
    msg_lines.append("喵~")
    
    await update.effective_message.reply_text("\n".join(msg_lines), parse_mode=ParseMode.HTML)

async def cmd_memo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """直接发送信息替换或清空指定目标的备注"""
    if not await auth_check(update): return
    if not context.args:
        await update.effective_message.reply_text(
            "<b>目标备注管理</b>\n\n"
            "• 设置/直接替换备注：\n"
            "  <code>/memo &lt;编号&gt; &lt;新备注内容&gt;</code>\n"
            "  <i>例：<code>/memo 1 考点在东校区302教室</code></i>\n\n"
            "• 清空某项备注：\n"
            "  <code>/memo &lt;编号&gt;</code>\n\n"
            "<i>提示：目标编号可通过 <code>/targets</code> 指令查阅。</i>",
            parse_mode=ParseMode.HTML
        )
        return
        
    t_id_str = context.args[0].strip()
    try:
        t_id = int(t_id_str)
    except ValueError:
        await update.effective_message.reply_text("目标编号必须为纯数字，请核对后重试喵。", parse_mode=ParseMode.HTML)
        return
        
    new_remark = " ".join(context.args[1:]).strip() if len(context.args) > 1 else ""
    
    with get_db() as conn:
        row = conn.execute("SELECT id, title, target_date FROM countdown_targets WHERE id = ?", (t_id,)).fetchone()
        if not row:
            await update.effective_message.reply_text(f"未找到编号为 <code>{t_id}</code> 的目标，请发送 <code>/targets</code> 核对编号喵。", parse_mode=ParseMode.HTML)
            return
            
        conn.execute("UPDATE countdown_targets SET remark = ? WHERE id = ?", (new_remark, t_id))
        conn.commit()
        
    if new_remark:
        await update.effective_message.reply_text(
            f"已成功为事项 <b>[{t_id}] {html.escape(row['title'])}</b> 替换更新备注：\n"
            f"<code>{html.escape(new_remark)}</code>喵~",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.effective_message.reply_text(
            f"已成功清空事项 <b>[{t_id}] {html.escape(row['title'])}</b> 的备注喵。",
            parse_mode=ParseMode.HTML
        )

async def cmd_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    upcoming, passed = get_all_targets()
    if not upcoming and not passed:
        await update.effective_message.reply_text(
            "当前日程看板空空如也喵。\n"
            "发送 <code>/target &lt;日期&gt; &lt;事项名称&gt;</code> 即可添加（如 <code>/target 2026-11-14 计算机考试</code>）。",
            parse_mode=ParseMode.HTML
        )
        return
        
    lines = ["<b>日程与历程双分区看板：</b>\n"]
    if upcoming:
        lines.append("<b>未来征途：</b>")
        for t in upcoming:
            t_line = f"• <b>[{t['id']}]</b> {html.escape(t['title'])} · <code>{t['target_date']}</code>（倒计时 <b>{t['days']}</b> 天）"
            if t.get("remark") and t["remark"].strip():
                t_line += f"\n  <i>备注: {html.escape(t['remark'].strip())}</i>"
            lines.append(t_line)
            
    if passed:
        if upcoming:
            lines.append("")
        lines.append("<b>历程记事：</b>")
        for t in passed:
            t_line = f"• <b>[{t['id']}]</b> {html.escape(t['title'])} · <code>{t['target_date']}</code>（距今已过 <b>{t['passed_days']}</b> 天）"
            if t.get("remark") and t["remark"].strip():
                t_line += f"\n  <i>备注: {html.escape(t['remark'].strip())}</i>"
            lines.append(t_line)
        
    lines.append("\n<i>彻底移除指令：<code>/deltarget &lt;编号&gt;</code></i>")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def cmd_deltarget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args:
        await update.effective_message.reply_text("格式错误，请使用：<code>/deltarget &lt;编号&gt;</code>（编号可通过 /targets 查看）", parse_mode=ParseMode.HTML)
        return
    t_id = context.args[0].strip()
    with get_db() as conn:
        res = conn.execute("DELETE FROM countdown_targets WHERE id = ?", (t_id,))
        conn.commit()
        if res.rowcount > 0:
            await update.effective_message.reply_text(f"已从看板中移除编号为 <code>{t_id}</code> 的记录喵。", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text("未找到该编号的记录，请发送 <code>/targets</code> 核对编号喵。", parse_mode=ParseMode.HTML)

# ----------------- 动态导出 1:1 复刻 Skill 压缩包 -----------------
async def cmd_export_skill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    status_msg = await update.effective_message.reply_text("正在为主人实时打包最新 Skill 归档包...")
    
    with get_db() as conn:
        feeds = conn.execute("SELECT id, title, url FROM feeds ORDER BY id ASC").fetchall()
        filters_rows = conn.execute("""
            SELECT ff.id, ff.feed_id, f.title AS feed_title, ff.keyword 
            FROM feed_filters ff 
            JOIN feeds f ON ff.feed_id = f.id
            ORDER BY ff.feed_id ASC, ff.id ASC
        """).fetchall()
    
    root = ET.Element("opml", version="2.0")
    head = ET.SubElement(root, "head")
    title_elem = ET.SubElement(head, "title")
    title_elem.text = "NewsFlash Subscriptions Baseline"
    date_elem = ET.SubElement(head, "dateCreated")
    date_elem.text = datetime.now(TIMEZONE).strftime("%a, %d %b %Y %H:%M:%S %z")
    body = ET.SubElement(root, "body")
    outline_group = ET.SubElement(body, "outline", text="Feeds", title="Feeds")
    for f in feeds:
        ET.SubElement(
            outline_group, "outline",
            type="rss",
            text=f["title"],
            title=f["title"],
            xmlUrl=f["url"],
            htmlUrl=""
        )
    opml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
    
    filters_data = []
    for r in filters_rows:
        filters_data.append({
            "feed_id": r["feed_id"],
            "feed_title": r["feed_title"],
            "keyword": r["keyword"]
        })
    filters_json_str = json.dumps(filters_data, ensure_ascii=False, indent=2)
    
    filter_lines = []
    grouped_filters = {}
    for r in filters_rows:
        f_title = r["feed_title"]
        if f_title not in grouped_filters:
            grouped_filters[f_title] = []
        grouped_filters[f_title].append(r["keyword"])
    for f_title, kws in grouped_filters.items():
        filter_lines.append(f"- Target Feed: `{f_title}`\n  Blocked Keywords: `{', '.join(kws)}`")
    filters_md_block = "\n".join(filter_lines) if filter_lines else "- 当前未设置任何屏蔽词"

    skill_md = f"""---
name: tg-rss-digest-bot
description: Build, deploy, and maintain an automated Telegram RSS evening digest bot with daytime silence, Master-companion tone, 7-day adaptive blog status tracking, retroactive title keyword filtering, 33 personas, countdown and milestone engine, Telegra.ph Instant View, and Master blog ID=1 top priority.
---

# Telegram RSS Digest Bot Builder

A comprehensive engineering guide for an AI Agent to build, deploy, and configure a personalized Telegram RSS Subscription & Evening Digest Bot 1:1 from scratch.

## 1. System Architecture & Prerequisites
- **OS**: FreeBSD 14+ / Linux / Docker
- **Runtime**: Python 3.11+
- **Database**: SQLite3
- **Dependencies**: `python-telegram-bot[job-queue]>=20.0`, `httpx>=0.24.0`, `feedparser>=6.0.0`, `beautifulsoup4>=4.12.0`, `tzdata`

## 2. Core Business Rules & Constraints
1. **Master's Blog Dedicated ID = 1 & Absolute Top Priority**:
   - Master's blog MUST strictly be registered as `id = 1` in the database `feeds` table.
   - All other external feeds follow sequentially from `id = 2, 3, 4...`.
2. **Strict Daytime Silence**:
   - Background polling every 30 minutes without sending daytime popups.
3. **Master Personalization & 33 Companion Personas**:
   - MUST address user exclusively as "主人" (Master). NEVER use real names or "蒸蛋".
   - 33 distinct companion personas rotate dynamically for greetings, countdowns, and bedtime whispers.
4. **Countdown & Milestone Engine (A1)**:
   - Full dates formatted with year (`YYYY-MM-DD`).
   - Upcoming targets count down; passed milestones are permanently retained ("距今已过 X 天").
5. **Telegra.ph Instant View + Telegram Single Card (C1)**:
   - Full daily digest is automatically formatted and published to Telegra.ph via official API.
   - Telegra.ph content strictly holds past 24 hours of RSS articles.
   - Telegram in-chat digest stays strictly within 1 single, elegant card without highlights or statistics clutter.
6. **Strict Zero-Emoji UI & Typography**:
   - 100% pure plain text across all buttons and messages.

## 3. Subscriptions Baseline
```xml
{opml_str}
```

## 4. Active Keyword Filters
{filters_md_block}
"""

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("SKILL.md", skill_md.encode("utf-8"))
        zip_file.writestr("subscriptions.opml", opml_str.encode("utf-8"))
        zip_file.writestr("feed_filters.json", filters_json_str.encode("utf-8"))
        
        personas = load_personas()
        zip_file.writestr("personas.json", json.dumps(personas, ensure_ascii=False, indent=2).encode("utf-8"))

    zip_buffer.seek(0)
    now_str = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    filename = f"tg_rss_bot_skill_{now_str}.zip"
    
    await status_msg.delete()
    await update.effective_message.reply_document(
        document=zip_buffer,
        filename=filename,
        caption=(
            "已为主人完成 1:1 完整复刻包打包喵！\n\n"
            "压缩包内包含：\n"
            "• <code>SKILL.md</code>（核心系统构建指令与工程约束）\n"
            "• <code>subscriptions.opml</code>（当前全部订阅基准）\n"
            "• <code>feed_filters.json</code>（已生效的关键词过滤规则）\n"
            "• <code>personas.json</code>（33 种精编伴侣人设库）\n\n"
            "直接发给任意 Agent 即可 1:1 原样复刻所有功能与状态喵~"
        ),
        parse_mode=ParseMode.HTML
    )

# ----------------- 关键词过滤指令 -----------------
async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args or len(context.args) < 2:
        await update.effective_message.reply_text(
            "格式错误，请使用：<code>/block &lt;源编号&gt; &lt;关键词1&gt; [关键词2...]</code>\n"
            "<i>(编号可通过 /list 查看，可一次输入多个关键词，用空格隔开)</i>",
            parse_mode=ParseMode.HTML
        )
        return
    feed_id_str = context.args[0].strip()
    keywords = [kw.strip() for kw in context.args[1:] if kw.strip()]
    if not keywords:
        await update.effective_message.reply_text("请输入至少一个有效的屏蔽关键词喵。")
        return

    with get_db() as conn:
        feed = conn.execute("SELECT id, title FROM feeds WHERE id = ?", (feed_id_str,)).fetchone()
        if not feed:
            await update.effective_message.reply_text(f"未找到编号为 <code>{feed_id_str}</code> 的订阅源，请发送 <code>/list</code> 核对编号喵。", parse_mode=ParseMode.HTML)
            return

        added, existed = [], []
        for kw in keywords:
            try:
                conn.execute("INSERT INTO feed_filters (feed_id, keyword) VALUES (?, ?)", (feed["id"], kw))
                added.append(kw)
            except sqlite3.IntegrityError:
                existed.append(kw)
                
        purged_count = 0
        if added:
            for kw in added:
                res = conn.execute(
                    "DELETE FROM articles WHERE feed_id = ? AND lower(title) LIKE lower(?)",
                    (feed["id"], f"%{kw}%")
                )
                purged_count += res.rowcount
        conn.commit()

    reply_parts = [f"针对「<b>{html.escape(feed['title'])}</b>」的屏蔽规则更新结果："]
    if added:
        reply_parts.append(f"• 成功添加屏蔽词：<code>{html.escape(', '.join(added))}</code>")
    if existed:
        reply_parts.append(f"• 已存在跳过：<code>{html.escape(', '.join(existed))}</code>")
    if purged_count > 0:
        reply_parts.append(f"<i>(已追溯清理数据库中已缓存的 {purged_count} 篇历史包含屏蔽词文章)</i>")
    await update.effective_message.reply_text("\n".join(reply_parts), parse_mode=ParseMode.HTML)

async def cmd_blocklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    with get_db() as conn:
        feeds = conn.execute("SELECT id, title FROM feeds ORDER BY id ASC").fetchall()
        rows = conn.execute("SELECT id, feed_id, keyword FROM feed_filters ORDER BY feed_id ASC, id ASC").fetchall()
        
    feed_map = {f["id"]: f["title"] for f in feeds}
    grouped = {}
    total_rules = 0
    for r in rows:
        fid = r["feed_id"]
        if fid not in grouped:
            grouped[fid] = []
        grouped[fid].append((r["id"], r["keyword"]))
        total_rules += 1

    sections = []
    for fid in sorted(grouped.keys()):
        f_title = feed_map.get(fid, f"未知源 (ID {fid})")
        kw_items = [f"<code>{html.escape(kw)}</code>(ID:{rid})" for rid, kw in grouped[fid]]
        sections.append(f"<b>[{fid}] {html.escape(f_title)}</b>\n  " + "，".join(kw_items))
    
    if total_rules == 0:
        await update.effective_message.reply_text(
            "当前未对任何订阅源设置屏蔽词喵。\n使用 <code>/block &lt;源编号&gt; &lt;关键词&gt;</code> 即可添加。",
            parse_mode=ParseMode.HTML
        )
        return
    
    msg_body = "<b>标题关键词屏蔽列表：</b>\n\n" + "\n\n".join(sections)
    msg_body += "\n\n<i>删除规则：<code>/unblock &lt;规则ID&gt;</code> 或 <code>/unblock &lt;源编号&gt; &lt;关键词&gt;</code></i>"
    await update.effective_message.reply_text(msg_body, parse_mode=ParseMode.HTML)

async def cmd_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    if not context.args:
        await update.effective_message.reply_text(
            "格式错误，请使用：\n"
            "• <code>/unblock &lt;规则ID&gt;</code>\n"
            "• <code>/unblock &lt;源编号&gt; &lt;关键词&gt;</code>\n"
            "<i>(规则 ID 可通过 <code>/blocklist</code> 查看)</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    with get_db() as conn:
        if len(context.args) == 1 and context.args[0].isdigit():
            rule_id = int(context.args[0])
            row = conn.execute("""
                SELECT ff.keyword, f.title 
                FROM feed_filters ff 
                JOIN feeds f ON ff.feed_id = f.id 
                WHERE ff.id = ?
            """, (rule_id,)).fetchone()
            if not row:
                await update.effective_message.reply_text(f"未找到 ID 为 <code>{rule_id}</code> 的屏蔽规则喵。", parse_mode=ParseMode.HTML)
                return
            conn.execute("DELETE FROM feed_filters WHERE id = ?", (rule_id,))
            conn.commit()
            await update.effective_message.reply_text(
                f"已解除「<b>{html.escape(row['title'])}</b>」的屏蔽词：<code>{html.escape(row['keyword'])}</code> 喵~",
                parse_mode=ParseMode.HTML
            )
        elif len(context.args) >= 2:
            feed_id_str = context.args[0]
            kw = context.args[1].strip()
            res = conn.execute("DELETE FROM feed_filters WHERE feed_id = ? AND keyword = ?", (feed_id_str, kw))
            conn.commit()
            if res.rowcount > 0:
                await update.effective_message.reply_text(f"已成功移除该源的屏蔽词 <code>{html.escape(kw)}</code> 喵~", parse_mode=ParseMode.HTML)
            else:
                await update.effective_message.reply_text("未找到匹配的屏蔽词，请主人核对编号与关键词喵。", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text("参数解析失败，请输入规则 ID 或源编号与关键词喵。")

# ----------------- OPML 文件并发导入 -----------------
async def handle_opml_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    doc = update.effective_message.document
    if not doc: return
    filename = doc.file_name or ""
    if not (filename.endswith(".opml") or filename.endswith(".xml") or doc.mime_type == "text/x-opml"):
        return
        
    status_msg = await update.effective_message.reply_text(f"检测到 OPML 文件「{html.escape(filename)}」，正在下载并解析喵...")
    try:
        file = await context.bot.get_file(doc.file_id)
        content_bytes = await file.download_as_bytearray()
        root = ET.fromstring(content_bytes)
        
        extracted_feeds = []
        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl") or outline.get("xmlurl") or outline.get("url")
            if xml_url and xml_url.startswith(("http://", "https://")):
                title = outline.get("title") or outline.get("text") or xml_url
                extracted_feeds.append({"title": title.strip(), "url": xml_url.strip()})
                
        if not extracted_feeds:
            await status_msg.edit_text("未能在该文件中找到任何有效的 RSS/Atom 订阅节点喵。")
            return

        with get_db() as conn:
            existing_urls = {row["url"] for row in conn.execute("SELECT url FROM feeds").fetchall()}

        to_probe = []
        already_in_db = 0
        for f in extracted_feeds:
            if f["url"] in existing_urls:
                already_in_db += 1
            else:
                to_probe.append(f)

        await status_msg.edit_text(
            f"共解析出 {len(extracted_feeds)} 个源。\n"
            f"• 已在库中：{already_in_db} 个\n"
            f"• 正在并发探测连通性：{len(to_probe)} 个，请主人稍候片刻喵..."
        )

        sem = asyncio.Semaphore(5)
        async def probe_single(item):
            async with sem:
                feed, err = await fetch_feed(item["url"], timeout=10.0)
                if feed and not err:
                    real_title = getattr(feed.feed, "title", item["title"]).strip()
                    return {"url": item["url"], "title": real_title, "valid": True, "feed_obj": feed}
                else:
                    return {"url": item["url"], "title": item["title"], "valid": False, "err": err}

        probe_results = await asyncio.gather(*(probe_single(item) for item in to_probe))
        
        success_list = []
        failed_list = []
        now = datetime.now(TIMEZONE)
        since_24h = now - timedelta(days=1)

        with get_db() as conn:
            cur = conn.cursor()
            for r in probe_results:
                if r["valid"]:
                    try:
                        cur.execute("INSERT INTO feeds (title, url) VALUES (?, ?)", (r["title"], r["url"]))
                        feed_id = cur.lastrowid
                        success_list.append(r["title"])
                        feed_obj = r["feed_obj"]
                        for entry in feed_obj.entries:
                            link = getattr(entry, "link", "").strip()
                            art_title = getattr(entry, "title", "无标题").strip()
                            guid = getattr(entry, "id", link) or link
                            if not link or not guid: continue
                            pub_dt, _ = parse_entry_datetime(entry, now)
                            if pub_dt >= since_24h:
                                try:
                                    cur.execute("""
                                        INSERT OR IGNORE INTO articles (feed_id, title, link, guid, published_at, is_pushed, is_in_digest)
                                        VALUES (?, ?, ?, ?, ?, 0, 0)
                                    """, (feed_id, art_title, link, guid, pub_dt.strftime("%Y-%m-%d %H:%M:%S")))
                                except Exception: pass
                    except sqlite3.IntegrityError:
                        pass
                else:
                    failed_list.append((r["title"], r["err"]))
            conn.commit()

        report = [
            f"<b>OPML 批量导入结果报告：</b>",
            f"• 成功入库：<b>{len(success_list)}</b> 个源",
            f"• 已在库中跳过：{already_in_db} 个源",
            f"• 探测失败：{len(failed_list)} 个源"
        ]
        if failed_list:
            report.append("\n<b>探测失败清单前 5 项：</b>")
            for t, e in failed_list[:5]:
                report.append(f"- {html.escape(t)}: <code>{html.escape(str(e))}</code>")
        if success_list:
            report.append("\n<i>新订阅源的最新动态已进入待发池，今晚 22:00 准时送达。</i>")
                
        await status_msg.edit_text("\n".join(report), parse_mode=ParseMode.HTML)
    except Exception as e:
        await status_msg.edit_text(f"处理文件时发生意外错误: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)

# ----------------- 交互面板回调分发 -----------------
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not await auth_check(update): return
    await query.answer()
    
    data = query.data
    if data == "menu_list":
        await cmd_list(update, context)
    elif data == "menu_digest":
        await cmd_digest(update, context)
    elif data == "menu_weekly":
        await cmd_weekly(update, context)
    elif data == "menu_monthly":
        await cmd_monthly(update, context)
    elif data == "menu_annual":
        await cmd_annual(update, context)
    elif data == "menu_targets":
        await cmd_targets(update, context)
    elif data == "menu_blocklist":
        await cmd_blocklist(update, context)
    elif data == "menu_export":
        await cmd_export(update, context)
    elif data == "menu_export_skill":
        await cmd_export_skill(update, context)
    elif data == "menu_help":
        await cmd_help(update, context)

# ----------------- 30 分钟后台静默轮询 -----------------
async def job_poll_feeds(context: ContextTypes.DEFAULT_TYPE):
    with get_db() as conn:
        feeds = conn.execute("SELECT id, title, url FROM feeds ORDER BY id ASC").fetchall()
    
    now = datetime.now(TIMEZONE)
    since_24h = now - timedelta(days=1)
    
    for f in feeds:
        try:
            feed, err = await fetch_feed(f["url"])
            if err or not feed:
                continue
                
            with get_db() as conn:
                cur = conn.cursor()
                for entry in feed.entries:
                    link = getattr(entry, "link", "").strip()
                    art_title = getattr(entry, "title", "无标题").strip()
                    guid = getattr(entry, "id", link) or link
                    if not link or not guid:
                        continue
                    pub_dt, _ = parse_entry_datetime(entry, now)
                    if pub_dt >= since_24h:
                        if is_title_blocked(f["id"], art_title, conn):
                            continue
                        try:
                            cur.execute("""
                                INSERT OR IGNORE INTO articles (feed_id, title, link, guid, published_at, is_pushed, is_in_digest)
                                VALUES (?, ?, ?, ?, ?, 0, 0)
                            """, (f["id"], art_title, link, guid, pub_dt.strftime("%Y-%m-%d %H:%M:%S")))
                        except Exception:
                            pass
                conn.commit()
        except Exception as e:
            print(f"[Polling Error] Feed {f['id']} - {f['title']}: {e}")

# ----------------- Telegra.ph 原生排版发布 -----------------
async def publish_telegraph_page(title: str, content_nodes: list[dict]) -> str | None:
    token = None
    try:
        with get_db() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = 'telegraph_token'").fetchone()
            if row:
                token = row["value"]
    except Exception:
        pass
        
    async with httpx.AsyncClient(timeout=15.0) as client:
        if not token:
            try:
                acc_resp = await client.get(
                    "https://api.telegra.ph/createAccount",
                    params={
                        "short_name": "NewsFlash",
                        "author_name": "NewsFlash",
                        "author_url": MASTER_BLOG_URL
                    }
                )
                if acc_resp.status_code == 200:
                    acc_data = acc_resp.json()
                    if acc_data.get("ok"):
                        token = acc_data["result"]["access_token"]
                        with get_db() as conn:
                            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('telegraph_token', ?)", (token,))
                            conn.commit()
            except Exception as e:
                print(f"[Telegraph CreateAccount Error] {e}")
                return None
                
        if not token:
            return None
            
        try:
            page_resp = await client.post(
                "https://api.telegra.ph/createPage",
                json={
                    "access_token": token,
                    "title": title,
                    "author_name": "NewsFlash",
                    "author_url": MASTER_BLOG_URL,
                    "content": content_nodes,
                    "return_content": False
                }
            )
            if page_resp.status_code == 200:
                page_data = page_resp.json()
                if page_data.get("ok"):
                    return page_data["result"]["url"]
        except Exception as e:
            print(f"[Telegraph CreatePage Error] {e}")
            return None
    return None

# ----------------- 晚报生成与推送调度引擎 -----------------
def format_persona_blog_status(persona: dict, stats: dict, report_type: str = "daily") -> str:
    rt = report_type
    blog_days = stats.get("days", -1)
    latest_title = stats.get("latest_title", "最新文章")
    week_count = stats.get("week_count", 0)
    month_count = stats.get("month_count", 0)
    year_count = stats.get("year_count", 0)
    now = datetime.now(TIMEZONE)
    
    if rt == "weekly":
        if week_count > 0:
            tpl = persona.get("weekly_opening_active", "周日晚风轻柔，本周主人完成 {master_week_count} 篇佳作，思维真让人着迷。")
            text = tpl.format(master_week_count=week_count)
        else:
            text = persona.get("weekly_opening_quiet", "转眼又是周日夜里，本周主人把精力留给了生活，卸下一周的疲惫吧。")
    elif rt == "monthly":
        if month_count > 0:
            tpl = persona.get("monthly_opening_active", "{month} 月末，整整一个月主人留下了 {master_month_count} 篇力作。")
            text = tpl.format(month=now.month, master_month_count=month_count)
        else:
            tpl = persona.get("monthly_opening_quiet", "{month} 月走到尾声，虽然少有动笔，但每一天都是踏实的沉淀。")
            text = tpl.format(month=now.month)
    elif rt == "annual":
        if year_count > 0:
            tpl = persona.get("annual_opening_active", "岁末长夜，{year} 年主人一共写下了 {master_year_count} 篇心血之作。")
            text = tpl.format(year=now.year, master_year_count=year_count)
        else:
            tpl = persona.get("annual_opening_quiet", "{year} 年马上画上句号，一年的坚持我全看在眼里，生活本身就是最厚重的书。")
            text = tpl.format(year=now.year)
    else: # daily
        if blog_days == 0:
            tpl = persona.get("daily_opening_active", "夜色深了，方才看见主人博客上新落下的字句（{blog_status_text}）。")
            text = tpl.format(blog_status_text=f"今日发表了《{html.escape(latest_title)}》")
        else:
            tpl = persona.get("daily_opening_quiet", "{blog_status_text}，今夜什么都不必多想，安心享受这份清静就好。")
            if blog_days > 0:
                status_desc = f"整整 {blog_days} 天未见片语"
            else:
                status_desc = "近日博客未见更新"
            text = tpl.format(blog_status_text=status_desc)

    return text

def format_persona_countdown_a1(persona: dict, holiday_name: str, holiday_days: int, upcoming: list[dict], passed: list[dict], report_type: str = "daily") -> str:
    """双分区看板流 (A1)：支持同日多任务自然融合与各周期独立台词"""
    rt = report_type
    now = datetime.now(TIMEZONE)
    
    if upcoming:
        min_days = upcoming[0]["days"]
        same_day_items = [t for t in upcoming if t["days"] == min_days]
        custom_days = min_days
        if len(same_day_items) == 1:
            custom_name = same_day_items[0]["title"]
        elif len(same_day_items) == 2:
            custom_name = f"{same_day_items[0]['title']}」与「{same_day_items[1]['title']}"
        else:
            custom_name = f"{same_day_items[0]['title']}」等 {len(same_day_items)} 项要务"
    else:
        custom_name = "眼下要务"
        custom_days = 0

    tpl = persona.get(f"{rt}_countdown_remark", "")
    try:
        main_quote = tpl.format(
            holiday_name=holiday_name,
            holiday_days=holiday_days,
            custom_name=custom_name,
            custom_days=custom_days,
            month=now.month,
            year=now.year
        )
    except Exception:
        main_quote = tpl
        
    lines = [main_quote]
    
    if upcoming or passed:
        lines.append("")
        transition_text = persona.get(f"{rt}_transition", persona.get("transition_intro", "翻开手边的随身备忘，我替主人把近期的重要事项理一理："))
        lines.append(transition_text)
        
        # 晚报看板完整展示备注（支持同日多任务紧凑与每项备注完整展开）
        if upcoming:
            lines.append("未来征途：")
            grouped_upcoming = {}
            for t in upcoming:
                d_key = (t["target_date"], t["days"])
                if d_key not in grouped_upcoming:
                    grouped_upcoming[d_key] = []
                grouped_upcoming[d_key].append(t)
                
            for (t_date, days), items in grouped_upcoming.items():
                if len(items) == 1:
                    it = items[0]
                    lines.append(f"• {t_date} (倒计时 {days} 天): {html.escape(it['title'])}")
                    if it.get("remark") and it["remark"].strip():
                        lines.append(f"  备注: {html.escape(it['remark'].strip())}")
                else:
                    titles_str = " · ".join(html.escape(it["title"]) for it in items)
                    lines.append(f"• {t_date} (倒计时 {days} 天): {titles_str}")
                    for it in items:
                        if it.get("remark") and it["remark"].strip():
                            lines.append(f"  - {html.escape(it['title'])} 备注: {html.escape(it['remark'].strip())}")
                
        if passed:
            if upcoming:
                lines.append("")
            lines.append("历程记事：")
            grouped_passed = {}
            for t in passed:
                d_key = (t["target_date"], t["passed_days"])
                if d_key not in grouped_passed:
                    grouped_passed[d_key] = []
                grouped_passed[d_key].append(t)
                
            for (t_date, p_days), items in grouped_passed.items():
                if len(items) == 1:
                    it = items[0]
                    lines.append(f"• {t_date} (距今已过 {p_days} 天): {html.escape(it['title'])}")
                    if it.get("remark") and it["remark"].strip():
                        lines.append(f"  备注: {html.escape(it['remark'].strip())}")
                else:
                    titles_str = " · ".join(html.escape(it["title"]) for it in items)
                    lines.append(f"• {t_date} (距今已过 {p_days} 天): {titles_str}")
                    for it in items:
                        if it.get("remark") and it["remark"].strip():
                            lines.append(f"  - {html.escape(it['title'])} 备注: {html.escape(it['remark'].strip())}")
                
    return "\n".join(lines)

async def send_digest_dispatch(context: ContextTypes.DEFAULT_TYPE, report_type: str = "auto", is_preview: bool = False):
    now = datetime.now(TIMEZONE)
    since_24h = now - timedelta(days=1)
    
    # 1. 自动时序判定（晋级吸收）
    if report_type == "auto":
        is_dec_31 = (now.month == 12 and now.day == 31)
        next_day = now + timedelta(days=1)
        is_last_day_of_month = (next_day.month != now.month)
        is_sunday = (now.weekday() == 6)
        
        if is_dec_31:
            rt = "annual"
        elif is_last_day_of_month:
            rt = "monthly"
        elif is_sunday:
            rt = "weekly"
        else:
            rt = "daily"
    else:
        rt = report_type

    # 2. 标题与特刊类型配置
    if rt == "weekly":
        week_num = now.isocalendar()[1]
        w_start = (now - timedelta(days=now.weekday())).strftime('%m.%d')
        w_end = (now + timedelta(days=6 - now.weekday())).strftime('%m.%d')
        title_date = f"{now.year}年第{week_num}周 ({w_start} - {w_end})"
        default_title = "NewsFlash 周度特刊 · {title_date}"
        link_prompt = "本周排版长报："
        period_name = "周报"
    elif rt == "monthly":
        title_date = f"{now.year}年{now.month}月"
        default_title = "NewsFlash 月度特刊 · {title_date}"
        link_prompt = "本月排版长报："
        period_name = "月报"
    elif rt == "annual":
        title_date = f"{now.year}年度全景"
        default_title = "NewsFlash 年度史册 · {title_date}"
        link_prompt = "年度排版长报："
        period_name = "年报"
    else:
        title_date = now.strftime('%Y年%m月%d日')
        default_title = "NewsFlash 晚间精编 · {title_date}"
        link_prompt = "今日排版长报："
        period_name = "晚报"

    # 3. 抽取 33 套人设中的一套
    personas = load_personas()
    persona = random.choice(personas) if personas else DEFAULT_FALLBACK_PERSONA
    
    title_fmt = persona.get(f"title_{rt}", default_title)
    header_title = f"<b>{title_fmt.format(title_date=title_date)}</b>"

    # 4. 获取博客状态与双分区倒数数据 (A1)
    blog_stats = await get_master_blog_stats()
    holiday_name, holiday_days = await get_next_holiday()
    upcoming_targets, passed_targets = get_all_targets()
    
    blog_status_text = format_persona_blog_status(persona, blog_stats, report_type=rt)
    countdown_text = format_persona_countdown_a1(persona, holiday_name, holiday_days, upcoming_targets, passed_targets, report_type=rt)
    
    closing_tpl = persona.get(f"{rt}_closing", persona.get("goodnight_closing", "夜深了，早些歇息吧，主人晚安。"))
    try:
        goodnight_closing = closing_tpl.format(year=now.year, month=now.month)
    except Exception:
        goodnight_closing = closing_tpl

    # 5. 提取过去 24 小时内的有效文章（恒定不变）
    with get_db() as conn:
        articles = conn.execute("""
            SELECT a.id, a.feed_id, a.title AS art_title, a.link, a.published_at,
                   f.title AS feed_title, f.url AS feed_url
            FROM articles a
            JOIN feeds f ON a.feed_id = f.id
            WHERE a.published_at >= ?
            ORDER BY a.feed_id ASC, a.published_at DESC
        """, (since_24h.strftime("%Y-%m-%d %H:%M:%S"),)).fetchall()
        
        valid_articles = [art for art in articles if not is_title_blocked(art["feed_id"], art["art_title"], conn)]
        
        if not is_preview and valid_articles:
            art_ids = [str(art["id"]) for art in valid_articles]
            conn.execute(f"UPDATE articles SET is_in_digest = 1 WHERE id IN ({','.join(art_ids)})")
            conn.commit()

    # 无文章时的空报卡片
    if not valid_articles:
        card_parts = [
            header_title,
            "",
            blog_status_text,
            "",
            "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈",
            "<b>倒数备忘：</b>",
            countdown_text,
            "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈",
            "",
            "今天关注的各博客都很安静，没有新的动态更新（或者都被主人的屏蔽词过滤掉啦）喵。",
            "",
            "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈",
            "",
            goodnight_closing
        ]
        night_empty_msg = "\n".join(card_parts)
        if is_preview:
            night_empty_msg = f"<i>[{rt.upper()} 预览]</i>\n\n" + night_empty_msg
            
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=night_empty_msg,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return

    # 按源分组
    grouped = {}
    master_articles = []
    for art in valid_articles:
        f_id = art["feed_id"]
        if f_id == 1 or (MASTER_BLOG_URL and MASTER_BLOG_URL.lower() in art["feed_url"].lower()):
            master_articles.append(art)
        if f_id not in grouped:
            grouped[f_id] = {
                "title": art["feed_title"],
                "url": art["feed_url"],
                "items": []
            }
        grouped[f_id]["items"].append(art)

    sorted_feed_items = sorted(grouped.items(), key=lambda item: item[0])

    # 6. 组装 Telegra.ph 原生排版节点（方向 3：CDT 杂志复刻级排版，纯粹资讯，典雅竖块）
    telegraph_nodes = [
        {"tag": "h4", "children": [f"NewsFlash {period_name} · 资讯精编 ({title_date})"]},
        {"tag": "p", "children": ["全网聚合 · 纯粹阅读 · 静默陪伴"]},
        {"tag": "hr"}
    ]
    
    if master_articles:
        telegraph_nodes.append({"tag": "h3", "children": ["▍ 主人专栏 · 今日动态"]})
        m_list = []
        for it in master_articles:
            try:
                pub_dt = datetime.strptime(it["published_at"], "%Y-%m-%d %H:%M:%S")
                time_str = pub_dt.strftime("%H:%M")
            except Exception:
                time_str = "--:--"
            m_list.append({"tag": "li", "children": [
                {"tag": "a", "attrs": {"href": it["link"]}, "children": [it["art_title"]]},
                f" ({time_str})"
            ]})
        telegraph_nodes.append({"tag": "ul", "children": m_list})
        telegraph_nodes.append({"tag": "hr"})

    for f_id, data in sorted_feed_items:
        feed_title_escaped = data["title"]
        telegraph_nodes.append({"tag": "h3", "children": [f"▍ [{f_id}] {feed_title_escaped} (共 {len(data['items'])} 篇)"]})
        items_nodes = []
        for it in data["items"]:
            try:
                pub_dt = datetime.strptime(it["published_at"], "%Y-%m-%d %H:%M:%S")
                time_str = pub_dt.strftime("%H:%M")
            except Exception:
                time_str = "--:--"
            items_nodes.append({
                "tag": "li",
                "children": [
                    {"tag": "a", "attrs": {"href": it["link"]}, "children": [it["art_title"]]},
                    f" ({time_str})"
                ]
            })
        telegraph_nodes.append({"tag": "ul", "children": items_nodes})
        telegraph_nodes.append({"tag": "hr"})

    telegraph_nodes.append({"tag": "p", "children": ["NewsFlash · 专属主人的高质感资讯特刊"]})

    # 发布到 Telegra.ph
    page_title = f"NewsFlash {period_name} · {title_date}"
    telegraph_url = await publish_telegraph_page(page_title, telegraph_nodes)

    # 7. 组装极致纯净的 Telegram 极简卡片 (C1 + 移除正文 URL)
    card_lines = [
        header_title,
        "",
        blog_status_text,
        "",
        "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈",
        "<b>倒数备忘：</b>",
        countdown_text,
        "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈",
        "",
        goodnight_closing
    ]

    final_card = "\n".join(card_lines)
    if is_preview:
        final_card = f"<i>[{rt.upper()} 预览]</i>\n\n" + final_card

    if telegraph_url:
        preview_opts = LinkPreviewOptions(
            url=telegraph_url,
            is_disabled=False,
            prefer_large_media=True,
            show_above_text=False
        )

        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=final_card,
            parse_mode=ParseMode.HTML,
            link_preview_options=preview_opts
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=final_card,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

# 定时调度入口
async def job_evening_digest(context: ContextTypes.DEFAULT_TYPE):
    await send_digest_dispatch(context, report_type="auto", is_preview=False)

# 手动预览指令
async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text("正在为主人生成今日晚报预览喵...")
    await send_digest_dispatch(context, report_type="daily", is_preview=True)

async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text("正在为主人生成周度特刊预览喵...")
    await send_digest_dispatch(context, report_type="weekly", is_preview=True)

async def cmd_monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text("正在为主人生成月度特刊预览喵...")
    await send_digest_dispatch(context, report_type="monthly", is_preview=True)

async def cmd_annual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await auth_check(update): return
    await update.effective_message.reply_text("正在为主人生成年度史册特刊预览喵...")
    await send_digest_dispatch(context, report_type="annual", is_preview=True)

# ----------------- 异步生命周期挂钩（注册原生菜单） -----------------
async def post_init(application: Application):
    commands = [
        BotCommand("menu", "控制中心面板"),
        BotCommand("digest", "今日晚报预览"),
        BotCommand("weekly", "周度特刊预览"),
        BotCommand("monthly", "月度特刊预览"),
        BotCommand("annual", "年度史册特刊预览"),
        BotCommand("targets", "日程与历程双分区看板"),
        BotCommand("target", "添加目标: /target 日期 事项 | 备注"),
        BotCommand("memo", "替换目标备注: /memo 编号 备注内容"),
        BotCommand("list", "已订阅博客列表"),
        BotCommand("blocklist", "关键词屏蔽列表"),
        BotCommand("export", "导出 OPML 订阅文件"),
        BotCommand("export_skill", "导出 1:1 复刻 Skill 压缩包"),
        BotCommand("help", "完整指令指南"),
    ]
    try:
        await application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        await application.bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=ADMIN_USER_ID))
        await application.bot.set_chat_menu_button(chat_id=ADMIN_USER_ID, menu_button=MenuButtonCommands())
        print("Telegram 原生左下角 Menu 菜单已强制刷新并生效！")
    except Exception as e:
        print(f"注册原生菜单失败: {e}")

# ----------------- 主程序启动 -----------------
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # 基础与各周期预览指令
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("del", cmd_del))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("export_skill", cmd_export_skill))
    
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("daily", cmd_digest))
    app.add_handler(CommandHandler("weekly", cmd_weekly))
    app.add_handler(CommandHandler("monthly", cmd_monthly))
    app.add_handler(CommandHandler("annual", cmd_annual))
    
    # 倒数日与历程指令
    app.add_handler(CommandHandler("target", cmd_target))
    app.add_handler(CommandHandler("memo", cmd_memo))
    app.add_handler(CommandHandler("remark", cmd_memo))
    app.add_handler(CommandHandler("targets", cmd_targets))
    app.add_handler(CommandHandler("deltarget", cmd_deltarget))
    
    # 关键词屏蔽指令
    app.add_handler(CommandHandler("block", cmd_block))
    app.add_handler(CommandHandler("blocklist", cmd_blocklist))
    app.add_handler(CommandHandler("filters", cmd_blocklist))
    app.add_handler(CommandHandler("unblock", cmd_unblock))
    
    # 按钮回调
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # OPML 文件接收
    app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, handle_opml_document))
    
    job_queue = app.job_queue
    job_queue.run_repeating(job_poll_feeds, interval=timedelta(minutes=POLL_INTERVAL_MINUTES), first=10)
    digest_time = dt_module.time(hour=EVENING_DIGEST_HOUR, minute=EVENING_DIGEST_MINUTE, tzinfo=TIMEZONE)
    job_queue.run_daily(job_evening_digest, time=digest_time)
    
    print("NewsFlash RSS Telegram Bot (A1+C1+周期体系上线) 已启动，正在长轮询中...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
