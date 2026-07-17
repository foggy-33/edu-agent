# API Examples

## Health
```bash
curl http://localhost:8000/health
```

## Analyze
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user_001",
    "course": "数据库系统",
    "message": "我是计算机专业大二学生，正在学习数据库系统。我对函数依赖、候选码和范式判断不太会，希望通过例题和步骤化讲解准备考试。"
  }'
```

## Generate
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user_001",
    "course": "数据库系统",
    "message": "我是计算机专业大二学生，正在学习数据库系统。我对函数依赖、候选码和范式判断不太会，希望通过例题和步骤化讲解准备考试。"
  }'
```

## Evaluate
```bash
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user_001",
    "course": "数据库系统",
    "answers": [
      {
        "question": "求 A+",
        "student_answer": "{A,B}",
        "correct_answer": "{A,B,C}",
        "is_correct": false,
        "topic": "函数依赖"
      }
    ]
  }'
```
