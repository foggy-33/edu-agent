from __future__ import annotations

from typing import Any


class PracticeAgent:
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        practice_case = """# SQL 实操案例：学生选课与范式理解

## 建表 SQL
```sql
CREATE TABLE student (
  student_id INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  department VARCHAR(50) NOT NULL
);

CREATE TABLE course (
  course_id INT PRIMARY KEY,
  course_name VARCHAR(100) NOT NULL,
  credit INT NOT NULL
);

CREATE TABLE enrollment (
  student_id INT,
  course_id INT,
  grade DECIMAL(5,2),
  PRIMARY KEY (student_id, course_id),
  FOREIGN KEY (student_id) REFERENCES student(student_id),
  FOREIGN KEY (course_id) REFERENCES course(course_id)
);
```

## 插入数据 SQL
```sql
INSERT INTO student VALUES (1, '张三', '计算机学院'), (2, '李四', '软件学院');
INSERT INTO course VALUES (101, '数据库系统', 4), (102, '操作系统', 4);
INSERT INTO enrollment VALUES (1, 101, 86), (1, 102, 79), (2, 101, 91);
```

## 练习任务
1. 查询选修“数据库系统”的学生姓名和成绩。
2. 查询每门课程的平均分。
3. 说明 enrollment 表为什么适合使用复合主键。

## 参考答案
```sql
SELECT s.name, e.grade
FROM student s
JOIN enrollment e ON s.student_id = e.student_id
JOIN course c ON e.course_id = c.course_id
WHERE c.course_name = '数据库系统';

SELECT c.course_name, AVG(e.grade) AS avg_grade
FROM course c
JOIN enrollment e ON c.course_id = e.course_id
GROUP BY c.course_name;
```

enrollment 表的一条记录由学生和课程共同确定，单独 student_id 或 course_id 都不能唯一标识成绩。
"""
        return {"practice_case": practice_case}
