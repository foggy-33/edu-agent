# 数据库系统复习笔记

## 一、核心概念总结

### 1.1 数据库基础

| 概念 | 定义 | 要点 |
|------|------|------|
| 数据库 | 长期存储的、有组织的数据集合 | 结构化、可共享 |
| DBMS | 管理数据库的软件系统 | DDL、DML、DQL、DCL |
| 数据模型 | 数据的组织方式 | 层次、网状、关系、NoSQL |
| 关系模型 | 以表形式组织数据 | 行、列、主键、外键 |

### 1.2 数据库设计

**规范化原则：**
- **1NF**：列不可再分
- **2NF**：非主键完全依赖主键
- **3NF**：消除传递依赖
- **BCNF**：消除主属性对候选键的部分依赖

**反规范化场景：**
- 查询性能要求高
- 数据量较大
- 读操作远多于写操作

### 1.3 SQL语言分类

| 分类 | 功能 | 关键字 |
|------|------|--------|
| DDL | 数据定义 | CREATE, ALTER, DROP |
| DML | 数据操纵 | INSERT, UPDATE, DELETE |
| DQL | 数据查询 | SELECT |
| DCL | 数据控制 | GRANT, REVOKE |
| TCL | 事务控制 | COMMIT, ROLLBACK, SAVEPOINT |

## 二、SQL查询要点

### 2.1 SELECT语句结构

```sql
SELECT [DISTINCT] column1, column2, ...
FROM table1
[JOIN table2 ON condition]
[WHERE condition]
[GROUP BY column]
[HAVING condition]
[ORDER BY column ASC|DESC]
[LIMIT offset, count];
```

### 2.2 常用函数

**聚合函数：**
- COUNT() - 计数
- SUM() - 求和
- AVG() - 平均值
- MAX() - 最大值
- MIN() - 最小值

**字符串函数：**
- CONCAT() - 拼接
- SUBSTRING() - 截取
- LENGTH() - 长度
- UPPER()/LOWER() - 大小写转换

**日期函数：**
- NOW() - 当前时间
- DATE() - 提取日期
- YEAR()/MONTH()/DAY() - 提取年/月/日
- DATEDIFF() - 日期差

### 2.3 JOIN类型对比

| JOIN类型 | 结果 | 关键字 |
|----------|------|--------|
| INNER JOIN | 只返回匹配的行 | JOIN / INNER JOIN |
| LEFT JOIN | 返回左表所有行，右表匹配的行 | LEFT JOIN / LEFT OUTER JOIN |
| RIGHT JOIN | 返回右表所有行，左表匹配的行 | RIGHT JOIN / RIGHT OUTER JOIN |
| FULL JOIN | 返回两表所有行 | FULL JOIN / FULL OUTER JOIN |
| CROSS JOIN | 笛卡尔积 | CROSS JOIN |

## 三、事务管理

### 3.1 ACID特性

- **原子性（Atomicity）**：事务是不可分割的工作单位
- **一致性（Consistency）**：事务执行前后数据完整性不变
- **隔离性（Isolation）**：事务之间相互独立
- **持久性（Durability）**：事务提交后数据永久保存

### 3.2 隔离级别

| 级别 | 说明 | 并发问题 |
|------|------|----------|
| READ UNCOMMITTED | 可读取未提交数据 | 脏读、不可重复读、幻读 |
| READ COMMITTED | 只能读取已提交数据 | 不可重复读、幻读 |
| REPEATABLE READ | 同一事务内多次读取结果一致 | 幻读 |
| SERIALIZABLE | 完全串行化执行 | 无 |

### 3.3 并发控制

**锁机制：**
- 共享锁（S锁）：读锁，多个事务可同时持有
- 排他锁（X锁）：写锁，独占

**死锁预防：**
- 按固定顺序获取锁
- 设置锁超时时间
- 使用死锁检测机制

## 四、索引优化

### 4.1 索引类型

| 类型 | 特点 | 适用场景 |
|------|------|----------|
| B-Tree索引 | 平衡树结构 | 范围查询、排序 |
| Hash索引 | 哈希表结构 | 等值查询 |
| 全文索引 | 全文检索 | 文本搜索 |
| 位图索引 | 位图结构 | 低基数列 |

### 4.2 索引使用原则

**创建索引：**
- 主键自动创建索引
- 外键建议创建索引
- 经常用于查询条件的列
- 经常用于排序和分组的列

**避免索引：**
- 频繁更新的列
- 数据量小的表
- 低选择性的列（如性别）

### 4.3 执行计划分析

使用 `EXPLAIN` 分析查询：
```sql
EXPLAIN SELECT * FROM students WHERE age > 18;
```

**关键输出字段：**
- type：访问类型（ALL, index, range, ref, eq_ref, const）
- key：使用的索引
- rows：扫描的行数
- Extra：额外信息（Using index, Using where, Using filesort）

## 五、数据库安全

### 5.1 用户管理

```sql
-- 创建用户
CREATE USER 'user'@'localhost' IDENTIFIED BY 'password';

-- 授权
GRANT SELECT, INSERT ON database.* TO 'user'@'localhost';

-- 撤销权限
REVOKE INSERT ON database.* FROM 'user'@'localhost';

-- 删除用户
DROP USER 'user'@'localhost';
```

### 5.2 安全最佳实践

1. 最小权限原则
2. 使用强密码
3. 定期备份数据
4. 加密敏感数据
5. 审计日志记录

## 六、复习自测题

### 选择题

1. 以下哪个不是ACID特性？
   A. 原子性 B. 一致性 C. 独立性 D. 持久性

2. 第三范式要求消除：
   A. 部分依赖 B. 传递依赖 C. 完全依赖 D. 函数依赖

3. 以下哪个JOIN返回左表所有行？
   A. INNER JOIN B. LEFT JOIN C. RIGHT JOIN D. CROSS JOIN

### 简答题

1. 简述数据库规范化的目的和常见范式。
2. 说明索引的作用和创建原则。
3. 解释事务的隔离级别。

### SQL练习

1. 写出查询每个专业学生人数的SQL语句。
2. 写出查询学生及其考试成绩的SQL语句。
3. 写出更新学生年龄的SQL语句。

## 七、学习资源推荐

### 书籍
- 《数据库系统概念》 - Abraham Silberschatz
- 《SQL必知必会》 - Ben Forta
- 《高性能MySQL》 - 施瓦茨

### 在线资源
- W3Schools SQL教程
- MySQL官方文档
- PostgreSQL官方文档

### 实践平台
- LeetCode 数据库题目
- HackerRank SQL挑战
- SQLZoo 交互式练习

## 八、总结

数据库系统是计算机科学的核心课程，重点掌握：
1. 关系模型和规范化理论
2. SQL语言的完整语法
3. 事务管理和并发控制
4. 索引优化和查询调优
5. 数据库安全和最佳实践

通过理论学习和实践练习，建立扎实的数据库基础知识，为后续学习高级数据库技术打下良好基础。