# 飞书文档自动化接入说明

## 概述

本模块实现了将 MCN 商单脚本自动写入飞书文档的功能，使用飞书开放平台 API v1。

## 快速开始

### Demo 模式（无需凭证）

```bash
cd feishu-integration
python feishu_writer.py
```

运行后生成 `feishu_doc_preview.html`，用浏览器打开即可查看飞书文档效果预览。

### Live 模式（实际写入飞书）

```bash
# 1. 配置凭证
cp .env.example .env
# 编辑 .env 填入飞书 App ID 和 App Secret

# 2. 安装依赖
pip install requests

# 3. 运行写入脚本
python feishu_writer.py --live
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `feishu_writer.py` | 主脚本：Markdown 解析 + 飞书 API 调用 + HTML 预览生成 |
| `feishu_operation_guide.md` | **完整操作指南**（应用创建、权限配置、FAQ） |
| `feishu_doc_preview.html` | demo 模式生成的飞书文档效果预览页面 |
| `.env.example` | 环境变量模板 |
| `.env` | 实际凭证文件（已 gitignore） |

## API 流程

```
1. 获取 tenant_access_token
   POST /auth/v3/tenant_access_token/internal
   → token 有效期 2 小时，自动管理刷新

2. 创建飞书文档
   POST /docx/v1/documents
   → 返回 document_id

3. 获取文档根 block
   GET /docx/v1/documents/{document_id}/blocks
   → 返回根 block_id

4. 批量写入内容块
   POST /docx/v1/documents/{document_id}/blocks/{block_id}/children
   → 自动分批（每批 ≤50 blocks），支持重试

5. 设置文档权限
   PATCH /drive/v1/permissions/{document_id}/public
   → 设置为任何人可读

6. 输出飞书文档链接
   https://bytedance.feishu.cn/docx/{document_id}
```

## 支持的内容块类型

| Markdown 元素 | 飞书 Block 类型 |
|---------------|----------------|
| `# H1` ~ `#### H4` | heading1 ~ heading4 |
| 普通段落 | text（支持粗体、斜体） |
| `- 无序列表` | bullet |
| `1. 有序列表` | ordered |
| `\| 表格 \|` | table（自动行列数） |
| `---` | divider |

## 效果预览

飞书文档效果可通过 `feishu_doc_preview.html` 本地预览。

本地 HTML 预览：运行 demo 模式后打开 `feishu_doc_preview.html`。

## 详细指南

完整的飞书应用创建、权限配置、FAQ 请阅读 **[feishu_operation_guide.md](feishu_operation_guide.md)**。

## 注意事项

- tenant_access_token 有效期 2 小时，脚本自动管理过期刷新
- 确保飞书应用已发布并管理员审核通过
- 内容块写入 API 单次最多支持 50 个块，脚本自动分批
- `FEISHU_FOLDER_TOKEN` 为可选参数，不填则文档创建在应用根目录
