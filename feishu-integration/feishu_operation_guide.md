# 飞书文档自动化接入 — 完整操作指南

## 概述

本指南详细说明如何通过飞书开放平台 API，将 MCN 商单脚本自动写入飞书文档。涵盖从应用创建到脚本运行的完整流程。

---

## 一、飞书应用创建（5 分钟）

### 1.1 注册飞书开放平台

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 使用飞书账号登录（个人或企业账号均可）
3. 如无飞书账号，先下载飞书客户端注册

### 1.2 创建企业自建应用

1. 进入 **开发者后台** → 点击 **创建企业自建应用**
2. 填写应用信息：
   - 应用名称：`MCN脚本助手`
   - 应用描述：`MCN商单脚本自动写入飞书文档`
   - 应用图标：自行上传或使用默认
3. 创建完成后，进入应用详情页

### 1.3 获取 API 凭证

在应用详情页的 **凭证与基础信息** 中获取：

| 凭证 | 说明 | 位置 |
|------|------|------|
| **App ID** | 应用唯一标识 | 凭证与基础信息 → App ID |
| **App Secret** | 应用密钥 | 凭证与基础信息 → App Secret |

> ⚠️ App Secret 请妥善保管，不要提交到 Git 仓库（已在 .gitignore 中排除）。

### 1.4 配置应用权限

在 **权限管理** 中添加以下权限：

| 权限名称 | 权限标识 | 用途 |
|----------|----------|------|
| 查看、评论、编辑和管理云空间中所有文件 | `drive:drive` | 创建文档到指定文件夹 |
| 查看、评论和编辑知识库 | `wiki:wiki` | 知识库操作（可选） |
| 查看、评论、编辑和管理文档 | `docx:document` | 文档读写 |
| 查看、评论、编辑和管理电子表格 | `sheets:spreadsheet` | 表格操作（可选） |

### 1.5 发布应用

1. 在 **版本管理与发布** 中创建版本
2. 提交审核（企业自建应用通常自动通过）
3. 确保应用状态为 **已发布**

---

## 二、环境配置（2 分钟）

### 2.1 配置环境变量

```bash
# 进入飞书集成目录
cd feishu-integration

# 复制环境变量模板
cp .env.example .env
```

编辑 `.env` 文件，填入你的飞书凭证：

```env
# 飞书开放平台配置
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_FOLDER_TOKEN=
```

> `FEISHU_FOLDER_TOKEN` 为可选参数，用于指定文档创建的目标文件夹。
> 获取方式：在飞书云空间中打开目标文件夹，URL 中的最后一段即为 folder_token。

### 2.2 安装依赖

```bash
pip install requests
```

---

## 三、运行脚本（1 分钟）

### 3.1 Demo 模式（无需凭证）

不配置 API 凭证时，脚本自动进入 demo 模式，生成本地 HTML 预览：

```bash
cd feishu-integration
python feishu_writer.py
```

**输出**：
```
============================================================
飞书文档预览 — DEMO 模式（未配置 API 凭证）
============================================================
[OK] HTML 预览已生成: feishu_doc_preview.html

预览文件: feishu_doc_preview.html
配置 .env 中的飞书 API 凭证后，可切换到 LIVE 模式实际写入飞书文档
============================================================
```

打开 `feishu_doc_preview.html` 即可查看飞书文档效果预览。

### 3.2 Live 模式（实际写入飞书）

配置好 `.env` 后，使用 `--live` 参数实际调用飞书 API：

```bash
cd feishu-integration
python feishu_writer.py --live
```

**输出**：
```
============================================================
飞书文档自动写入 — LIVE 模式
============================================================
[1/5] 读取脚本文件: ../script/script-storyboard.md
[2/5] 解析完成: 48 个内容块
[OK] 获取 tenant_access_token 成功
[OK] 文档创建成功: ABCDefghIJklMNop
      链接: https://bytedance.feishu.cn/docx/ABCDefghIJklMNop
[OK] 写入进度: 48/48 blocks
[OK] 全部内容写入完成 (48 blocks)
[OK] 文档权限已设置为任何人可读

============================================================
飞书文档链接: https://bytedance.feishu.cn/docx/ABCDefghIJklMNop
============================================================
```

### 3.3 指定自定义脚本文件

```bash
python feishu_writer.py --doc /path/to/your_script.md --live
```

---

## 四、API 调用流程详解

脚本内部执行以下 5 个步骤：

