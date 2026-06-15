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

RADAR_DIMENSIONS = {
    "知识掌握": "反映当前学科知识基础与测评表现",
    "目标清晰": "反映学习目标和学习动机的明确程度",
    "学习策略": "反映认知风格和学习方法的成熟程度",
    "资源适配": "反映资源偏好是否已经识别",
    "学习投入": "反映学习节奏和持续学习证据",
    "画像可信": "反映画像维度覆盖率和证据可信度",
}


class DynamicProfileService:
    def __init__(self) -> None:
        self.store = ProfileStore()
        self.llm = LLMClient()
        self._update_lock = Lock()

    def get_profile(self, user_id: str, course: str | None = None) -> dict[str, Any]:
        profile = self.store.get(user_id, course)
        if profile:
            return self._enrich(profile)
        return self._empty_profile(user_id, course or "未指定学科")

    def list_profiles(self, user_id: str) -> list[dict[str, Any]]:
        return self.store.list(user_id)

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
        current = self.get_profile(user_id, course)
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
            known = set(current.get("dimensions", {})) | set(extracted)
            missing = [name for name in PROFILE_DIMENSIONS if name not in known]
            updated = "、".join(extracted.keys())
            reply = f"我已根据这次回答更新了{course}画像：{updated}。{self._fallback_question(course, missing)}"
            warning = str(exc)

        merged = self._merge_latest(user_id, course, extracted, message)
        return {
            "reply": reply,
            "profile": merged,
            "updated_dimensions": sorted(extracted.keys()),
            "provider": provider,
            "warning": warning,
        }

    def next_question(
        self,
        *,
        user_id: str,
        course: str,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
    ) -> dict[str, Any]:
        current = self.get_profile(user_id, course)
        missing = [name for name in PROFILE_DIMENSIONS if name not in current.get("dimensions", {})]
        provider = "rule-fallback"
        warning = ""
        try:
            prompt = (
                "你是主动式学科学习画像访谈助手。基于所选学科和已有画像，只提出一个简短、自然、容易回答的问题。"
                "优先询问缺失维度，不要一次问多个问题。\n"
                f"学科：{course}\n缺失维度：{missing}\n"
                f"已有画像：{json.dumps(current.get('llm_context', {}), ensure_ascii=False)}"
            )
            question = self.llm.siliconflow_generate(
                prompt,
                task="profile_interview",
                api_key=api_key,
                base_url=base_url,
                model=model,
                system_prompt="你是善于主动提问的学科学习画像访谈助手。",
                temperature=0.45,
                max_tokens=160,
            ).strip()
            provider = "siliconflow"
        except ValueError as exc:
            question = self._fallback_question(course, missing)
            warning = str(exc)
        return {"question": question, "profile": current, "provider": provider, "warning": warning}

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

    def update_from_evaluation(self, *, user_id: str, course: str, result: dict[str, Any]) -> dict[str, Any]:
        accuracy = result.get("score_summary", {}).get("accuracy")
        if accuracy is not None and float(accuracy) <= 1:
            accuracy = float(accuracy) * 100
        level = "待评估" if accuracy is None else f"最近评估正确率 {round(float(accuracy))}%"
        evidence = f"学科测评结果：{result.get('analysis', '')}"
        return self._merge_latest(
            user_id,
            course,
            {"易错点": result.get("weak_points", []), "知识基础": level},
            evidence,
        )

    def _merge_latest(self, user_id: str, course: str, extracted: dict[str, Any], evidence: str) -> dict[str, Any]:
        with self._update_lock:
            current = self.get_profile(user_id, course)
            profile = self._merge(current, extracted, evidence)
            return self.store.save(user_id, course, profile)

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
        prompt = (
            "通过自然语言对话持续构建学生的单学科学习画像。只提取本轮有明确证据的维度，不要猜测；"
            "易错点和资源偏好使用数组。严格输出包含 reply 和 dimensions 的 JSON。\n"
            f"允许维度：{PROFILE_DIMENSIONS}\n学科：{course}\n"
            f"已有画像：{json.dumps(current.get('llm_context', {}), ensure_ascii=False)}\n"
            f"学生本轮输入：{message}"
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
        return dimensions, str(data.get("reply") or f"我已更新你的{course}学习画像。")

    @staticmethod
    def _extract_with_rules(*, course: str, message: str) -> dict[str, Any]:
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
        profile = {
            "user_id": current["user_id"],
            "course": current["course"],
            "version": int(current.get("version", 0)) + 1,
            "dimensions": dimensions,
            "history": history,
            "updated_at": now,
            "completion": round(len(dimensions) / len(PROFILE_DIMENSIONS) * 100),
            "dimension_catalog": PROFILE_DIMENSIONS,
        }
        return self._enrich(profile)

    def _enrich(self, profile: dict[str, Any]) -> dict[str, Any]:
        profile.setdefault("course", "未分类画像")
        profile.setdefault("dimension_catalog", PROFILE_DIMENSIONS)
        profile["completion"] = min(100, round(len(profile.get("dimensions", {})) / len(PROFILE_DIMENSIONS) * 100))
        profile["radar_catalog"] = RADAR_DIMENSIONS
        profile["radar_metrics"] = self._build_radar_metrics(profile)
        profile["llm_context"] = self._build_llm_context(profile)
        return profile

    @staticmethod
    def _dimension_value(profile: dict[str, Any], name: str, default: Any = None) -> Any:
        return profile.get("dimensions", {}).get(name, {}).get("value", default)

    def _build_radar_metrics(self, profile: dict[str, Any]) -> dict[str, int]:
        dimensions = profile.get("dimensions", {})
        confidence_values = [float(item.get("confidence", 0)) for item in dimensions.values()]
        average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        knowledge_text = str(self._dimension_value(profile, "知识基础", ""))
        knowledge = 50
        score_match = re.search(r"(\d{1,3})%", knowledge_text)
        if score_match:
            knowledge = min(100, int(score_match.group(1)))
        elif any(word in knowledge_text for word in ["偏弱", "初学", "薄弱"]):
            knowledge = 35
        elif any(word in knowledge_text for word in ["熟练", "优秀", "进阶"]):
            knowledge = 82

        return {
            "知识掌握": knowledge if "知识基础" in dimensions else 20,
            "目标清晰": 85 if "学习目标" in dimensions and "学习动机" in dimensions else 60 if "学习目标" in dimensions else 20,
            "学习策略": 78 if "认知风格" in dimensions else 25,
            "资源适配": 82 if "资源偏好" in dimensions else 25,
            "学习投入": min(95, 35 + len(profile.get("history", [])) * 7 + (20 if "学习节奏" in dimensions else 0)),
            "画像可信": min(100, round(average_confidence * 70 + profile.get("completion", 0) * 0.3)),
        }

    def _build_llm_context(self, profile: dict[str, Any]) -> dict[str, Any]:
        facts = {
            name: data.get("value")
            for name, data in profile.get("dimensions", {}).items()
            if data.get("value") not in ("", [], None)
        }
        weak_points = facts.get("易错点", [])
        preferences = facts.get("资源偏好", [])
        summary_parts = [f"学科：{profile.get('course', '未指定学科')}"]
        for name in ["学习目标", "知识基础", "认知风格", "学习节奏"]:
            if name in facts:
                summary_parts.append(f"{name}：{facts[name]}")
        if weak_points:
            summary_parts.append(f"重点薄弱项：{'、'.join(weak_points) if isinstance(weak_points, list) else weak_points}")
        return {
            "schema_version": "subject-profile-v1",
            "instruction": "仅将本画像用于当前学科的个性化教学、资源生成和学习评估；不确定信息不得当作事实。",
            "user_id": profile.get("user_id"),
            "course": profile.get("course"),
            "summary": "；".join(summary_parts),
            "facts": facts,
            "weak_points": weak_points if isinstance(weak_points, list) else [weak_points],
            "resource_preferences": preferences if isinstance(preferences, list) else [preferences],
            "radar_metrics": profile.get("radar_metrics", {}),
            "completion": profile.get("completion", 0),
            "updated_at": profile.get("updated_at"),
        }

    def _empty_profile(self, user_id: str, course: str) -> dict[str, Any]:
        return self._enrich(
            {
                "user_id": user_id,
                "course": course,
                "version": 0,
                "dimensions": {},
                "history": [],
                "updated_at": None,
                "completion": 0,
                "dimension_catalog": PROFILE_DIMENSIONS,
            }
        )

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
    def _fallback_question(course: str, missing: list[str]) -> str:
        target = missing[0] if missing else "当前最需要提升的方面"
        questions = {
            "专业与年级": "先认识一下你：你的专业和当前年级是什么？",
            "学习目标": f"你学习《{course}》最想达成什么目标？",
            "知识基础": f"你觉得自己目前对《{course}》掌握到什么程度？",
            "认知风格": "遇到新知识时，你更容易通过概念讲解、图示、例题还是动手实践理解？",
            "易错点": f"学习《{course}》时，你最容易在哪些知识点或题型上出错？",
            "资源偏好": "你更喜欢视频、讲义、思维导图、练习题还是项目案例？",
            "学习节奏": "你通常在什么时间学习，每次大约能专注多久？",
            "学习动机": f"是什么促使你现在重点学习《{course}》？",
        }
        if not missing:
            return f"关于《{course}》，最近有什么新的困难、目标或学习习惯需要更新进画像？"
        return questions[target]
