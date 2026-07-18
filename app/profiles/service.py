from __future__ import annotations

import json
import re
from threading import Lock
from typing import Any

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
    "知识掌握": "当前学科的概念理解、知识基础与测评表现",
    "目标规划": "学习目标是否明确，并能否拆分为可执行计划",
    "策略运用": "是否形成适合自己的理解、记忆和练习方法",
    "实践迁移": "能否把知识用于题目、项目和新情境",
    "学习投入": "学习节奏、持续性与主动参与程度",
    "自我调节": "能否识别薄弱点、复盘错误并调整学习安排",
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
        active_provider: str = "siliconflow",
        spark_api_password: str = "",
        spark_base_url: str = "",
        spark_model: str = "",
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
                active_provider=active_provider,
                spark_api_password=spark_api_password,
                spark_base_url=spark_base_url,
                spark_model=spark_model,
            )
            provider = active_provider
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
        active_provider: str = "siliconflow",
        spark_api_password: str = "",
        spark_base_url: str = "",
        spark_model: str = "",
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
            question = self.llm.configured_generate(
                prompt,
                task="profile_interview",
                active_provider=active_provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                spark_api_password=spark_api_password,
                spark_base_url=spark_base_url,
                spark_model=spark_model,
                system_prompt="你是善于主动提问的学科学习画像访谈助手。",
                temperature=0.45,
                max_tokens=160,
            ).strip()
            provider = active_provider
        except ValueError as exc:
            question = self._fallback_question(course, missing)
            warning = str(exc)
        return {"question": question, "profile": current, "provider": provider, "warning": warning}

    def test_connection(self, *, api_key: str, base_url: str, model: str, **_: Any) -> dict[str, Any]:
        content = self.llm.siliconflow_generate(
            "只回复：连接成功",
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=32,
            temperature=0,
        )
        return {"status": "ok", "model": model, "message": content.strip()}

    def test_spark_connection(
        self,
        *,
        spark_api_password: str,
        spark_base_url: str,
        spark_model: str,
        **_: Any,
    ) -> dict[str, Any]:
        content = self.llm.spark_generate(
            "只回复：连接成功",
            spark_api_password=spark_api_password,
            spark_base_url=spark_base_url,
            spark_model=spark_model,
            max_tokens=32,
            temperature=0,
        )
        return {"status": "ok", "model": spark_model or self.llm.settings.spark_model, "message": content.strip()}

    def initialize_from_onboarding(self, user_id: str, onboarding_data: dict[str, Any]) -> None:
        grade_level = onboarding_data.get("grade_level", "")
        major = onboarding_data.get("major", "")
        weak_subjects = onboarding_data.get("weak_subjects", [])
        improvement_areas = onboarding_data.get("improvement_areas", [])
        learning_style = onboarding_data.get("learning_style", [])
        learning_goal = onboarding_data.get("learning_goal", "")

        base_dimensions: dict[str, Any] = {}
        if grade_level or major:
            base_dimensions["专业与年级"] = f"{major or '未明确'} / {grade_level or '未明确'}"
        if learning_goal:
            base_dimensions["学习目标"] = learning_goal
        if learning_style:
            base_dimensions["认知风格"] = "、".join(learning_style)
        if improvement_areas:
            base_dimensions["学习动机"] = "希望提升：" + "、".join(improvement_areas)
        if weak_subjects:
            base_dimensions["易错点"] = weak_subjects
        if learning_style:
            resource_map = {
                "视频讲解": "教学视频",
                "图文讲义": "讲解文档",
                "思维导图": "思维导图",
                "练习题": "练习题",
                "案例实践": "案例实践",
                "讨论交流": "讲解文档",
                "自主阅读": "讲解文档",
            }
            preferences: list[str] = []
            for style in learning_style:
                pref = resource_map.get(style)
                if pref and pref not in preferences:
                    preferences.append(pref)
            if preferences:
                base_dimensions["资源偏好"] = preferences

        if not base_dimensions:
            return

        evidence = "新用户初始画像问卷"
        courses = [course for course in weak_subjects if course and course != "未分类画像"]
        if not courses:
            return
        for course in courses[:3]:
            current = self.get_profile(user_id, course)
            if current.get("version", 0) > 0:
                continue
            course_dimensions = dict(base_dimensions)
            if weak_subjects and course in weak_subjects:
                course_dimensions["易错点"] = [course]
            with self._update_lock:
                profile = self._merge(current, course_dimensions, evidence)
                self.store.save(user_id, course, profile)

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
        active_provider: str,
        spark_api_password: str,
        spark_base_url: str,
        spark_model: str,
    ) -> tuple[dict[str, Any], str]:
        prompt = (
            "通过自然语言对话持续构建学生的单学科学习画像。只提取本轮有明确证据的维度，不要猜测；"
            "易错点和资源偏好使用数组。严格输出包含 reply 和 dimensions 的 JSON。\n"
            f"允许维度：{PROFILE_DIMENSIONS}\n学科：{course}\n"
            f"已有画像：{json.dumps(current.get('llm_context', {}), ensure_ascii=False)}\n"
            f"学生本轮输入：{message}"
        )
        raw = self.llm.configured_generate(
            prompt,
            task="profile",
            active_provider=active_provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            spark_api_password=spark_api_password,
            spark_base_url=spark_base_url,
            spark_model=spark_model,
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
        weak_candidates = [
            "函数依赖", "候选码", "范式判断", "关系模型", "SQL", "事务", "并发控制", "索引",
            "存储管理", "数据结构", "算法", "进程调度", "内存管理", "计算机网络", "软件工程",
        ]
        weak_points = [item for item in weak_candidates if item in message] or ["需要通过后续学习行为进一步识别"]
        preference_map = {
            "文档": "讲解文档",
            "讲解": "讲解文档",
            "思维导图": "思维导图",
            "练习": "练习题",
            "题": "练习题",
            "案例": "案例实践",
            "视频": "教学视频",
        }
        preferences: list[str] = []
        for key, value in preference_map.items():
            if key in message and value not in preferences:
                preferences.append(value)
        grade_level = next((grade for grade in ["大一", "大二", "大三", "大四", "研一", "研二", "研三"] if grade in message), "未明确")
        dimensions: dict[str, Any] = {
            "专业与年级": f"{'计算机科学与技术' if '计算机' in message else '未明确'} / {grade_level}",
            "学习目标": "考试复习" if any(word in message for word in ["考试", "复习", "期末"]) else "课程学习",
            "知识基础": "中等偏弱" if re.search(r"不太会|不会|薄弱|困难|看不懂", message) else "中等",
            "认知风格": "步骤化讲解" if any(word in message for word in ["步骤", "例题", "一步"]) else "概念讲解结合练习",
            "易错点": weak_points,
            "资源偏好": preferences or ["讲解文档", "练习题"],
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
        profile["radar_summaries"] = self._build_radar_summaries(profile)
        profile["llm_context"] = self._build_llm_context(profile)
        return profile

    @staticmethod
    def _dimension_value(profile: dict[str, Any], name: str, default: Any = None) -> Any:
        return profile.get("dimensions", {}).get(name, {}).get("value", default)

    def _build_radar_metrics(self, profile: dict[str, Any]) -> dict[str, int]:
        dimensions = profile.get("dimensions", {})
        knowledge_text = str(self._dimension_value(profile, "知识基础", ""))
        knowledge = 50
        score_match = re.search(r"(\d{1,3})%", knowledge_text)
        if score_match:
            knowledge = min(100, int(score_match.group(1)))
        elif any(word in knowledge_text for word in ["偏弱", "初学", "薄弱"]):
            knowledge = 35
        elif any(word in knowledge_text for word in ["熟练", "优秀", "进阶"]):
            knowledge = 82

        history_count = len(profile.get("history", []))
        has_goal = "学习目标" in dimensions
        has_motivation = "学习动机" in dimensions
        has_style = "认知风格" in dimensions
        has_resources = "资源偏好" in dimensions
        has_weakness = "易错点" in dimensions
        has_rhythm = "学习节奏" in dimensions
        return {
            "知识掌握": knowledge if "知识基础" in dimensions else 20,
            "目标规划": 88 if has_goal and has_motivation else 64 if has_goal else 24,
            "策略运用": 84 if has_style and has_resources else 62 if has_style or has_resources else 26,
            "实践迁移": min(90, 30 + history_count * 5 + (18 if has_weakness else 0) + (12 if "知识基础" in dimensions else 0)),
            "学习投入": min(95, 32 + history_count * 7 + (20 if has_rhythm else 0) + (10 if has_motivation else 0)),
            "自我调节": min(92, 28 + (26 if has_weakness else 0) + (20 if has_rhythm else 0) + (12 if has_goal else 0) + history_count * 3),
        }

    def _build_radar_summaries(self, profile: dict[str, Any]) -> dict[str, str]:
        dimensions = profile.get("dimensions", {})
        metrics = profile.get("radar_metrics", {})

        def value(name: str, fallback: str) -> str:
            raw = self._dimension_value(profile, name, "")
            if isinstance(raw, list):
                return "、".join(str(item) for item in raw if item) or fallback
            return str(raw).strip() or fallback

        def level(name: str) -> str:
            score = int(metrics.get(name, 0))
            if score >= 75:
                return "表现较稳定"
            if score >= 50:
                return "已有基础，仍可加强"
            return "当前信息较少，建议优先补充"

        knowledge = value("知识基础", "尚未形成明确的知识基础描述")
        goal = value("学习目标", "学习目标尚未明确")
        motivation = value("学习动机", "学习动机仍待了解")
        style = value("认知风格", "尚未识别稳定的学习方法")
        resources = value("资源偏好", "资源形式偏好仍待了解")
        weakness = value("易错点", "尚未识别明确薄弱点")
        rhythm = value("学习节奏", "学习频率和时间安排仍待了解")
        return {
            "知识掌握": f"{level('知识掌握')}。当前基础：{knowledge}。",
            "目标规划": f"{level('目标规划')}。目标：{goal}；动力来源：{motivation}。",
            "策略运用": f"{level('策略运用')}。学习方式：{style}；适合资源：{resources}。",
            "实践迁移": f"{level('实践迁移')}。当前重点应围绕“{weakness}”增加例题、练习与实际应用。",
            "学习投入": f"{level('学习投入')}。当前节奏：{rhythm}。",
            "自我调节": f"{level('自我调节')}。已识别问题：{weakness}；建议按学习结果持续复盘并调整计划。",
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
            "radar_summaries": profile.get("radar_summaries", {}),
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
