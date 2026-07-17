from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from app.auth.service import AuthService
from app.core.config import get_settings
from app.mistakes.store import MistakeStore
from app.profiles.service import DynamicProfileService
from app.resources.service import ResourceService


class LearningStatsService:
    def __init__(self) -> None:
        self.mistake_store = MistakeStore()
        self.profile_service = DynamicProfileService()
        self.resource_service = ResourceService()
        self.auth_service = AuthService()

    def get_overall_stats(self, user_id: str) -> dict[str, Any]:
        mistake_stats = self.mistake_store.get_mistake_stats(user_id)
        total_mistakes = sum(s["total_count"] for s in mistake_stats)
        mastered_mistakes = sum(s["mastered_count"] for s in mistake_stats)
        unmastered_mistakes = sum(s["unmastered_count"] for s in mistake_stats)

        try:
            resources = self.resource_service.list_resources(user_id)
        except Exception:
            resources = []
        total_resources = len(resources)
        generated_resources = sum(1 for r in resources if r.get("source_type") == "generated")
        uploaded_resources = sum(1 for r in resources if r.get("source_type") == "uploaded")

        profiles = self.profile_service.list_profiles(user_id)
        course_count = len(profiles)

        total_study_minutes = self._estimate_study_minutes(
            total_resources=total_resources,
            total_mistakes=total_mistakes,
            profiles=profiles,
        )
        total_study_hours = round(total_study_minutes / 60, 1)

        correct_rate = 0
        if total_mistakes > 0 and mastered_mistakes > 0:
            correct_rate = round((mastered_mistakes / total_mistakes) * 100)
        elif total_mistakes == 0 and total_resources > 0:
            correct_rate = 75
        else:
            correct_rate = 0

        streak_days = self._calculate_streak_days(user_id)

        completed_courses = sum(1 for p in profiles if p.get("completed", False))
        if completed_courses == 0 and course_count > 0:
            completed_courses = min(course_count, 1)

        combined_radar = self._combine_radar_metrics(profiles)
        combined_summary = self._combine_profile_summaries(profiles)
        all_weak_topics = self._collect_all_weak_topics(user_id, profiles)
        user_info = self._get_user_basic_info(user_id)

        return {
            "total_study_hours": total_study_hours,
            "completed_courses": completed_courses,
            "correct_rate": correct_rate,
            "streak_days": streak_days,
            "total_mistakes": total_mistakes,
            "mastered_mistakes": mastered_mistakes,
            "unmastered_mistakes": unmastered_mistakes,
            "total_resources": total_resources,
            "generated_resources": generated_resources,
            "uploaded_resources": uploaded_resources,
            "course_count": course_count,
            "course_stats": mistake_stats,
            "combined_radar": combined_radar,
            "combined_summary": combined_summary,
            "all_weak_topics": all_weak_topics,
            "major": user_info.get("major", "未填写"),
            "grade_level": user_info.get("grade_level", "未填写"),
        }

    def get_course_stats(self, user_id: str, course: str) -> dict[str, Any]:
        mistakes = self.mistake_store.list_mistakes(user_id, course)
        mastered_mistakes = self.mistake_store.list_mistakes(user_id, course, mastered=True)
        total_mistakes = len(mistakes) + len(mastered_mistakes)
        weak_topics = self.mistake_store.get_weak_topics(user_id, course, limit=5)

        profile = self.profile_service.get_profile(user_id, course)
        radar_metrics = profile.get("radar_metrics", {})
        dimensions = profile.get("dimensions", {})

        try:
            resources = self.resource_service.list_resources(user_id)
            course_resources = [
                r for r in resources
                if r.get("course_folder", "").lower() == course.lower()
            ]
        except Exception:
            course_resources = []

        study_minutes = self._estimate_study_minutes(
            total_resources=len(course_resources),
            total_mistakes=total_mistakes,
            profiles=[profile] if profile.get("course") else [],
        )

        correct_rate = 0
        if total_mistakes > 0:
            correct_rate = round((len(mastered_mistakes) / total_mistakes) * 100)
        elif len(course_resources) > 0:
            correct_rate = 70

        weekly_hours = self._estimate_weekly_hours(study_minutes)
        weak_points_detail = self._analyze_weak_points_detail(user_id, course, weak_topics)
        user_info = self._get_user_basic_info(user_id)

        profile_learning_goal = profile.get("learning_goal", "")
        profile_knowledge_level = profile.get("knowledge_level", "")
        profile_learning_style = profile.get("learning_style", "")

        final_learning_goal = profile_learning_goal or user_info.get("learning_goal", "未设定")
        final_knowledge_level = profile_knowledge_level or "待评估"
        final_learning_style = profile_learning_style or "、".join(user_info.get("learning_style", [])) or "待分析"

        suggestions = self._generate_suggestions(
            weak_topics=weak_topics,
            weak_points_detail=weak_points_detail,
            knowledge_level=final_knowledge_level,
            learning_style=final_learning_style,
            total_mistakes=total_mistakes,
            resource_count=len(course_resources),
            learning_goal=final_learning_goal,
            correct_rate=correct_rate,
        )

        return {
            "course": course,
            "study_minutes": study_minutes,
            "study_hours": round(study_minutes / 60, 1),
            "total_mistakes": total_mistakes,
            "unmastered_mistakes": len(mistakes),
            "mastered_mistakes": len(mastered_mistakes),
            "correct_rate": correct_rate,
            "weak_topics": weak_topics,
            "weak_points_detail": weak_points_detail,
            "resource_count": len(course_resources),
            "radar_metrics": radar_metrics,
            "dimensions": dimensions,
            "profile_summary": profile.get("summary", ""),
            "learning_goal": final_learning_goal,
            "knowledge_level": final_knowledge_level,
            "learning_style": final_learning_style,
            "weekly_hours": weekly_hours,
            "suggestions": suggestions,
            "display_name": user_info.get("display_name", "学习者"),
            "major": user_info.get("major", "未填写"),
            "grade_level": user_info.get("grade_level", "未填写"),
            "school": user_info.get("school", "未填写"),
            "weak_subjects": user_info.get("weak_subjects", []),
            "improvement_areas": user_info.get("improvement_areas", []),
        }

    @staticmethod
    def _combine_radar_metrics(profiles: list[dict[str, Any]]) -> dict[str, int]:
        all_metrics: dict[str, list[int]] = {}
        for p in profiles:
            metrics = p.get("radar_metrics", {}) or {}
            for key, value in metrics.items():
                if key not in all_metrics:
                    all_metrics[key] = []
                all_metrics[key].append(int(value) if isinstance(value, (int, float)) else 50)
        result = {}
        for key, values in all_metrics.items():
            if values:
                result[key] = round(sum(values) / len(values))
        if not result:
            result = {
                "概念理解": 60,
                "应用迁移": 55,
                "练习表现": 58,
                "学习稳定性": 50,
                "资源偏好": 62,
            }
        return result

    @staticmethod
    def _combine_profile_summaries(profiles: list[dict[str, Any]]) -> str:
        summaries = []
        for p in profiles:
            s = p.get("summary", "")
            if s and len(s) > 10:
                summaries.append(s)
        if summaries:
            return summaries[0]
        return "正在综合评估你的学习情况..."

    def _collect_all_weak_topics(self, user_id: str, profiles: list[dict[str, Any]]) -> list[str]:
        all_topics: list[str] = []
        for p in profiles:
            course = p.get("course", "")
            if course:
                topics = self.mistake_store.get_weak_topics(user_id, course, limit=3)
                all_topics.extend(topics)
        if not all_topics:
            for p in profiles:
                weak = p.get("weak_points", [])
                if weak:
                    all_topics.extend(weak[:2])
        return list(dict.fromkeys(all_topics))[:10]

    def _get_user_basic_info(self, user_id: str) -> dict[str, Any]:
        try:
            user = self.auth_service.get_user_by_username(user_id)
            if not user:
                return {}
            profile = user.get("onboarding_profile", {}) or {}

            display_name = user.get("display_name", "")
            school = user.get("school", "") or profile.get("school", "")
            major = user.get("major", "") or profile.get("major", "") or profile.get("profession", "")
            grade_level = user.get("grade_level", "") or profile.get("study_stage", "") or profile.get("grade", "") or profile.get("grade_level", "")
            learning_goal = user.get("learning_goal", "") or profile.get("learning_goal", "")
            weak_subjects = profile.get("weak_subjects", []) or []
            improvement_areas = profile.get("improvement_areas", []) or []
            learning_style = profile.get("learning_style", []) or []

            return {
                "display_name": display_name or "学习者",
                "major": major or "未填写",
                "grade_level": grade_level or "未填写",
                "school": school or "未填写",
                "weak_subjects": weak_subjects,
                "improvement_areas": improvement_areas,
                "learning_style": learning_style,
                "learning_goal": learning_goal or "未设定",
            }
        except Exception:
            return {}

    def _analyze_weak_points_detail(
        self,
        user_id: str,
        course: str,
        weak_topics: list[str],
    ) -> list[dict[str, Any]]:
        mistakes = self.mistake_store.list_mistakes(user_id, course)
        mastered_mistakes = self.mistake_store.list_mistakes(user_id, course, mastered=True)
        all_mistakes = mistakes + mastered_mistakes

        result = []
        for topic in weak_topics:
            topic_mistakes = [
                m for m in all_mistakes
                if (m.get("chapter") or m.get("topic") or "综合") == topic
            ]
            topic_unmastered = [
                m for m in topic_mistakes if not m.get("mastered")
            ]
            topic_mastered = [
                m for m in topic_mistakes if m.get("mastered")
            ]
            total_count = len(topic_mistakes)
            unmastered_count = len(topic_unmastered)
            mastered_count = len(topic_mastered)
            total_mistake_count = sum(m.get("mistake_count", 1) for m in topic_mistakes)

            master_rate = 0
            if total_count > 0:
                master_rate = round((mastered_count / total_count) * 100)

            levels = [m.get("level", "") for m in topic_mistakes if m.get("level")]
            type_counts: dict[str, int] = {}
            for m in topic_mistakes:
                t = m.get("type", "其他")
                type_counts[t] = type_counts.get(t, 0) + 1
            most_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "综合"

            level_map = {"简单": 1, "中等": 2, "困难": 3}
            avg_level = 0
            if levels:
                level_values = [level_map.get(l, 2) for l in levels]
                avg_level = round(sum(level_values) / len(level_values), 1)
            level_label = "简单" if avg_level <= 1.3 else ("中等" if avg_level <= 2.3 else "困难")

            error_patterns = self._analyze_error_patterns(topic_mistakes)
            analysis_summary = self._generate_analysis_summary(
                topic=topic,
                master_rate=master_rate,
                total_count=total_count,
                unmastered_count=unmastered_count,
                total_mistake_count=total_mistake_count,
                level_label=level_label,
                most_type=most_type,
                error_patterns=error_patterns,
            )
            suggestions = self._generate_topic_suggestions(
                topic=topic,
                master_rate=master_rate,
                unmastered_count=unmastered_count,
                level_label=level_label,
                most_type=most_type,
                error_patterns=error_patterns,
            )

            result.append({
                "topic": topic,
                "total_count": total_count,
                "unmastered_count": unmastered_count,
                "mastered_count": mastered_count,
                "total_mistake_count": total_mistake_count,
                "master_rate": master_rate,
                "avg_level": level_label,
                "most_type": most_type,
                "analysis_summary": analysis_summary,
                "suggestion": suggestions,
            })

        return result

    @staticmethod
    def _analyze_error_patterns(topic_mistakes: list[dict[str, Any]]) -> list[str]:
        patterns = []
        if not topic_mistakes:
            return patterns

        type_map = {
            "choice": "概念辨析类",
            "single": "概念辨析类",
            "multiple": "多概念综合类",
            "judge": "概念理解类",
            "fill": "记忆背诵类",
            "short": "应用表达类",
            "essay": "综合应用类",
        }

        type_counts: dict[str, int] = {}
        for m in topic_mistakes:
            t = m.get("type", "其他")
            category = type_map.get(t, "综合类")
            type_counts[category] = type_counts.get(category, 0) + 1

        if type_counts:
            sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
            top_type = sorted_types[0][0]
            patterns.append(f"主要错误集中在{top_type}题目")

        hard_count = sum(1 for m in topic_mistakes if m.get("level") == "困难")
        easy_count = sum(1 for m in topic_mistakes if m.get("level") == "简单")
        if hard_count > len(topic_mistakes) * 0.4:
            patterns.append("高难度题目失分较多")
        if easy_count > len(topic_mistakes) * 0.3:
            patterns.append("基础题也存在失分，说明概念不牢")

        repeat_mistakes = sum(1 for m in topic_mistakes if m.get("mistake_count", 1) >= 2)
        if repeat_mistakes > len(topic_mistakes) * 0.3:
            patterns.append("存在反复出错的情况，知识巩固不足")

        return patterns[:3]

    @staticmethod
    def _generate_analysis_summary(
        *,
        topic: str,
        master_rate: int,
        total_count: int,
        unmastered_count: int,
        total_mistake_count: int,
        level_label: str,
        most_type: str,
        error_patterns: list[str],
    ) -> str:
        type_labels = {
            "choice": "选择题",
            "single": "单选题",
            "multiple": "多选题",
            "judge": "判断题",
            "fill": "填空题",
            "short": "简答题",
            "essay": "论述题",
        }
        type_label = type_labels.get(most_type, most_type + "题")

        if master_rate < 30:
            severity = "严重薄弱"
            desc = "基础概念掌握不足，需要系统性补漏"
        elif master_rate < 60:
            severity = "较为薄弱"
            desc = "有一定基础但知识漏洞较多，需要针对性巩固"
        elif master_rate < 80:
            severity = "基本掌握"
            desc = "整体掌握尚可，但部分细节和难题有待突破"
        else:
            severity = "掌握良好"
            desc = "知识掌握扎实，可向更高层次拓展"

        pattern_desc = "；".join(error_patterns[:2]) if error_patterns else "错误类型较为分散"

        return (
            f"「{topic}」{severity}：共做错 {total_count} 道题（累计错误 {total_mistake_count} 次），"
            f"掌握率 {master_rate}%，还有 {unmastered_count} 道待复习。"
            f"平均难度{level_label}，以{type_label}为主。{desc}。{pattern_desc}。"
        )

    @staticmethod
    def _generate_topic_suggestions(
        *,
        topic: str,
        master_rate: int,
        unmastered_count: int,
        level_label: str,
        most_type: str,
        error_patterns: list[str],
    ) -> str:
        suggestions = []

        if master_rate < 30:
            suggestions.append(
                f"回归课本，系统梳理「{topic}」的核心概念和定义，"
                f"建议用思维导图整理知识框架，确保每个基础知识点都理解到位。"
            )
            suggestions.append(
                "从最简单的例题开始重做，每做完一道题都要对照答案分析，"
                "弄清楚错在哪里、为什么错，不要急于做难题。"
            )
            suggestions.append(
                f"每天花 20-30 分钟专门复习「{topic}」基础内容，"
                "连续 3-5 天后再做练习题检验效果。"
            )
        elif master_rate < 60:
            suggestions.append(
                f"针对「{topic}」整理错题本，把做错的题目按类型分类，"
                f"分析每类题目的错误原因，是概念不清还是审题失误。"
            )
            if unmastered_count > 0:
                suggestions.append(
                    f"优先攻克当前 {unmastered_count} 道未掌握的错题，"
                    "每题重做 2-3 遍直到能独立做对为止。"
                )
            suggestions.append(
                f"找一些{level_label}难度的专项练习题，每天做 5-10 道，"
                "边做边总结解题方法和套路。"
            )
            suggestions.append(
                "学完一个小模块后及时做小结，用自己的话复述知识点，"
                "检验是否真正理解而不是死记硬背。"
            )
        elif master_rate < 80:
            suggestions.append(
                f"「{topic}」整体掌握不错，重点练习{level_label}难度的题目，"
                "多做一些综合性强的题型，加强知识迁移能力。"
            )
            suggestions.append(
                "把错题中反复出错的地方找出来，分析是思路问题还是计算问题，"
                "针对性地加强训练。"
            )
            suggestions.append(
                "尝试做一些跨章节的综合题，将「{topic}」与其他知识点联系起来，"
                "构建完整的知识体系。"
            )
        else:
            suggestions.append(
                f"「{topic}」掌握良好（{master_rate}%），建议定期复习保持手感，"
                "每周做 3-5 道相关题目防止遗忘。"
            )
            suggestions.append(
                "可以尝试更高难度的拓展题，加深对知识点的理解深度。"
            )
            suggestions.append(
                "尝试给同学讲解「{topic}」的知识点，费曼学习法能帮你发现知识盲区，"
                "同时巩固已有掌握。"
            )

        if any("反复出错" in p for p in error_patterns):
            suggestions.append(
                "建立错题复习机制，每周日回顾本周错题，"
                "对反复出错的题目做上标记，重点攻克。"
            )

        if any("基础题" in p for p in error_patterns):
            suggestions.append(
                "不要轻视简单题，基础概念是难题的根基。"
                "建议把课本上的基础例题全部重做一遍，确保万无一失。"
            )

        unique_suggestions = list(dict.fromkeys(suggestions))
        return "\n".join(f"{i+1}. {s}" for i, s in enumerate(unique_suggestions[:4]))

    @staticmethod
    def _estimate_study_minutes(
        *,
        total_resources: int,
        total_mistakes: int,
        profiles: list[dict[str, Any]],
    ) -> int:
        minutes = 0
        minutes += total_resources * 25
        minutes += total_mistakes * 8
        dimension_count = 0
        for p in profiles:
            dims = p.get("dimensions", {})
            dimension_count += len(dims)
        minutes += dimension_count * 5
        return max(minutes, 0)

    def _estimate_weekly_hours(self, total_minutes: int) -> list[int]:
        avg_daily = max(1, total_minutes // 7)
        random.seed(total_minutes)
        weekly = []
        remaining = total_minutes
        for i in range(7):
            if i == 6:
                weekly.append(max(0, round(remaining / 60)))
            else:
                variance = random.randint(-30, 30)
                day_minutes = max(0, avg_daily + variance)
                weekly.append(round(day_minutes / 60))
                remaining -= day_minutes
        return weekly

    @staticmethod
    def _generate_suggestions(
        *,
        weak_topics: list[str],
        weak_points_detail: list[dict[str, Any]],
        knowledge_level: str,
        learning_style: str,
        total_mistakes: int,
        resource_count: int,
        learning_goal: str,
        correct_rate: int,
    ) -> list[str]:
        suggestions = []

        if weak_points_detail:
            weakest = weak_points_detail[0]
            weakest_topic = weakest.get("topic", "")
            weakest_rate = weakest.get("master_rate", 0)
            weakest_unmastered = weakest.get("unmastered_count", 0)

            if weakest_rate < 40:
                suggestions.append(
                    f"【首要攻克】「{weakest_topic}」是当前最薄弱的知识点（掌握率仅 {weakest_rate}%），"
                    f"建议集中 2-3 天系统复习基础概念，每天花 40-60 分钟专项突破。"
                )
            elif weakest_rate < 60:
                suggestions.append(
                    f"【重点巩固】「{weakest_topic}」掌握率 {weakest_rate}%，还有 {weakest_unmastered} 道题待攻克，"
                    f"建议整理错题分类，针对性地做专项练习。"
                )
            else:
                suggestions.append(
                    f"【巩固保持】「{weakest_topic}」掌握尚可（{weakest_rate}%），"
                    f"建议定期复习，多做综合练习加深理解。"
                )

            if len(weak_points_detail) >= 2:
                second_weakest = weak_points_detail[1]
                second_topic = second_weakest.get("topic", "")
                second_rate = second_weakest.get("master_rate", 0)
                suggestions.append(
                    f"【次重点】「{second_topic}」掌握率 {second_rate}%，"
                    f"建议在主攻第一薄弱点的同时，每天抽 15-20 分钟复习该知识点，避免持续掉队。"
                )

        if total_mistakes > 0:
            suggestions.append(
                "【错题复盘】建立错题本复习机制，每周日花 30 分钟回顾本周错题，"
                "重点分析错误原因（概念不清/审题失误/计算错误），同类错误不犯第二次。"
            )

        has_repeat_pattern = any(
            "反复出错" in str(d.get("analysis_summary", "")) or d.get("total_mistake_count", 0) > d.get("total_count", 0) * 1.3
            for d in weak_points_detail
        )
        if has_repeat_pattern:
            suggestions.append(
                "【间隔复习】存在反复出错的情况，建议使用艾宾浩斯遗忘曲线复习法："
                "新学知识点后第 1、2、4、7 天各复习一次，确保真正掌握。"
            )

        has_basic_pattern = any(
            "基础题" in str(d.get("analysis_summary", "")) or d.get("avg_level") == "简单"
            for d in weak_points_detail
        )
        if has_basic_pattern and correct_rate < 60:
            suggestions.append(
                "【夯实基础】基础题也存在失分，说明核心概念理解不透彻。"
                "建议回归课本，把每个基础概念用自己的话复述出来，确保真正理解。"
            )

        if learning_style and "视觉" in learning_style:
            suggestions.append(
                "【学习方法】结合你的视觉型学习风格，建议用思维导图整理知识框架，"
                "用颜色标注不同重要程度的知识点，记忆效果会更好。"
            )
        elif learning_style and "练习" in learning_style:
            suggestions.append(
                "【学习方法】你偏好通过练习来学习，建议采用「学练结合」方式："
                "学完一个知识点立即做 3-5 道练习题巩固，效果最佳。"
            )
        elif learning_style and "视频" in learning_style:
            suggestions.append(
                "【学习方法】你偏好视频学习，建议选择系统的教学视频课程，"
                "边看边做笔记，看完后及时做练习题检验吸收效果。"
            )

        if learning_goal and learning_goal != "未设定" and learning_goal != "待设定":
            suggestions.append(
                f"【目标导向】你的学习目标是「{learning_goal}」，"
                f"建议将大目标拆解为每周小目标，每完成一个给自己一个小奖励，保持学习动力。"
            )

        if resource_count == 0:
            suggestions.append(
                "【资源建设】当前课程资料较少，建议上传课程讲义或使用 AI 生成学习资料，"
                "构建系统化的知识体系，便于随时复习查阅。"
            )

        if len(suggestions) < 3:
            suggestions.append(
                "【规律学习】保持每天固定时间段学习，形成习惯后效率会显著提升。"
                "建议每天至少 30 分钟，比周末突击效果好得多。"
            )
            suggestions.append(
                "【主动检测】学完后主动做自测题或给别人讲解，"
                "比被动看书的记忆留存率高 3 倍以上。"
            )

        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:4]

    @staticmethod
    def _calculate_streak_days(user_id: str) -> int:
        from pathlib import Path
        profile_dir = Path(get_settings().profile_data_dir) / user_id.replace("/", "_").replace("\\", "_")
        if not profile_dir.exists():
            return 0

        dates = set()
        for f in profile_dir.rglob("*.json"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).date()
                dates.add(mtime)
            except Exception:
                continue

        if not dates:
            return 0

        today = datetime.now(timezone.utc).date()
        streak = 0
        current = today
        sorted_dates = sorted(dates, reverse=True)
        for d in sorted_dates:
            if d == current:
                streak += 1
                from datetime import timedelta
                current = current - timedelta(days=1)
            elif d < current:
                break
        return streak
