#!/usr/bin/env python3
"""
安全检查Agent测试脚本
验证三层校验逻辑：知识库范围检查、事实准确性校验、内容安全过滤
"""
import sys
import os

# 设置项目路径
PROJECT_ROOT = r"C:\Users\wyh\Downloads\edu-agent-main (1)\edu-agent-main"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from app.agents.safety_agent import SafetyCheckAgent


def print_report(report):
    """打印安全检查报告"""
    print(f"\n{'='*60}")
    print(f"安全检查报告")
    print(f"{'='*60}")
    print(f"整体状态: {report['status']}")
    print(f"风险等级: {report['risk_level']}")
    print(f"检查总数: {report['summary']['total_checks']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"警告: {report['summary']['warnings']}")
    print(f"失败: {report['summary']['failed']}")
    
    print(f"\n{'检查详情':-^60}")
    for check in report["checks"]:
        print(f"\n[{check['check_type']}] {check['content_name']}")
        print(f"  状态: {check['status']}")
        print(f"  置信度: {check['confidence']:.2f}")
        if check["risks"]:
            for risk in check["risks"]:
                print(f"  风险: {risk['risk']}")
                print(f"    原因: {risk['reason']}")
                if "correction" in risk:
                    print(f"    正确表述: {risk['correction']}")
                print(f"    建议: {risk['suggestion']}")
    
    if report["suggestions"]:
        print(f"\n{'改进建议':-^60}")
        for i, suggestion in enumerate(report["suggestions"], 1):
            print(f"{i}. {suggestion}")


def test_case_1_normal_content():
    """测试用例1：正常的数据库课程内容"""
    print("\n" + "="*70)
    print("测试用例1：正常的数据库课程内容")
    print("="*70)
    
    agent = SafetyCheckAgent()
    
    state = {
        "document": """# 关系数据库范式

## 第一范式(1NF)
第一范式要求关系中的每个属性都是原子的，即不可再分。这意味着每个字段只能包含一个值，不能有重复组或嵌套结构。

## 第二范式(2NF)
第二范式要求在第一范式的基础上，非主属性必须完全函数依赖于主键。消除部分函数依赖。

## SQL基础操作
- DDL: CREATE, ALTER, DROP
- DML: INSERT, UPDATE, DELETE
- DQL: SELECT
""",
        "mindmap": """mindmap
  root((数据库系统))
    基础概念
      关系模型
      SQL语言
    范式理论
      1NF
      2NF
      3NF
"""
    }
    
    result = agent.run(state)
    print_report(result["safety_report"])


def test_case_2_factual_error():
    """测试用例2：包含事实错误的内容"""
    print("\n" + "="*70)
    print("测试用例2：包含事实错误的内容")
    print("="*70)
    
    agent = SafetyCheckAgent()
    
    state = {
        "document": """# 数据库知识讲解

需要注意的是，第一范式允许重复组，这是数据库设计的基础。
索引越多越好，可以提高所有查询的性能。
SQL不区分大小写，所有标识符都不区分。
NULL等于空字符串，两者可以互换使用。
"""
    }
    
    result = agent.run(state)
    print_report(result["safety_report"])


def test_case_3_forbidden_content():
    """测试用例3：包含违规内容"""
    print("\n" + "="*70)
    print("测试用例3：包含违规内容")
    print("="*70)
    
    agent = SafetyCheckAgent()
    
    state = {
        "document": """# 数据库学习指南

如果你想快速通过考试，可以考虑找黑客帮忙或者使用作弊软件。
我们提供代写服务，可以帮你完成所有作业。
另外，这里有一些赌博网站推荐，可以放松一下。
政治话题不在讨论范围内，但我可以告诉你一些内幕消息。
"""
    }
    
    result = agent.run(state)
    print_report(result["safety_report"])


def test_case_4_out_of_scope():
    """测试用例4：内容脱离知识库范围"""
    print("\n" + "="*70)
    print("测试用例4：内容脱离知识库范围")
    print("="*70)
    
    agent = SafetyCheckAgent()
    
    state = {
        "document": """# 人工智能入门

人工智能是计算机科学的一个分支，致力于研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。

机器学习是人工智能的核心，包括监督学习、无监督学习、强化学习等方法。

深度学习是机器学习的一个子集，使用多层神经网络进行特征学习。
""",
        "practice_case": "这是一个关于Python编程的练习，与数据库无关。"
    }
    
    result = agent.run(state)
    print_report(result["safety_report"])


def test_case_5_mixed_content():
    """测试用例5：混合内容（正常+违规）"""
    print("\n" + "="*70)
    print("测试用例5：混合内容（正常+违规）")
    print("="*70)
    
    agent = SafetyCheckAgent()
    
    state = {
        "document": """# 数据库事务管理

事务是数据库管理系统执行过程中的一个逻辑单位，由一个有限的数据库操作序列构成。

事务具有ACID特性：
- 原子性(Atomicity)
- 一致性(Consistency)
- 隔离性(Isolation)
- 持久性(Durability)

如果你想快速拿到答案，可以联系我们的代写团队。
"""
    }
    
    result = agent.run(state)
    print_report(result["safety_report"])


if __name__ == "__main__":
    print("="*70)
    print("SafetyCheckAgent 安全检查功能测试")
    print("="*70)
    
    # 运行所有测试用例
    test_case_1_normal_content()
    test_case_2_factual_error()
    test_case_3_forbidden_content()
    test_case_4_out_of_scope()
    test_case_5_mixed_content()
    
    print("\n" + "="*70)
    print("所有测试用例执行完毕！")
    print("="*70)
