# 第二章：SQL语言基础

## 2.1 SQL概述

SQL（Structured Query Language）是用于管理关系数据库的标准语言，包括以下主要功能：
- **数据定义语言（DDL）**：CREATE, ALTER, DROP
- **数据操纵语言（DML）**：INSERT, UPDATE, DELETE
- **数据查询语言（DQL）**：SELECT
- **数据控制语言（DCL）**：GRANT, REVOKE

## 2.2 SELECT语句

### 基本语法

```sql
SELECT column1, column2, ...
FROM table_name
WHERE condition
ORDER BY column_name ASC|DESC;
```

### 示例

```sql
-- 查询所有学生信息
SELECT * FROM students;

-- 查询指定列
SELECT student_id, name, age FROM students;

-- 带条件查询
SELECT * FROM students WHERE age > 18;

-- 排序查询
SELECT * FROM students ORDER BY age DESC;
```

## 2.3 WHERE子句

### 比较运算符

| 运算符 | 说明 |
|--------|------|
| = | 等于 |
| <> | 不等于 |
| > | 大于 |
| < | 小于 |
| >= | 大于等于 |
| <= | 小于等于 |

### 逻辑运算符

```sql
-- AND 与
SELECT * FROM students WHERE age > 18 AND gender = '男';

-- OR 或
SELECT * FROM students WHERE major = '计算机' OR major = '软件工程';

-- NOT 非
SELECT * FROM students WHERE NOT age < 18;
```

### 模糊查询

```sql
-- LIKE 模糊匹配
SELECT * FROM students WHERE name LIKE '张%';  -- 姓张的学生
SELECT * FROM students WHERE name LIKE '%伟';  -- 名字以伟结尾
SELECT * FROM students WHERE name LIKE '_三';  -- 名字两个字，第二个字是三
```

## 2.4 聚合函数

```sql
-- COUNT 计数
SELECT COUNT(*) FROM students;

-- SUM 求和
SELECT SUM(score) FROM exam_results;

-- AVG 平均值
SELECT AVG(age) FROM students;

-- MAX 最大值
SELECT MAX(score) FROM exam_results;

-- MIN 最小值
SELECT MIN(score) FROM exam_results;
```

## 2.5 GROUP BY子句

```sql
-- 按专业分组统计人数
SELECT major, COUNT(*) as count
FROM students
GROUP BY major;

-- 按性别分组计算平均年龄
SELECT gender, AVG(age) as avg_age
FROM students
GROUP BY gender;
```

## 2.6 JOIN操作

### INNER JOIN

```sql
-- 查询学生及其所在班级
SELECT s.name, c.class_name
FROM students s
INNER JOIN classes c ON s.class_id = c.class_id;
```

### LEFT JOIN

```sql
-- 查询所有学生，包括没有班级的学生
SELECT s.name, c.class_name
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id;
```

### RIGHT JOIN

```sql
-- 查询所有班级，包括没有学生的班级
SELECT s.name, c.class_name
FROM students s
RIGHT JOIN classes c ON s.class_id = c.class_id;
```

## 2.7 INSERT语句

```sql
-- 插入单行
INSERT INTO students (student_id, name, age, gender)
VALUES ('2024001', '张三', 20, '男');

-- 插入多行
INSERT INTO students (student_id, name, age, gender)
VALUES 
    ('2024002', '李四', 19, '男'),
    ('2024003', '王五', 21, '女');
```

## 2.8 UPDATE语句

```sql
-- 更新单个记录
UPDATE students
SET age = 21
WHERE student_id = '2024001';

-- 更新多个字段
UPDATE students
SET age = 22, major = '计算机科学'
WHERE student_id = '2024002';
```

## 2.9 DELETE语句

```sql
-- 删除指定记录
DELETE FROM students
WHERE student_id = '2024001';

-- 删除所有记录（谨慎使用）
DELETE FROM students;
```

## 2.10 创建表

```sql
CREATE TABLE students (
    student_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT,
    gender VARCHAR(10),
    major VARCHAR(100),
    class_id INT,
    FOREIGN KEY (class_id) REFERENCES classes(class_id)
);
```

## 2.11 学习目标

通过本章学习，你将能够：
- 使用SELECT语句查询数据
- 使用WHERE子句过滤数据
- 使用聚合函数进行统计
- 使用GROUP BY分组数据
- 使用JOIN连接多个表
- 执行INSERT、UPDATE、DELETE操作
- 创建和修改表结构