```
┌─────────────────────────────────────────────────────────────────┐
│                    飞书文档自动写入流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: 读取脚本 Markdown 文件                                  │
│  ├── 读取 script/script-storyboard.md                           │
│  └── 解析为文本内容                                              │
│         ↓                                                       │
│  Step 2: Markdown → 飞书 Block 转换                             │
│  ├── MarkdownParser 解析标题、段落、表格、列表、分割线            │
│  └── 转换为飞书 docx API 的 block 结构                           │
│         ↓                                                       │
│  Step 3: 获取 tenant_access_token                               │
│  ├── POST /auth/v3/tenant_access_token/internal                 │
│  ├── 传入 app_id + app_secret                                   │
│  └── token 有效期 2 小时，自动管理过期刷新                       │
│         ↓                                                       │
│  Step 4: 创建飞书文档                                           │
│  ├── POST /docx/v1/documents                                    │
│  ├── 传入文档标题 + folder_token（可选）                         │
│  └── 返回 document_id                                           │
│         ↓                                                       │
│  Step 5: 批量写入内容块                                         │
│  ├── GET /docx/v1/documents/{doc_id}/blocks → 获取根 block_id   │
│  ├── POST /docx/v1/documents/{doc_id}/blocks/{root_id}/children │
│  ├── 自动分批（每批 ≤50 blocks）                                 │
│  └── 支持重试（3次指数退避）                                     │
│         ↓                                                       │
│  Bonus:  设置文档权限为任何人可读                                │
│  └── PATCH /drive/v1/permissions/{doc_id}/public                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.1 飞书 Block 类型映射

脚本支持以下 Markdown 元素到飞书 Block 的转换：

| Markdown 元素 | 飞书 block_type | 说明 |
|---------------|-----------------|------|
| `# 标题` | 3 (heading1) | 一级标题 |
| `## 标题` | 4 (heading2) | 二级标题 |
| `### 标题` | 5 (heading3) | 三级标题 |
| `#### 标题` | 6 (heading4) | 四级标题 |
| 普通文本 | 2 (text) | 支持粗体、斜体 |
| `- 列表项` | 12 (bullet) | 无序列表 |
| `1. 列表项` | 13 (ordered) | 有序列表 |
| `\| 表格 \|` | 31 (table) | 表格（自动行列） |
| `---` | 19 (divider) | 分割线 |

### 4.2 错误处理机制

- **Token 过期**：自动检测 code=99991663，刷新 token 后重试
- **网络超时**：3 次指数退避重试（1s → 2s → 4s）
- **QPS 限制**：批量写入间隔 0.5s，避免触发频率限制
- **权限不足**：输出明确错误提示，引导检查应用权限配置

---

## 五、飞书文档效果预览

### 5.1 文档结构

写入飞书后的文档包含以下内容：

1. **文档标题**：`【轻醒酸奶】@是Nikki呀 短视频脚本 - 20260724`
2. **基本信息**：达人、品牌、口味、时长、风格
3. **脚本标题**：打工人5分钟高蛋白早餐！这个蓝莓希腊酸奶真的绝了
4. **分镜设计**（6 个分镜，每个含画面、口播、字幕、BGM）
5. **产品植入点分析表**
6. **合规自查表**（7 项检查）
7. **拍摄建议**

### 5.2 本地预览

运行 demo 模式后，打开 `feishu_doc_preview.html` 查看效果：

```bash
# Windows
start feishu_doc_preview.html

# macOS
open feishu_doc_preview.html
```

预览页面模拟飞书文档 UI，包含：
- 左侧文档目录侧边栏
- 文档标题和元信息
- 格式化的分镜表格
- 合规检查标记（绿色 ✅ / 橙色 ⚠️）
- 底部生成信息

### 5.3 效果截图

飞书文档效果截图见 `references/screenshots/feishu-doc-mockup.png`。

---

## 六、常见问题排查

### Q1: 获取 token 失败

```
错误: API 返回错误: {"code": 99991663, "msg": "invalid app_id or app_secret"}
```

**解决方案**：
- 检查 `.env` 文件中的 App ID 和 App Secret 是否正确
- 确认 App ID 格式为 `cli_` 开头
- 确认应用已发布

### Q2: 创建文档失败

```
错误: API 错误 code=99991672: permission denied
```

**解决方案**：
- 检查应用是否已添加 `docx:document` 权限
- 确认应用已发布并审核通过
- 如指定了 folder_token，确认应用有该文件夹的访问权限

### Q3: 写入内容块失败

```
错误: API 错误 code=99991663: tenant_access_token expired
```

**解决方案**：
- 脚本已内置 token 自动刷新，此错误不应出现
- 如仍出现，检查网络连接稳定性

### Q4: 文档权限设置失败

```
错误: 设置权限失败（不影响文档内容）
```

**解决方案**：
- 权限设置失败不影响文档内容，可手动在飞书中设置分享权限
- 检查应用是否有 `drive:drive` 权限

### Q5: 如何获取 folder_token

1. 在飞书云空间中创建或打开目标文件夹
2. 查看浏览器地址栏 URL
3. URL 最后一段即为 folder_token（如 `fldcnXXXXXX`）

---

## 七、自动化集成建议

### 7.1 CI/CD 集成

可将飞书写入步骤集成到 CI/CD 流水线中：

```yaml
# GitHub Actions 示例
- name: Write script to Feishu
  env:
    FEISHU_APP_ID: ${{ secrets.FEISHU_APP_ID }}
    FEISHU_APP_SECRET: ${{ secrets.FEISHU_APP_SECRET }}
  run: |
    cd feishu-integration
    python feishu_writer.py --live
```

### 7.2 批量处理

修改脚本支持批量处理多个商单脚本：

```python
scripts = ["script1.md", "script2.md", "script3.md"]
for script in scripts:
    run_live_mode(script, app_id, app_secret, folder_token)
```

### 7.3 Webhook 通知

写入完成后可集成企业微信/飞书机器人通知：

```python
# 写入成功后发送通知
import requests
requests.post(webhook_url, json={
    "msg_type": "text",
    "content": {"text": f"脚本已写入飞书文档: {doc_url}"}
})
```
