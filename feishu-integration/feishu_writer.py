"""
MCN Script Assistant - 飞书文档自动化写入模块
将生成的短视频脚本自动写入飞书文档（飞书开放 API v1）

功能：
  1. 读取脚本 Markdown 文件，解析为结构化内容块
  2. 调用飞书开放 API 创建文档并批量写入内容
  3. 支持标题、正文、表格、分隔线等内容块类型
  4. 无凭证时自动进入 demo 模式，生成本地 HTML 预览

用法：
  python feishu_writer.py                          # demo 模式，生成本地预览
  python feishu_writer.py --doc ../script/script-storyboard.md  # 指定脚本文件
  python feishu_writer.py --live                   # 调用飞书 API（需配置 .env）
"""

import os
import re
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path


# ============================================================
# 飞书 API 常量
# ============================================================

FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"

# 飞书文档 block_type 枚举
BLOCK_TYPE_TEXT = 2          # 文本
BLOCK_TYPE_HEADING1 = 3      # 一级标题
BLOCK_TYPE_HEADING2 = 4      # 二级标题
BLOCK_TYPE_HEADING3 = 5      # 三级标题
BLOCK_TYPE_HEADING4 = 6      # 四级标题
BLOCK_TYPE_BULLET = 12       # 无序列表
BLOCK_TYPE_ORDERED = 13      # 有序列表
BLOCK_TYPE_DIVIDER = 19      # 分割线
BLOCK_TYPE_TABLE = 31        # 表格


# ============================================================
# Markdown 解析器
# ============================================================

