# 飞书文档自动化接入说明

## 概述

本模块实现了将 MCN 商单脚本自动写入飞书文档的功能，使用飞书开放平台 API。

## 前置准备

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 **App ID** 和 **App Secret**
4. 在应用权限中添加以下权限：
   - `docx:document` - 文档读写权限
   - `drive:drive` - 云空间访问权限

### 2. 配置环境变量

```bash
# 方式一：环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_FOLDER_TOKEN="your_folder_token"  # 可选

# 方式二：创建 .env 文件
cp .env.example .env
# 编辑 .env 文件填入凭证
```

### 3. 安装依赖

```bash
pip install requests
```

## 使用方法

### 命令行运行

```bash
cd feishu-integration
python feishu_writer.py
```

### Python 代码集成

```python
from feishu_writer import FeishuDocWriter, build_script_blocks

# 初始化
writer = FeishuDocWriter(app_id="xxx", app_secret="xxx")

# 创建文档
doc_id = writer.create_doc(title="脚本标题", folder_token="可选")

# 写入内容
blocks = build_script_blocks(script_data)
writer.write_content(doc_id, blocks)

print(f"文档链接: https://bytedance.feishu.cn/docx/{doc_id}")
```

## API 流程说明

```
1. 获取 tenant_access_token
   POST /auth/v3/tenant_access_token/internal

2. 创建飞书文档
   POST /docx/v1/documents

3. 批量写入内容块
   POST /docx/v1/documents/{document_id}/blocks/batch_create

4. 获取文档链接
   格式: https://bytedance.feishu.cn/docx/{document_id}
```

## 注意事项

- tenant_access_token 有效期 2 小时，需定期刷新
- 确保飞书应用已发布并管理员审核通过
- 内容块写入 API 单次最多支持 50 个块
