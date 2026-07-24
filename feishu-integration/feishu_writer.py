"""
MCN Script Assistant - 飞书文档自动化写入模块
将生成的脚本文档自动写入飞书文档
"""

import json
import requests
from datetime import datetime


class FeishuDocWriter:
    """飞书文档写入器"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self._tenant_access_token = None

    def _get_tenant_access_token(self) -> str:
        """获取 tenant_access_token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取token失败: {data}")
        self._tenant_access_token = data["tenant_access_token"]
        return self._tenant_access_token

    def _headers(self) -> dict:
        if not self._tenant_access_token:
            self._get_tenant_access_token()
        return {
            "Authorization": f"Bearer {self._tenant_access_token}",
            "Content-Type": "application/json"
        }

    def create_doc(self, title: str, folder_token: str = None) -> str:
        """创建飞书文档，返回文档 ID"""
        url = f"{self.base_url}/docx/v1/documents"
        body = {"title": title}
        if folder_token:
            body["folder_token"] = folder_token
        resp = requests.post(url, headers=self._headers(), json=body)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"创建文档失败: {data}")
        doc_id = data["data"]["document"]["document_id"]
        print(f"文档创建成功: https://bytedance.feishu.cn/docx/{doc_id}")
        return doc_id

    def write_content(self, doc_id: str, content_blocks: list):
        """向文档写入内容块"""
        url = f"{self.base_url}/docx/v1/documents/{doc_id}/blocks/batch_create"
        body = {
            "children": content_blocks,
            "index": 0
        }
        resp = requests.post(url, headers=self._headers(), json=body)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"写入内容失败: {data}")
        print(f"内容写入成功到文档: {doc_id}")


def build_script_blocks(script_data: dict) -> list:
    """将脚本数据构建为飞书文档内容块"""

    blocks = []

    # 标题块
    blocks.append({
        "block_type": 2,
        "heading1": {
            "elements": [{
                "text_run": {"content": script_data.get("标题", "短视频脚本")}
            }]
        }
    })

    # 基本信息
    for key, value in script_data.get("基本信息", {}).items():
        blocks.append({
            "block_type": 2,
            "text": {
                "elements": [
                    {"text_run": {"content": f"{key}：", "text_element_style": {"bold": True}}},
                    {"text_run": {"content": value}}
                ]
            }
        })

    # 分隔线
    blocks.append({"block_type": 18})

    # 分镜内容
    for shot in script_data.get("分镜", []):
        blocks.append({
            "block_type": 2,
            "heading2": {
                "elements": [{"text_run": {"content": shot.get("标题", "")}}]
            }
        })

        for key, value in shot.get("内容", {}).items():
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [
                        {"text_run": {"content": f"{key}：", "text_element_style": {"bold": True}}},
                        {"text_run": {"content": value}}
                    ]
                }
            })

    # 合规检查
    blocks.append({"block_type": 18})
    blocks.append({
        "block_type": 2,
        "heading2": {
            "elements": [{"text_run": {"content": "合规检查"}}]
        }
    })

    for item in script_data.get("合规检查", []):
        blocks.append({
            "block_type": 2,
            "text": {
                "elements": [{"text_run": {"content": f"{item.get('status')} {item.get('item')}: {item.get('说明')}"}}]
            }
        })

    return blocks


def main():
    """主流程：将脚本写入飞书文档"""

    # TODO: 从环境变量或配置文件读取
    import os
    APP_ID = os.getenv("FEISHU_APP_ID", "your_app_id")
    APP_SECRET = os.getenv("FEISHU_APP_SECRET", "your_app_secret")
    FOLDER_TOKEN = os.getenv("FEISHU_FOLDER_TOKEN", "")

    # 示例脚本数据
    script_data = {
        "标题": "打工人5分钟高蛋白早餐！这个蓝莓希腊酸奶真的绝了",
        "基本信息": {
            "达人": "@是Nikki呀",
            "品牌": "轻醒 0蔗糖高蛋白希腊酸奶",
            "时长": "约45秒",
            "创作日期": datetime.now().strftime("%Y-%m-%d")
        },
        "分镜": [
            {
                "标题": "分镜1 · 开场钩子（0-5秒）",
                "内容": {
                    "画面": "俯拍闹钟响起，手按掉闹钟，切到厨房",
                    "口播": "姐妹们，打工人早上真的来不及做早餐啊！",
                    "字幕": "打工人早上有多赶？"
                }
            },
            {
                "标题": "分镜2 · 痛点共鸣（5-12秒）",
                "内容": {
                    "画面": "博主半身，厨房自然光，无奈表情",
                    "口播": "以前我都是随便塞两片面包就出门，到10点就饿了。",
                    "字幕": "随便吃 -> 饿 -> 没精神"
                }
            },
            {
                "标题": "分镜3 · 解决方案引入（12-20秒）",
                "内容": {
                    "画面": "打开冰箱，取出蓝莓味酸奶",
                    "口播": "后来我发现这个希腊酸奶，配点水果5分钟搞定！",
                    "字幕": "5分钟高蛋白早餐"
                }
            },
            {
                "标题": "分镜4 · 产品展示制作（20-32秒）",
                "内容": {
                    "画面": "俯拍打开酸奶展示质地，加蓝莓和燕麦",
                    "口播": "质地特别醇厚，高蛋白0蔗糖，早上吃没负担。加蓝莓和燕麦口感超好。",
                    "字幕": "醇厚 | 高蛋白 | 0蔗糖 | +水果+燕麦"
                }
            },
            {
                "标题": "分镜5 · 食用体验（32-40秒）",
                "内容": {
                    "画面": "博主坐在餐桌前吃酸奶，近景，表情满足",
                    "口播": "这样一碗吃下去到中午都不怎么饿。下午当下午茶也完全OK。",
                    "字幕": "饱腹感强 | 下午茶也OK"
                }
            },
            {
                "标题": "分镜6 · 结尾互动（40-45秒）",
                "内容": {
                    "画面": "博主微笑对镜头，酸奶正面朝向镜头",
                    "口播": "有好几个口味，我最近超爱蓝莓的！你们早上都吃什么呀？评论区告诉我~",
                    "字幕": "原味/蓝莓/黄桃 | 评论区聊聊早餐"
                }
            }
        ],
        "合规检查": [
            {"status": "✅", "item": "减肥功效宣称", "说明": "全文无减肥/瘦身/减脂词汇"},
            {"status": "✅", "item": "降糖功效宣称", "说明": "仅说明0蔗糖产品属性"},
            {"status": "✅", "item": "医疗暗示", "说明": "无任何医疗相关表述"},
            {"status": "✅", "item": "虚假夸大", "说明": "真实体验描述"},
            {"status": "⚠️", "item": "广告标识", "说明": "发布时需添加合作标签"}
        ]
    }

    writer = FeishuDocWriter(APP_ID, APP_SECRET)
    doc_id = writer.create_doc(
        title=f"【轻醒酸奶】@{script_data['基本信息']['达人']} 短视频脚本 - {datetime.now().strftime('%Y%m%d')}",
        folder_token=FOLDER_TOKEN if FOLDER_TOKEN else None
    )
    blocks = build_script_blocks(script_data)
    writer.write_content(doc_id, blocks)

    print(f"
飞书文档链接: https://bytedance.feishu.cn/docx/{doc_id}")


if __name__ == "__main__":
    main()
