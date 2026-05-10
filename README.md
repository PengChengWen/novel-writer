# 🖊️ 小说风格模仿引擎 (Novel Style Mimicry Engine)

一个能模仿特定小说风格来自动写作的系统。上传参考小说，分析文笔特征和爽点模式，生成风格指南，然后逐章自动创作保持风格一致性的新小说。

## 核心功能

1. **风格分析** — 上传参考小说，AI 分析句式、词汇、节奏、描写、对话等维度，输出 StyleDNA
2. **爽点识别** — 自动扫描全文，识别打脸、装逼、升级、揭秘、危机、感情 6 种爽点类型，提取分布规律
3. **风格指南生成** — 根据分析结果生成详细的风格指南，后续写作时作为 system prompt
4. **大纲引擎** — 三层大纲结构（总纲→分卷→章节），支持多种题材模板
5. **逐章写作** — 加载上下文 → 构建 prompt → AI 生成 → 质量检查 → 存入数据库
6. **人物一致性** — 人设定义、说话风格、战斗风格管理，写完自动检查人设崩塌
7. **番茄发布** — Playwright 浏览器自动化，登录番茄小说并发布章节

## 技术栈

- **后端**: Python 3.11+ / FastAPI
- **数据库**: MySQL (novel_writer)
- **异步任务**: Celery + Redis
- **AI**: OpenAI Python SDK (对接小米大模型)
- **发布**: Playwright (番茄小说自动化)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写实际配置
```

### 3. 启动基础设施

```bash
docker-compose up -d redis
```

### 4. 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS novel_writer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 启动服务

```bash
# 启动 FastAPI
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 启动 Celery Worker
celery -A backend.tasks.celery_app worker --loglevel=info -Q analyze,write,publish
```

### 6. 访问 API 文档

打开 http://localhost:8000/docs 查看 Swagger 文档

## API 概览

| 模块 | 路由前缀 | 功能 |
|------|---------|------|
| 分析器 | `/api/analyzer` | 上传小说、触发风格分析、获取结果 |
| 大纲 | `/api/planner` | 生成大纲、编辑大纲 |
| 写作 | `/api/writer` | 触发写作、获取章节、人物管理 |
| 发布 | `/api/publisher` | 发布到番茄小说 |

## 项目结构

```
novel-writer/
├── backend/
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库连接 + 建表
│   ├── analyzer/         # 风格分析器
│   │   ├── style_parser.py
│   │   ├── hook_parser.py
│   │   ├── style_guide.py
│   │   └── routes.py
│   ├── planner/          # 大纲引擎
│   │   ├── generator.py
│   │   ├── templates.py
│   │   └── routes.py
│   ├── writer/           # 写作引擎
│   │   ├── engine.py
│   │   ├── prompts.py
│   │   ├── characters.py
│   │   ├── state_manager.py
│   │   ├── quality.py
│   │   └── routes.py
│   ├── publisher/        # 发布引擎
│   │   ├── base.py
│   │   ├── fanqie.py
│   │   └── routes.py
│   ├── models/           # SQLAlchemy 模型
│   │   ├── novel.py
│   │   ├── chapter.py
│   │   ├── outline.py
│   │   ├── style_profile.py
│   │   └── character.py
│   └── tasks/            # Celery 任务
│       ├── celery_app.py
│       ├── analyze_task.py
│       ├── write_task.py
│       └── publish_task.py
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## License

Private project.
