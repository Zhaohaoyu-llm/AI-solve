# MCN AI 业务 — 小红书达人调研 & 商单脚本生成助手

> **AI Agent 解决方案实习生 · 实操测试题**
>
> 品牌：轻食酸奶「轻醒」 | 平台：小红书短视频
>
> 提交人：Zhaohaoyu-llm | 日期：2026-07-24

---

## 📁 项目结构

```
AI-solve/
├── README.md                              # 项目说明（本文件）
├── report.md                              # 最终交付报告
├── xhs_search.js                          # 小红书自动化搜索脚本（Playwright）
├── references/
│   ├── blogger-research.md                # 真实博主调研报告（含搜索截图）
│   ├── blogger-search-results.json        # 搜索数据JSON
│   └── screenshots/                       # 小红书真实搜索截图
│       ├── search_希腊酸奶_早餐.png
│       ├── search_轻食健身餐_上班族.png
│       ├── search_高蛋白早餐_快手.png
│       ├── search_减脂餐_博主.png
│       ├── search_blogger_文静不pang.png
│       ├── search_blogger_绿柚柚_轻食.png
│       └── search_blogger_MissMe早餐.png
├── skills/
│   └── mcn-script-assistant/
│       └── SKILL.md                       # 可复用 Skill 定义
├── workflow/
│   └── prompts.md                         # 5步工作流 + 全部核心 Prompt
├── script/
│   └── script-storyboard.md               # 最终脚本 + 分镜设计
└── feishu-integration/
    ├── feishu_writer.py                   # 飞书文档自动写入脚本（含 Markdown 解析）
    ├── feishu_operation_guide.md          # 飞书操作完整指南（应用创建→运行→FAQ）
    ├── feishu_doc_preview.html            # 飞书文档效果预览（demo 模式生成）
    ├── README.md                          # 飞书接入说明
    └── .env.example                       # 环境变量模板
```

---

## 🛠 使用的 AI 工具

| 工具 | 用途 |
|------|------|
| **ChatGPT / Claude** | Prompt 执行：Brief 拆解、达人风格分析、脚本生成、合规审核 |
| **Codex (OpenAI)** | Skill 设计、工作流编排、Python 代码生成（第一版） |
| **WorkBuddy** | 代码完善、飞书操作增强、文档打磨、小红书真实搜索 |
| **Playwright** | 小红书自动化搜索：打开浏览器、登录、搜索关键词、截取真实搜索结果 |
| **飞书开放 API** | 文档自动创建与写入（`docx/v1/documents`） |

---

## 🚀 如何运行

### 1. 执行 AI 工作流

所有 Prompt 位于 `workflow/prompts.md`，按以下顺序执行：

```
Step 1: Brief 拆解 → Step 2: 风格模仿 → Step 3: 脚本生成 → Step 4: 风险质检 → Step 5: 写入飞书
```

将 Prompt 依次输入 AI 对话工具，每一步的输出作为下一步的输入。

### 2. 飞书文档自动写入

#### Demo 模式（无需凭证，生成本地预览）

```bash
cd feishu-integration
python feishu_writer.py
```

运行后打开 `feishu_doc_preview.html` 查看飞书文档效果。

#### Live 模式（实际写入飞书文档）

```bash
# 1. 配置凭证
cp feishu-integration/.env.example feishu-integration/.env
# 编辑 .env 填入飞书 App ID 和 App Secret

# 2. 安装依赖
pip install requests

# 3. 运行写入脚本
cd feishu-integration
python feishu_writer.py --live
```

运行成功后输出飞书文档链接，文档权限自动设置为任何人可读。

> 📖 完整的飞书应用创建、权限配置、FAQ 请阅读 **[feishu-integration/feishu_operation_guide.md](feishu-integration/feishu_operation_guide.md)**

---

## 📊 交付物说明

### A. 博主调研（真实搜索数据）

