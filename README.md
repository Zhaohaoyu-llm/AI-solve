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
├── README.md                          # 项目说明（本文件）
├── report.md                          # 最终交付报告
├── references/
│   └── blogger-research.md            # 10位达人调研 + 最终选定分析
├── skills/
│   └── mcn-script-assistant/
│       └── SKILL.md                   # 可复用 Skill 定义
├── workflow/
│   └── prompts.md                     # 5步工作流 + 全部核心 Prompt
├── script/
│   └── script-storyboard.md           # 最终脚本 + 分镜设计
└── feishu-integration/
    ├── feishu_writer.py               # 飞书文档自动写入脚本
    ├── README.md                      # 飞书接入详细说明
    └── .env.example                   # 环境变量模板
```

---

## 🛠 使用的 AI 工具

| 工具 | 用途 |
|------|------|
| **ChatGPT / Claude** | Prompt 执行：Brief 拆解、达人风格分析、脚本生成、合规审核 |
| **Codex (OpenAI)** | Skill 设计、工作流编排、Python 代码生成 |
| **飞书开放 API** | 文档自动创建与写入（`docx/v1/documents`） |

---

## 🚀 如何运行

### 1. 执行 AI 工作流

所有 Prompt 位于 `workflow/prompts.md`，按以下顺序执行：

```
Step 1: Brief 拆解 → Step 2: 风格模仿 → Step 3: 脚本生成 → Step 4: 风险质检
```

将 Prompt 依次输入 AI 对话工具，每一步的输出作为下一步的输入。

### 2. 飞书文档自动写入

```bash
# 1. 配置凭证
cp feishu-integration/.env.example feishu-integration/.env
# 编辑 .env 填入你的飞书 App ID 和 App Secret

# 2. 安装依赖
pip install requests

# 3. 运行写入脚本
cd feishu-integration
python feishu_writer.py
```

详细说明见 `feishu-integration/README.md`。

---

## 📊 交付物说明

### A. 博主调研

- **调研范围**：小红书平台
- **调研数量**：10 位候选人 → 最终选定 1 位（@是Nikki呀）
- **调研维度**：粉丝量、内容方向、粉丝画像、代表作品、匹配理由
- **最终选定理由**：在「人设」「内容场景」「表达方式」「品牌匹配度」四个维度均为最优
- **文件**：`references/blogger-research.md`

### B. AI 工作流 & Skill

- **工作流**：5 步 Pipeline（拆解→模仿→生成→质检→写入飞书）
- **核心 Prompt**：每步均含 System Prompt + User Prompt + 输出格式
- **可复用 Skill**：`skills/mcn-script-assistant/SKILL.md`，含场景定义、输入材料、执行步骤、输出格式、风险检查清单

### C. 脚本 & 分镜

- **达人**：@是Nikki呀
- **标题**：打工人5分钟高蛋白早餐！这个蓝莓希腊酸奶真的绝了
- **时长**：约 45 秒，6 个分镜
- **内容**：快手早餐场景 → 痛点共鸣 → 产品自然引入 → 制作展示 → 食用体验 → 互动引导
- **合规**：已通过 6 项合规检查
- **文件**：`script/script-storyboard.md`

### D. 飞书文档接入

- **实现方式**：Python 脚本调用飞书开放 API
- **API 链路**：获取 token → 创建文档 → 批量写入内容块
- **文件**：`feishu-integration/feishu_writer.py`
- **文档标题**：`【轻醒酸奶】@是Nikki呀 短视频脚本 - 20260724`

> 📎 飞书文档链接：运行 `feishu_writer.py` 后自动输出，请将链接填入此处并确保已开权限。
>
> **飞书文档链接**：[待运行后填写]

---

## 🔍 关键决策说明

### 为什么选 @是Nikki呀？

1. **三重场景覆盖**：她的内容天然覆盖早餐、运动后、快手便当，与 brief 的三大场景完美吻合
2. **人设真实**：一线城市上班族，28 万粉丝以白领女性为主，购买力和种草转化预期好
3. **风格适配**：温柔教程型口吻，产品植入无违和感，符合「自然种草」核心要求
4. **合规安全**：日常内容不涉功效承诺，商业合作风险低

### 为什么选蓝莓口味？

- 蓝莓是「抗氧化」「健康」的视觉符号，在镜头下色彩表现力强
- 蓝莓口味在女性用户中偏好度高于原味
- 蓝莓+酸奶的搭配在小红书已有大量 UGC 心智基础

---

## 📝 最终报告

完整报告见 `report.md`

---

## ⚠️ 合规声明

- 脚本已通过合规检查，不涉及减肥/降糖功效宣称
- 文案中「饱腹感强」为用户真实体验描述，非功效承诺
- 发布时需标注「合作」标签
