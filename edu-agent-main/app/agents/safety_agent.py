from __future__ import annotations

from typing import Any, List, Dict

from app.core.llm_client import LLMClient


class SafetyCheckAgent:
    def __init__(self):
        self.llm = LLMClient()
        # 数据库领域专业术语列表
        self.database_terms = {
            # 基础概念
            "数据库", "关系模型", "表", "元组", "属性", "主键", "外键",
            "索引", "视图", "范式", "SQL", "DDL", "DML", "DQL", "DCL",
            # 范式相关
            "第一范式", "1NF", "第二范式", "2NF", "第三范式", "3NF", 
            "BCNF", "第四范式", "4NF", "第五范式", "5NF",
            # 数据模型
            "E-R模型", "概念模型", "逻辑模型", "物理模型",
            # 事务
            "事务", "ACID", "原子性", "一致性", "隔离性", "持久性",
            # 并发控制
            "锁", "死锁", "并发", "串行化", "隔离级别",
            # 查询优化
            "查询计划", "索引优化", "连接算法", "代价估算",
            # 存储管理
            "缓冲区管理", "磁盘存储", "数据字典", "事务日志",
            # 常见数据库
            "MySQL", "PostgreSQL", "SQLite", "Oracle", "SQL Server"
        }
        
        # 违规内容关键词
        self.forbidden_keywords = [
            # 恶意内容
            "攻击", "黑客", "入侵", "破解", "漏洞", "病毒", "木马",
            # 敏感内容
            "色情", "暴力", "赌博", "毒品", "政治",
            # 不当教学
            "作弊", "抄袭", "代写", "代考", "答案",
            # 无关内容
            "广告", "推销", "招聘", "兼职", "网课"
        ]
        
        # 常见数据库错误知识
        self.common_mistakes = [
            ("第一范式允许重复组", "第一范式要求每个属性都是原子的，不允许重复组"),
            ("第二范式不要求完全函数依赖", "第二范式要求非主属性完全函数依赖于主键"),
            ("第三范式允许传递依赖", "第三范式要求消除非主属性对主键的传递依赖"),
            ("外键必须与主键同名", "外键列名可以与主键不同，只要类型匹配"),
            ("SQL不区分大小写", "SQL关键字不区分大小写，但标识符取决于数据库配置"),
            ("索引越多越好", "过多索引会降低写操作性能"),
            ("NULL等于空字符串", "NULL和空字符串是不同的概念"),
            ("事务不需要提交", "事务需要显式COMMIT才能持久化"),
            ("锁只会阻塞写操作", "某些锁也会阻塞读操作"),
            ("视图可以提高查询性能", "视图只是查询的封装，本身不提高性能")
        ]

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """执行三层安全检查"""
        report = {
            "status": "pass",
            "risk_level": "low",
            "checks": [],
            "suggestions": []
        }
        
        # 获取需要检查的内容
        contents = self._collect_contents(state)
        
        # 执行三层检查
        for content_name, content in contents.items():
            if not content:
                continue
                
            # 第一层：知识库范围检查
            kb_result = self._check_knowledge_base_scope(content, content_name)
            report["checks"].append(kb_result)
            
            # 第二层：专业事实校验
            fact_result = self._check_factual_accuracy(content, content_name)
            report["checks"].append(fact_result)
            
            # 第三层：内容安全过滤
            safety_result = self._check_content_safety(content, content_name)
            report["checks"].append(safety_result)
        
        # 汇总结果
        report = self._summarize_report(report)
        
        return {"safety_report": report}

    def _collect_contents(self, state: dict[str, Any]) -> Dict[str, str]:
        """收集需要检查的所有内容"""
        contents = {}
        if "document" in state and state["document"]:
            contents["document"] = state["document"]
        if "mindmap" in state and state["mindmap"]:
            contents["mindmap"] = state["mindmap"]
        if "quiz" in state and state["quiz"]:
            contents["quiz"] = str(state["quiz"])
        if "practice_case" in state and state["practice_case"]:
            contents["practice_case"] = state["practice_case"]
        return contents

    def _check_knowledge_base_scope(self, content: str, content_name: str) -> Dict[str, Any]:
        """第一层检查：判断内容是否脱离database_system课程知识库范围"""
        result = {
            "check_type": "knowledge_base_scope",
            "content_name": content_name,
            "status": "pass",
            "risks": [],
            "confidence": 0.0
        }
        
        # 统计数据库术语覆盖率
        content_lower = content.lower()
        term_count = sum(1 for term in self.database_terms if term.lower() in content_lower)
        term_density = term_count / len(self.database_terms)
        
        if term_density < 0.1:
            result["status"] = "warning"
            result["risk_level"] = "medium"
            result["risks"].append({
                "risk": "内容与数据库课程相关性较低",
                "reason": f"数据库专业术语覆盖率仅为 {term_density:.1%}，内容可能偏离课程范围",
                "suggestion": "建议增加数据库相关概念和术语的讲解"
            })
            result["confidence"] = 0.8
        elif term_density < 0.2:
            result["status"] = "warning"
            result["risk_level"] = "low"
            result["risks"].append({
                "risk": "内容数据库术语较少",
                "reason": f"数据库专业术语覆盖率为 {term_density:.1%}",
                "suggestion": "可以适当增加数据库专业术语的使用"
            })
            result["confidence"] = 0.6
        else:
            result["confidence"] = 0.95
            
        return result

    def _check_factual_accuracy(self, content: str, content_name: str) -> Dict[str, Any]:
        """第二层检查：识别专业事实错误"""
        result = {
            "check_type": "factual_accuracy",
            "content_name": content_name,
            "status": "pass",
            "risks": [],
            "confidence": 0.0
        }
        
        content_lower = content.lower()
        found_mistakes = []
        
        for wrong_statement, correction in self.common_mistakes:
            if wrong_statement.lower() in content_lower:
                found_mistakes.append({
                    "wrong_statement": wrong_statement,
                    "correction": correction
                })
        
        if found_mistakes:
            result["status"] = "fail"
            result["risk_level"] = "high"
            for mistake in found_mistakes:
                result["risks"].append({
                    "risk": "专业事实错误",
                    "reason": f"检测到错误陈述：\"{mistake['wrong_statement']}\"",
                    "correction": mistake["correction"],
                    "suggestion": "请修正上述数据库概念错误"
                })
            result["confidence"] = 0.95
        else:
            # 使用LLM进行深度事实检查
            llm_check = self._llm_fact_check(content)
            if llm_check.get("has_errors"):
                result["status"] = "warning"
                result["risk_level"] = "medium"
                result["risks"].append({
                    "risk": "潜在事实错误",
                    "reason": llm_check.get("reason", "LLM检测到潜在的事实问题"),
                    "suggestion": "请仔细检查内容中的数据库概念是否准确"
                })
                result["confidence"] = llm_check.get("confidence", 0.7)
            else:
                result["confidence"] = 0.8
                
        return result

    def _llm_fact_check(self, content: str) -> Dict[str, Any]:
        """使用LLM进行事实检查"""
        try:
            prompt = f"""请检查以下数据库课程相关内容是否存在事实错误：

内容：
{content[:2000]}

请分析是否存在数据库概念错误、术语使用错误、原理描述错误等问题。

回答格式：
错误数量：N
错误详情：
1. [错误描述] - [正确表述]
...

如果没有错误，请回答：无错误
"""
            response = self.llm.generate(prompt, task="analysis")
            
            if "无错误" in response:
                return {"has_errors": False, "confidence": 0.8}
            elif "错误数量：0" in response:
                return {"has_errors": False, "confidence": 0.8}
            else:
                return {
                    "has_errors": True,
                    "reason": response[:500],
                    "confidence": 0.7
                }
        except Exception:
            return {"has_errors": False, "confidence": 0.3}

    def _check_content_safety(self, content: str, content_name: str) -> Dict[str, Any]:
        """第三层检查：过滤违规内容"""
        result = {
            "check_type": "content_safety",
            "content_name": content_name,
            "status": "pass",
            "risks": [],
            "confidence": 0.0
        }
        
        content_lower = content.lower()
        found_forbidden = []
        
        for keyword in self.forbidden_keywords:
            if keyword in content_lower:
                found_forbidden.append(keyword)
        
        if found_forbidden:
            result["status"] = "fail"
            result["risk_level"] = "high"
            result["risks"].append({
                "risk": "包含违规内容",
                "reason": f"检测到以下违规关键词：{', '.join(found_forbidden)}",
                "suggestion": "请删除或替换这些违规内容，确保输出适合课堂教学"
            })
            result["confidence"] = 0.99
        else:
            result["confidence"] = 0.95
            
        return result

    def _summarize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """汇总检查结果"""
        # 统计各状态数量
        pass_count = sum(1 for c in report["checks"] if c["status"] == "pass")
        warning_count = sum(1 for c in report["checks"] if c["status"] == "warning")
        fail_count = sum(1 for c in report["checks"] if c["status"] == "fail")
        
        # 确定整体状态
        if fail_count > 0:
            report["status"] = "fail"
            report["risk_level"] = "high"
        elif warning_count > 0:
            report["status"] = "warning"
            report["risk_level"] = "medium"
        else:
            report["status"] = "pass"
            report["risk_level"] = "low"
        
        # 生成建议
        suggestions = []
        for check in report["checks"]:
            for risk in check.get("risks", []):
                if "suggestion" in risk:
                    suggestions.append(risk["suggestion"])
        
        report["suggestions"] = list(set(suggestions))  # 去重
        report["summary"] = {
            "total_checks": len(report["checks"]),
            "passed": pass_count,
            "warnings": warning_count,
            "failed": fail_count
        }
        
        return report