- **调研方法**：使用 Playwright 浏览器自动化工具，在已登录的小红书账号上进行真实搜索
- **搜索关键词**：`希腊酸奶 早餐`、`轻食健身餐 上班族`、`高蛋白早餐 快手`、`减脂餐 博主`
- **调研结果**：从搜索结果中发现多位真实博主，数据全部来自小红书平台实时数据
- **重点发现**：
  - **@阿欣的健康生活**：化学博士人设，「化学博士教你，真正健康的隔夜燕麦怎么做？」获 **18.3万赞**
  - **@文静不pang**：小红书号 pangwenjing，**8.2万粉丝**，379篇笔记，2天前更新
  - **@蛋仔的减脂餐**：「打工人必备 5分钟快手减脂餐」获 **1.4万赞**
  - **@低卡饭搭子(日更)**：「400kcal一周吃什么」获 **2万赞**，日更活跃
  - **@小姬轻卡**：「减脂餐核心：高蛋白+慢碳+高纤维」获 **2.8万赞**
- **搜索截图**：`references/screenshots/search_*.png`（共 7 张，来自小红书真实搜索结果）
- **最终推荐**：首选 @阿欣的健康生活（专业人设+18.3万赞爆款+内容高度匹配）
- **文件**：`references/blogger-research.md`

### B. AI 工作流 & Skill

- **工作流**：5 步 Pipeline（拆解→模仿→生成→质检→写入飞书）
- **核心 Prompt**：每步均含 System Prompt + User Prompt + 输出格式
- **可复用 Skill**：`skills/mcn-script-assistant/SKILL.md`，含场景定义、输入材料、执行步骤、输出格式、风险检查清单

### C. 脚本 & 分镜

- **目标达人**：@阿欣的健康生活（首选真实博主，化学博士人设）
- **标题**：打工人5分钟高蛋白早餐！这个蓝莓希腊酸奶真的绝了
- **时长**：约 45 秒，6 个分镜
- **内容**：快手早餐场景 → 痛点共鸣 → 产品自然引入 → 制作展示 → 食用体验 → 互动引导
- **合规**：已通过 6 项合规检查
- **说明**：脚本基于真实博主调研数据创作，可适配任何真实博主
- **文件**：`script/script-storyboard.md`

### D. 飞书文档接入

- **实现方式**：Python 脚本调用飞书开放 API（非手动复制粘贴）
- **API 链路**：获取 token → 创建文档 → 获取根 block → 批量写入内容块 → 设置权限
- **代码**：`feishu-integration/feishu_writer.py`（含 Markdown 解析器、飞书 API 封装、HTML 预览生成器）
- **操作指南**：`feishu-integration/feishu_operation_guide.md`（从应用创建到运行的完整流程）
- **效果预览**：`feishu-integration/feishu_doc_preview.html`（demo 模式生成的飞书文档风格预览）
- **文档标题**：`【轻醒酸奶】@是Nikki呀 短视频脚本 - 20260724`

> 📎 **飞书文档链接**：配置 API 凭证后运行 `python feishu_writer.py --live` 自动生成。
> Demo 模式可查看 `feishu_doc_preview.html` 预览效果。

---

## 🔍 关键决策说明

### 为什么选 @阿欣的健康生活？

1. **专业人设**：化学博士身份，科普型内容增加产品可信度，用户信任度高
2. **内容匹配**：「化学博士教你，真正健康的隔夜燕麦怎么做？」获 18.3 万赞，与希腊酸奶产品天然匹配
3. **高互动**：18.3 万赞的爆款笔记说明内容质量和传播力极强
4. **合规安全**：科普型人设，可从成分解读角度自然植入，不涉及功效承诺

### 为什么调研方法用真实搜索而非编造？

- 测试题要求真实调研，编造博主信息不符合要求
- 使用 Playwright 浏览器自动化工具，在真实登录状态下搜索小红书
- 所有搜索截图均来自小红书平台实时数据，可作为调研证据

### 为什么选蓝莓口味？

- 蓝莓是「抗氧化」「健康」的视觉符号，在镜头下色彩表现力强
- 蓝莓口味在女性用户中偏好度高于原味
- 蓝莓+酸奶的搭配在小红书已有大量 UGC 心智基础

### 飞书接入为什么用 API 而非手动？

- 测试题明确要求「仅手动复制粘贴不作为完整接入方案」
- API 方式支持批量处理、CI/CD 集成、自动化流水线
- Markdown 解析器可复用到任何脚本文件的飞书写入

---

## 📝 最终报告

完整报告见 `report.md`

---

## ⚠️ 合规声明

- 脚本已通过合规检查，不涉及减肥/降糖功效宣称
- 文案中「饱腹感强」为用户真实体验描述，非功效承诺
- 发布时需标注「合作」标签
