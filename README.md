# NewsFlash Telegram Bot

> **高质感二次元伴侣晚报 · CDT 杂志即时预览 · 智能时序晋级 · 跨平台个人专属 RSS 聚合系统**

NewsFlash 是一个专为个人打造的高品质 Telegram 资讯聚合与伴侣陪伴机器人。区别于传统生硬机械的推送工具，NewsFlash 将**33 套细腻沉浸的二次元伴侣拟人台词**、**CDT 杂志级 Telegraph 即时预览排版**与**智能时序晋级周期特刊体系**融为一体，带来温暖、纯净、极简的晚间阅读体验。

---

## 核心特性

- **33 套无标签二次元伴侣人设**：基于御姐、黑长直、幼驯染、大小姐、女仆、萝莉、金发、傲娇、机娘、文学少女、强占有欲、腹黑等 12 项经典母题衍生。口吻自然生动，绝不自称“本猫娘”，无任何生硬的系统设定提示词。
- **四大周期独立体系与时序自动晋级**：
  - 日报（Daily）、周报（Weekly · 周日晚）、月报（Monthly · 月末晚）、年报（Annual · 12月31日跨年夜）拥有完全独立的专属台词、标题模板与总结维度；
  - 采用**时序自动晋级吸收制**（年报 > 月报 > 周报 > 日报），任何给定的夜晚仅精准推送 1 张最高层级的聚合特刊，绝不轰炸刷屏。
- **全局严格零 Emoji 极简排版**：所有卡片、交互按钮、对话台词严禁任何彩色图标与特殊符号，全凭文字本身的排版美学与节奏传递高质感。
- **CDT 杂志级 Telegraph 即时预览**：
  - 聊天气泡内专注私享陪伴，去除冗长资讯；
  - 点击底部原生的 `⚡ 即时预览`（Instant View），瞬间秒开包含典雅竖块分栏（`▍`）、发布时间戳与外链目录的杂志长报。
- **日程与历程双分区看板 (A1 + 单行紧凑流)**：
  - 支持完整年份 `YYYY-MM-DD` 目标倒数；
  - 目标到期后永久沉淀为“距今已过 X 天”的历程记事；
  - 同一天有多个任务时，单行以中圆点 `·` 紧凑并列，伴侣台词智能口语化汇总。
- **博主专属 ID = 1 特权**：
  - 个人独立博客享有专享置顶、优先轮询、以及根据博文更新天数的阶梯式情感互动（新作赞赏 / 长期静默体贴抚慰）。
- **全天静默轮询与双重屏蔽**：
  - 30 分钟后台静默探测，支持全局动态匹配与追溯式关键词屏蔽；
  - 支持直接拖拽发送 `.opml` 文件并发探测批量导入；
  - 原生提供 `/export_skill` 一键打包导出当前订阅与人设的完整复刻 Skill 压缩包。

---

## 快速开始

### 1. 克隆仓库与安装依赖

```bash
git clone https://github.com/F10w-0x00/newsflash-telegram-bot.git
cd newsflash-telegram-bot

# 创建并激活 Python 虚拟环境 (建议 Python 3.10+)
python3 -m venv venv
source venv/bin/activate  # Windows 用户运行: .\venv\Scripts\activate

# 安装生产依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量模板文件并填写您的真实凭据：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```ini
# 从 @BotFather 申请的 Telegram Bot Token
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRstuVWXyz

# 授权主人的 Telegram 纯数字 ID
ADMIN_USER_ID=1234567890

# （可选）主人的个人博客与 RSS 地址
MASTER_BLOG_URL=https://example.com/
MASTER_BLOG_RSS=https://example.com/rss.xml

# （可选）时区设置，默认为 Asia/Shanghai
TIMEZONE=Asia/Shanghai
```

### 3. 启动运行

#### Linux / FreeBSD 后台守护启动：
```bash
chmod +x start.sh
./start.sh
```

#### 直接前台运行：
```bash
python3 rss_bot.py
```

---

## 指令一览

| 指令 | 说明 |
| :--- | :--- |
| `/menu` | 打开纯文字双列控制中心面板 |
| `/digest` | 手动生成今日晚报预览（同 `/daily`） |
| `/weekly` | 预览周度特刊（每周日晚 22:00 自动推送） |
| `/monthly` | 预览月度特刊（每月末日晚 22:00 自动推送） |
| `/annual` | 预览年度史册特刊（每年 12 月 31 日晚自动推送） |
| `/targets` | 查看未来征途与历程记事双分区看板 |
| `/target <日期> <事项>` | 添加目标（例：`/target 2026-11-14 计算机考试`） |
| `/deltarget <编号>` | 从数据库中彻底删除指定的日程 |
| `/add <URL>` | 添加 RSS/Atom 订阅源 |
| `/list` | 查看已订阅博客列表（个人博客置顶） |
| `/del <编号>` | 取消指定订阅 |
| `/block <源编号> <词...>` | 针对指定源添加标题关键词屏蔽 |
| `/blocklist` | 查看当前生效的关键词屏蔽列表 |
| `/unblock <规则ID>` | 解除关键词屏蔽 |
| `/export` | 导出标准的 OPML 订阅备份文件 |
| `/export_skill` | 一键打包导出当前订阅、33 套人设与屏蔽词的复刻包 |
| `/help` | 查看完整帮助指南 |

---

## 目录结构

```text
newsflash-telegram-bot/
├── rss_bot.py           # 核心机器人服务与调度引擎
├── personas.json        # 33 套精选高情商二次元伴侣人设文案包
├── start.sh             # POSIX 标准后台进程管理脚本
├── requirements.txt     # Python 依赖清单
├── .env.example         # 环境变量模板
├── .gitignore           # Git 忽略配置
├── LICENSE              # MIT 开源协议
└── README.md            # 项目使用与架构说明
```

---

## 开源协议

本项目基于 [MIT License](LICENSE) 协议开源。
