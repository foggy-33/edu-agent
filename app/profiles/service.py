from __future__ import annotations

import json
import re
from threading import Lock
from typing import Any

from app.agents.profile_agent import ProfileAgent
from app.core.llm_client import LLMClient
from app.profiles.store import ProfileStore, utc_now


PROFILE_DIMENSIONS = [
    "专业与年级",
    "学习目标",
    "知识基础",
    "认知风格",
    "易错点",
    "资源偏好",
    "学习节奏",
    "学习动机",
]


class DynamicProfileService:
    def __init__(self) -> None:
        self.store = ProfileStore()
        self.llm = LLMClient()
        self._update_lock = Lock()

    def get_profile(self, user_id: str) -> dict[str, Any]:
        return self.store.get(user_id) or self._empty_profile(user_id)

    def update_from_chat(
        self,
        *,
        user_id: str,
        course: str,
        message: str,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
    ) -> dict[str, Any]:
        current = self.get_profile(user_id)
        provider = "rule-fallback"
        warning = ""

        try:
            extracted, reply = self._extract_with_llm(
                current=current,
                course=course,
                message=message,
                api_key=api_key,
                base_url=base_url,
                model=model,
            )
            provider = "siliconflow"
        except ValueError as exc:
            extracted = self._extract_with_rules(course=course, message=message)
            reply = self._fallback_reply(extracted)
            warning = str(exc)

        merged = self._merge_latest(user_id, extracted, message)
        return {
            "reply": reply,
            "profile": merged,
            "updated_dimensions": sorted(extracted.keys()),
            "provider": provider,
            "warning": warning,
        }

    def test_connection(self, *, api_key: str, base_url: str, model: str) -> dict[str, Any]:
        content = self.llm.siliconflow_generate(
            "只回复：连接成功",
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=32,
            temperature=0,
        )
        return {"status": "ok", "model": model, "message": content.strip()}

    def update_from_evaluation(self, *, user_id: str, result: dict[str, Any]) -> dict[str, Any]:
        accuracy = result.get("score_summary", {}).get("accuracy")
        level = "待评估" if accuracy is None else f"最近评估正确率 {round(float(accuracy) * 100)}%"
        evidence = f"学习评估结果：{result.get('analysis', '')}"
        return self._merge_latest(
            user_id,
            {"易错点": result.get("weak_points", []), "知识基础": level},
            evidence,
        )

    def _merge_latest(self, user_id: str, extracted: dict[str, Any], evidence: str) -> dict[str, Any]:
        with self._update_lock:
            current = self.get_profile(user_id)
            return self.store.save(user_id, self._merge(current, extracted, evidence))

    def _extract_with_llm(
        self,
        *,
        current: dict[str, Any],
        course: str,
        message: str,
        api_key: str,
        base_url: str,
        model: str,
    ) -> tuple[dict[str, Any], str]:
        schema = {
            "reply": "给学生的自然、简短回应，并追问一个最有价值的画像问题",
            "dimensions": {
                "专业与年级": "字符串",
                "学习目标": "字符串",
                "知识基础": "字符串",
                "认知风格": "字符串",
                "易错点": ["字符串"],
                "资源偏好": ["字符串"],
                "学习节奏": "字符串",
                "学习动机": "字符串",
            },
        }
        prompt = (
            "你负责通过自然语言对话持续构建学生画像。只提取本轮有明确证据的维度，"
            "不要猜测；未出现的维度不要放入 dimensions。易错点和资源偏好使用数组。"
            "reply 应确认本轮理解，并追问一个最能补全画像的问题。\n"
            f"课程：{course}\n"
            f"现有画像：{json.dumps(current.get('dimensions', {}), ensure_ascii=False)}\n"
            f"学生本轮输入：{message}\n"
            f"严格输出 JSON：{json.dumps(schema, ensure_ascii=False)}"
        )
        raw = self.llm.siliconflow_generate(
            prompt,
            task="profile",
            api_key=api_key,
            base_url=base_url,
            model=model,
            system_prompt="你是学生画像分析专家，只输出合法 JSON。",
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = self._parse_json(raw)
        dimensions = {
            key: value
            for key, value in data.get("dimensions", {}).items()
            if key in PROFILE_DIMENSIONS and value not in ("", [], None)
        }
        return dimensions, str(data.get("reply") or "我已根据这次交流更新了你的学习画像。")

    def _extract_with_rules(self, *, course: str, message: str) -> dict[str, Any]:
        basic = ProfileAgent().run({"course": course, "message": message})
        dimensions: dict[str, Any] = {
            "专业与年级": f"{basic['major']} / {basic['grade_level']}",
            "学习目标": basic["learning_goal"],
            "知识基础": basic["knowledge_level"],
            "认知风格": basic["learning_style"],
            "易错点": basic["weak_points"],
            "资源偏好": basic["resource_preference"],
        }
        if re.search(r"每天|周末|晚上|早上|分钟|小时", message):
            dimensions["学习节奏"] = message[:100]
        if re.search(r"考试|竞赛|工作|保研|兴趣|面试", message):
            dimensions["学习动机"] = message[:100]
        return dimensions

    def _merge(self, current: dict[str, Any], extracted: dict[str, Any], evidence: str) -> dict[str, Any]:
        dimensions = dict(current.get("dimensions", {}))
        now = utc_now()
        for key, value in extracted.items():
            old_value = dimensions.get(key, {}).get("value")
            if isinstance(value, list) and isinstance(old_value, list):
                value = list(dict.fromkeys([*old_value, *value]))[-8:]
            dimensions[key] = {
                "value": value,
                "confidence": min(0.95, 0.58 + 0.08 * len(current.get("history", []))),
                "updated_at": now,
                "evidence": evidence[:180],
            }

        history = [*current.get("history", []), {"role": "user", "content": evidence, "created_at": now}][-20:]
        return {
            "user_id": current["user_id"],
            "version": int(current.get("version", 0)) + 1,
            "dimensions": dimensions,
            "history": history,
            "updated_at": now,
            "completion": round(len(dimensions) / len(PROFILE_DIMENSIONS) * 100),
            "dimension_catalog": PROFILE_DIMENSIONS,
        }

    def _empty_profile(self, user_id: str) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "version": 0,
            "dimensions": {},
            "history": [],
            "updated_at": None,
            "completion": 0,
            "dimension_catalog": PROFILE_DIMENSIONS,
        }

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise ValueError("模型未返回可解析的画像 JSON")
            return json.loads(match.group(0))

    @staticmethod
    def _fallback_reply(extracted: dict[str, Any]) -> str:
        updated = "、".join(extracted.keys())
        return f"我已经根据这次交流更新了：{updated}。你通常在什么时间学习，每次能持续多久？"
