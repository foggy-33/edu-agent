from __future__ import annotations

from typing import Any


class QuizAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        quiz = [
            {
                "question": "在关系模式 R(A,B,C) 中，若 A->B 且 B->C，则 A+ 包含哪些属性？",
                "type": "选择题",
                "answer": "A、B、C",
                "explanation": "由自反律得到 A，A->B 得到 B，再由 B->C 得到 C。",
            },
            {
                "question": "候选码一定是超码，但超码不一定是候选码。",
                "type": "判断题",
                "answer": "正确",
                "explanation": "候选码是最小超码，不能再删除属性。",
            },
            {
                "question": "若非主属性完全依赖于任一候选码，则关系至少满足____。",
                "type": "填空题",
                "answer": "第二范式/2NF",
                "explanation": "2NF 消除非主属性对候选码的部分函数依赖。",
            },
            {
                "question": "简述用属性闭包判断候选码的基本步骤。",
                "type": "简答题",
                "answer": "选取属性集，反复应用函数依赖扩展闭包；若闭包包含全部属性且无真子集也能决定全部属性，则为候选码。",
                "explanation": "关键是同时验证可决定全部属性和最小性。",
            },
            {
                "question": "给定 R(Sno,Cno,Grade,Sdept)，Sno->Sdept，(Sno,Cno)->Grade，分析是否存在部分依赖。",
                "type": "应用题",
                "answer": "存在。候选码可为 (Sno,Cno)，Sdept 依赖于候选码的一部分 Sno。",
                "explanation": "非主属性 Sdept 对复合候选码存在部分依赖，因此不满足 2NF。",
            },
        ]
        return {"quiz": quiz}
