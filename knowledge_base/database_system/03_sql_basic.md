# SQL 基础

## 知识点概述
SQL 是关系数据库的标准语言，包含数据定义、数据查询、数据操纵和数据控制。

## 核心概念
- DDL：CREATE、ALTER、DROP。
- DML：INSERT、UPDATE、DELETE。
- DQL：SELECT。
- JOIN：连接多个关系表。

## 常见易错点
- WHERE 在分组前过滤行，HAVING 在分组后过滤组。
- 内连接只保留匹配行，外连接会保留未匹配行。

## 示例
```sql
SELECT department, COUNT(*) AS total
FROM student
GROUP BY department
HAVING COUNT(*) > 10;
```

## 练习题
写出查询每个学院学生人数的 SQL。