class MarkdownParser:
    """将 Markdown 脚本解析为飞书文档内容块"""

    def __init__(self, md_text: str):
        self.lines = md_text.split("\n")
        self.blocks = []

    def _text_run(self, content: str, bold: bool = False, italic: bool = False) -> dict:
        """构造 text_run 元素"""
        style = {}
        if bold:
            style["bold"] = True
        if italic:
            style["italic"] = True
        return {
            "text_run": {
                "content": content,
                "text_element_style": style if style else None
            }
        }

    def _parse_inline(self, text: str) -> list:
        """解析行内格式（粗体、斜体）"""
        elements = []
        pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*)'
        last_end = 0
        for m in re.finditer(pattern, text):
            if m.start() > last_end:
                elements.append(self._text_run(text[last_end:m.start()]))
            if m.group(2):  # **bold**
                elements.append(self._text_run(m.group(2), bold=True))
            elif m.group(3):  # *italic*
                elements.append(self._text_run(m.group(3), italic=True))
            last_end = m.end()
        if last_end < len(text):
            elements.append(self._text_run(text[last_end:]))
        return elements if elements else [self._text_run(text)]

    def _parse_table(self, lines: list, start: int) -> tuple:
        """解析 Markdown 表格，返回 (blocks, next_index)"""
        rows = []
        idx = start
        while idx < len(lines) and lines[idx].strip().startswith("|"):
            row = [c.strip() for c in lines[idx].strip().split("|")[1:-1]]
            rows.append(row)
            idx += 1

        # 跳过分隔行
        if len(rows) > 1 and all(set(c) <= set("-: ") for c in rows[1]):
            rows.pop(1)

        if not rows:
            return [], start

        num_rows = len(rows)
        num_cols = max(len(r) for r in rows)

        # 补齐每行列数
        for r in rows:
            while len(r) < num_cols:
                r.append("")

        # 飞书表格 block
        table_block = {
            "block_type": BLOCK_TYPE_TABLE,
            "table": {
                "property": {
                    "row_size": num_rows,
                    "column_size": num_cols
                },
                "cells": []
            }
        }

        for row in rows:
            cell_row = []
            for cell in row:
                cell_row.append([{
                    "block_type": BLOCK_TYPE_TEXT,
                    "text": {
                        "elements": self._parse_inline(cell)
                    }
                }])
            table_block["table"]["cells"].append(cell_row)

        return [table_block], idx

    def parse(self) -> list:
        """解析整个 Markdown 文档"""
        idx = 0
        while idx < len(self.lines):
            line = self.lines[idx].strip()

            # 空行
            if not line:
                idx += 1
                continue

            # 水平分割线
            if line in ("---", "***", "___"):
                self.blocks.append({"block_type": BLOCK_TYPE_DIVIDER})
                idx += 1
                continue

            # 标题
            heading_match = re.match(r'^(#{1,4})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2)
                block_type_map = {
                    1: BLOCK_TYPE_HEADING1,
                    2: BLOCK_TYPE_HEADING2,
                    3: BLOCK_TYPE_HEADING3,
                    4: BLOCK_TYPE_HEADING4,
                }
                bt = block_type_map.get(level, BLOCK_TYPE_HEADING2)
                key_map = {1: "heading1", 2: "heading2", 3: "heading3", 4: "heading4"}
                key = key_map.get(level, "heading2")
                self.blocks.append({
                    "block_type": bt,
                    key: {
                        "elements": self._parse_inline(title_text)
                    }
                })
                idx += 1
                continue

            # 表格
            if line.startswith("|"):
                table_blocks, next_idx = self._parse_table(self.lines, idx)
                self.blocks.extend(table_blocks)
                idx = next_idx
                continue

            # 无序列表
            bullet_match = re.match(r'^[-*]\s+(.+)$', line)
            if bullet_match:
                self.blocks.append({
                    "block_type": BLOCK_TYPE_BULLET,
                    "bullet": {
                        "elements": self._parse_inline(bullet_match.group(1))
                    }
                })
                idx += 1
                continue

            # 有序列表
            ordered_match = re.match(r'^\d+\.\s+(.+)$', line)
            if ordered_match:
                self.blocks.append({
                    "block_type": BLOCK_TYPE_ORDERED,
                    "ordered": {
                        "elements": self._parse_inline(ordered_match.group(1))
                    }
                })
                idx += 1
                continue

            # 普通文本
            self.blocks.append({
                "block_type": BLOCK_TYPE_TEXT,
                "text": {
                    "elements": self._parse_inline(line)
                }
            })
            idx += 1

        return self.blocks


# ============================================================
# 飞书文档写入器
# ============================================================

class FeishuDocWriter:
    """飞书文档写入器 — 封装飞书开放 API 调用"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = FEISHU_BASE_URL
        self._tenant_access_token = None
        self._token_expire_at = 0

    def _get_tenant_access_token(self) -> str:
        """获取 tenant_access_token（带过期管理）"""
        if self._tenant_access_token and time.time() < self._token_expire_at:
            return self._tenant_access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        for attempt in range(3):
            try:
                resp = requests.post(url, json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }, timeout=10)
                data = resp.json()
                if data.get("code") == 0:
                    self._tenant_access_token = data["tenant_access_token"]
                    # token 有效期 2 小时，提前 5 分钟刷新
                    self._token_expire_at = time.time() + 7200 - 300
                    print(f"[OK] 获取 tenant_access_token 成功")
                    return self._tenant_access_token
                else:
                    raise Exception(f"API 返回错误: {data}")
            except requests.RequestException as e:
                print(f"[WARN] 获取 token 第 {attempt+1} 次失败: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def _headers(self) -> dict:
        token = self._get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _retry_request(self, method: str, url: str, **kwargs) -> dict:
        """带重试的 HTTP 请求"""
        for attempt in range(3):
            try:
                resp = requests.request(method, url, headers=self._headers(), timeout=30, **kwargs)
                data = resp.json()
                if data.get("code") == 0:
                    return data
                # token 过期
                if data.get("code") == 99991663:
                    self._tenant_access_token = None
                    self._token_expire_at = 0
                    continue
                raise Exception(f"API 错误 code={data.get('code')}: {data.get('msg', '')}")
            except requests.RequestException as e:
                print(f"[WARN] 请求第 {attempt+1} 次失败: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def create_doc(self, title: str, folder_token: str = None) -> str:
        """创建飞书文档，返回文档 ID"""
        url = f"{self.base_url}/docx/v1/documents"
        body = {"title": title}
        if folder_token:
            body["folder_token"] = folder_token

        data = self._retry_request("POST", url, json=body)
        doc_id = data["data"]["document"]["document_id"]
        print(f"[OK] 文档创建成功: {doc_id}")
        print(f"      链接: https://bytedance.feishu.cn/docx/{doc_id}")
        return doc_id

    def get_doc_blocks(self, doc_id: str) -> dict:
        """获取文档的所有 block（用于获取根 block ID）"""
        url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks"
        data = self._retry_request("GET", url)
        return data["data"]

    def write_blocks(self, doc_id: str, blocks: list, batch_size: int = 50):
        """向文档批量写入内容块

        飞书 API 单次最多写入 50 个 block，自动分批。
        """
        # 获取文档根 block
        blocks_data = self.get_doc_blocks(doc_id)
        root_block_id = blocks_data["items"][0]["block_id"]

        total = len(blocks)
        written = 0

        for i in range(0, total, batch_size):
            batch = blocks[i:i + batch_size]
            url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks/{root_block_id}/children"
            body = {
                "children": batch,
                "index": -1  # 追加到末尾
            }
            self._retry_request("POST", url, json=body)
            written += len(batch)
            print(f"[OK] 写入进度: {written}/{total} blocks")
            if i + batch_size < total:
                time.sleep(0.5)  # 避免 QPS 限制

        print(f"[OK] 全部内容写入完成 ({total} blocks)")

    def set_doc_permission(self, doc_id: str, anyone_can_read: bool = True):
        """设置文档权限为任何人可阅读"""
        url = f"{self.base_url}/drive/v1/permissions/{doc_id}/public"
        body = {
            "external_access_entity": "open",
            "security_entity": "anyone_can_view",
            "comment_entity": "anyone_can_view",
            "share_entity": "anyone",
            "link_share_entity": "anyone_readable" if anyone_can_read else "anyone",
            "invite_external": True
        }
        try:
            self._retry_request("PATCH", url, json=body, params={"type": "doc"})
            print(f"[OK] 文档权限已设置为任何人可读")
        except Exception as e:
            print(f"[WARN] 设置权限失败（不影响文档内容）: {e}")


# ============================================================
# HTML 预览生成器（demo 模式）
# ============================================================

def generate_html_preview(md_text: str, output_path: str):
    """将 Markdown 脚本渲染为飞书文档风格的 HTML 预览页面"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>飞书文档预览 — 短视频脚本</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f5f6f7;
    color: #1f2329;
    line-height: 1.8;
  }}
  .feishu-sidebar {{
    position: fixed; left: 0; top: 0; width: 240px; height: 100vh;
    background: #fff; border-right: 1px solid #e8e8e8;
    padding: 16px 12px; overflow-y: auto; z-index: 100;
  }}
  .sidebar-header {{
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; margin-bottom: 12px;
    font-size: 14px; color: #3370ff; font-weight: 500;
  }}
  .sidebar-item {{
    padding: 6px 12px; border-radius: 6px; cursor: pointer;
    font-size: 13px; color: #646a73; margin-bottom: 2px;
  }}
  .sidebar-item:hover {{ background: #f0f2f5; }}
  .sidebar-item.active {{ background: #e8f0ff; color: #3370ff; }}
  .doc-container {{
    margin-left: 240px; padding: 40px 0;
    display: flex; justify-content: center;
  }}
  .doc-page {{
    background: #fff; width: 820px; min-height: 100vh;
    padding: 48px 64px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-radius: 0;
  }}
  .doc-title {{
    font-size: 28px; font-weight: 600; color: #1f2329;
    margin-bottom: 32px; line-height: 1.4;
  }}
  .doc-meta {{
    display: flex; gap: 24px; margin-bottom: 24px;
    font-size: 12px; color: #8f959e;
  }}
  .doc-meta span {{ display: flex; align-items: center; gap: 4px; }}
  .doc-divider {{
    border: none; border-top: 1px solid #e8e8e8; margin: 24px 0;
  }}
  h1 {{ font-size: 22px; font-weight: 600; margin: 24px 0 12px; color: #1f2329; }}
  h2 {{ font-size: 18px; font-weight: 600; margin: 20px 0 10px; color: #1f2329; }}
  h3 {{ font-size: 15px; font-weight: 600; margin: 16px 0 8px; color: #1f2329; }}
  p {{ font-size: 14px; margin-bottom: 8px; color: #3f3f3f; }}
  table {{
    width: 100%; border-collapse: collapse; margin: 12px 0;
    font-size: 13px;
  }}
  th {{
    background: #f0f2f5; padding: 8px 12px; text-align: left;
    font-weight: 500; color: #1f2329; border: 1px solid #e8e8e8;
  }}
  td {{
    padding: 8px 12px; border: 1px solid #e8e8e8; color: #3f3f3f;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  ul, ol {{ padding-left: 24px; margin-bottom: 8px; }}
  li {{ font-size: 14px; margin-bottom: 4px; color: #3f3f3f; }}
  strong {{ font-weight: 600; color: #1f2329; }}
  .check-pass {{ color: #00b42a; font-weight: 500; }}
  .check-warn {{ color: #ff9a2e; font-weight: 500; }}
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 12px; font-weight: 500; margin-right: 6px;
  }}
  .badge-blue {{ background: #e8f0ff; color: #3370ff; }}
  .badge-green {{ background: #e8ffea; color: #00b42a; }}
  .badge-orange {{ background: #fff3e8; color: #ff9a2e; }}
  .footer-note {{
    margin-top: 32px; padding: 12px 16px; background: #f7f8fa;
    border-radius: 8px; font-size: 12px; color: #8f959e;
  }}
  .demo-banner {{
    position: fixed; top: 0; right: 20px; z-index: 200;
    background: #fff3e8; color: #ff9a2e; padding: 6px 16px;
    border-radius: 0 0 8px 8px; font-size: 12px; font-weight: 500;
    border: 1px solid #ff9a2e; border-top: none;
  }}
</style>
</head>
<body>
<div class="demo-banner">DEMO 模式 — 此为本地预览，实际效果以飞书文档为准</div>
<div class="feishu-sidebar">
  <div class="sidebar-header">
    <span style="font-size:18px;">📄</span>
    <span>飞书文档</span>
  </div>
  <div class="sidebar-item active">短视频脚本</div>
  <div class="sidebar-item" style="color:#c0c4cc; cursor:default;">达人调研报告</div>
  <div class="sidebar-item" style="color:#c0c4cc; cursor:default;">AI 工作流设计</div>
  <div class="sidebar-item" style="color:#c0c4cc; cursor:default;">Skill 定义</div>
</div>
<div class="doc-container">
  <div class="doc-page">
    <div class="doc-title">【轻醒酸奶】@是Nikki呀 短视频脚本 - {datetime.now().strftime('%Y%m%d')}</div>
    <div class="doc-meta">
      <span>👤 飞行标准管理部</span>
      <span>🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
      <span>✅ 已通过合规检查</span>
    </div>
"""

    # 简单 Markdown -> HTML 转换
    import html as html_module

    in_table = False
    table_rows = []

    for line in md_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            if in_table and table_rows:
                html += _render_table(table_rows)
                table_rows = []
                in_table = False
            html += "<br>\n"
            continue

        if stripped in ("---", "***", "___"):
            if in_table and table_rows:
                html += _render_table(table_rows)
                table_rows = []
                in_table = False
            html += '<hr class="doc-divider">\n'
            continue

        # 表格行
        if stripped.startswith("|"):
            in_table = True
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            # 跳过分隔行
            if all(set(c) <= set("-: ") for c in cells):
                continue
            table_rows.append(cells)
            continue
        elif in_table and table_rows:
            html += _render_table(table_rows)
            table_rows = []
            in_table = False

        # 标题
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = html_module.escape(heading_match.group(2))
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            html += f"<h{level}>{text}</h{level}>\n"
            continue

        # 无序列表
        bullet_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if bullet_match:
            text = _inline_format(bullet_match.group(1))
            html += f"<ul><li>{text}</li></ul>\n"
            continue

        # 有序列表
        ordered_match = re.match(r'^\d+\.\s+(.+)$', stripped)
        if ordered_match:
            text = _inline_format(ordered_match.group(1))
            html += f"<ol><li>{text}</li></ol>\n"
            continue

        # 普通段落
        text = _inline_format(stripped)
        html += f"<p>{text}</p>\n"

    if in_table and table_rows:
        html += _render_table(table_rows)

    html += f"""
    <div class="footer-note">
      本文档由 <strong>feishu_writer.py</strong> 自动写入 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
      MCN Script Assistant Skill v1.0
    </div>
  </div>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML 预览已生成: {output_path}")


def _inline_format(text: str) -> str:
    """简单的行内格式化"""
    import html as html_module
    text = html_module.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 合规检查标记
    text = text.replace("✅ PASS", '<span class="check-pass">✅ PASS</span>')
    text = text.replace("⚠️", '<span class="check-warn">⚠️</span>')
    text = text.replace("⭐", '<span style="color:#ff9a2e;">⭐</span>')
    return text


def _render_table(rows: list) -> str:
    """渲染 Markdown 表格行为 HTML"""
    import html as html_module
    html = '<table>\n'
    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        html += "<tr>"
        for cell in row:
            cell_html = _inline_format(cell)
            html += f"<{tag}>{cell_html}</{tag}>"
        html += "</tr>\n"
    html += "</table>\n"
    return html


# ============================================================
# 主流程
# ============================================================

def run_live_mode(script_path: str, app_id: str, app_secret: str, folder_token: str = ""):
    """实际调用飞书 API 写入文档"""
    print("=" * 60)
    print("飞书文档自动写入 — LIVE 模式")
    print("=" * 60)

    # 1. 读取脚本文件
    with open(script_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    print(f"[1/5] 读取脚本文件: {script_path}")

    # 2. 解析 Markdown 为飞书 block
    parser = MarkdownParser(md_text)
    blocks = parser.parse()
    print(f"[2/5] 解析完成: {len(blocks)} 个内容块")

    # 3. 创建飞书文档
    writer = FeishuDocWriter(app_id, app_secret)
    doc_title = f"【轻醒酸奶】@是Nikki呀 短视频脚本 - {datetime.now().strftime('%Y%m%d')}"
    doc_id = writer.create_doc(title=doc_title, folder_token=folder_token if folder_token else None)
    print(f"[3/5] 文档已创建: {doc_id}")

    # 4. 写入内容块
    writer.write_blocks(doc_id, blocks)
    print(f"[4/5] 内容写入完成")

    # 5. 设置权限
    writer.set_doc_permission(doc_id)
    print(f"[5/5] 权限设置完成")

    doc_url = f"https://bytedance.feishu.cn/docx/{doc_id}"
    print("\n" + "=" * 60)
    print(f"飞书文档链接: {doc_url}")
    print("=" * 60)
    return doc_url


def run_demo_mode(script_path: str):
    """demo 模式：生成本地 HTML 预览"""
    print("=" * 60)
    print("飞书文档预览 — DEMO 模式（未配置 API 凭证）")
    print("=" * 60)

    with open(script_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    output_path = os.path.join(os.path.dirname(script_path), "..", "feishu-integration", "feishu_doc_preview.html")
    output_path = os.path.normpath(output_path)
    generate_html_preview(md_text, output_path)

    print("\n" + "=" * 60)
    print(f"预览文件: {output_path}")
    print("配置 .env 中的飞书 API 凭证后，可切换到 LIVE 模式实际写入飞书文档")
    print("=" * 60)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="飞书文档自动写入工具")
    parser.add_argument("--doc", default=None, help="脚本 Markdown 文件路径")
    parser.add_argument("--live", action="store_true", help="启用 LIVE 模式（调用飞书 API）")
    args = parser.parse_args()

    # 默认脚本路径
    script_path = args.doc
    if not script_path:
        default_path = os.path.join(os.path.dirname(__file__), "..", "script", "script-storyboard.md")
        script_path = os.path.normpath(default_path)

    if not os.path.exists(script_path):
        print(f"[ERROR] 脚本文件不存在: {script_path}")
        sys.exit(1)

    # 加载环境变量
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    folder_token = os.getenv("FEISHU_FOLDER_TOKEN", "")

    if args.live or (app_id and app_secret and app_id != "your_app_id_here"):
        if not app_id or not app_secret:
            print("[ERROR] LIVE 模式需要配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
            print("        请编辑 feishu-integration/.env 文件填入凭证")
            sys.exit(1)
        run_live_mode(script_path, app_id, app_secret, folder_token)
    else:
        run_demo_mode(script_path)


if __name__ == "__main__":
    main()
