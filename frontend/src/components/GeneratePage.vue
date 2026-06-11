<script setup lang="ts">
import { ref, computed } from 'vue'
import { generate } from '../api/client'
import MarkdownRenderer from './MarkdownRenderer.vue'
import MermaidRenderer from './MermaidRenderer.vue'

const emit = defineEmits<{
  navigate: [page: 'resources']
}>()

const user_id = ref('demo_user_001')
const course = ref('数据库系统')
const message = ref('')
const loading = ref(false)
const resources = ref<any>(null)
const error = ref('')

const currentStage = ref(0)
const generationStages = [
  { name: '分析用户需求', icon: '🔍' },
  { name: '生成学生画像', icon: '👤' },
  { name: '规划学习路径', icon: '🗺️' },
  { name: '生成文档摘要', icon: '📄' },
  { name: '绘制思维导图', icon: '🧠' },
  { name: '创建练习题', icon: '📝' },
  { name: '设计实践案例', icon: '💡' },
  { name: '安全检查', icon: '🛡️' }
]

const resourceTabs = [
  { key: 'document', label: '📄 文档摘要' },
  { key: 'mindmap', label: '🧠 思维导图' },
  { key: 'quiz', label: '📝 练习题' },
  { key: 'practice', label: '💡 实践案例' },
]
const activeTab = ref('document')

const resourceTypes = [
  { id: 'document', name: '文档摘要', icon: '📄', enabled: true },
  { id: 'mindmap', name: '思维导图', icon: '🧠', enabled: true },
  { id: 'quiz', name: '练习题', icon: '📝', enabled: true },
  { id: 'practice', name: '实践案例', icon: '💡', enabled: true },
]
const selectedTypes = ref(resourceTypes.filter(t => t.enabled).map(t => t.id))

const progressPercent = computed(() => {
  return Math.round((currentStage.value / generationStages.length) * 100)
})

let progressTimer: ReturnType<typeof setInterval> | null = null

async function handleGenerate() {
  if (!message.value.trim()) {
    error.value = '请输入学习需求'
    return
  }

  loading.value = true
  error.value = ''
  resources.value = null
  currentStage.value = 0

  progressTimer = setInterval(() => {
    if (currentStage.value < generationStages.length - 1) {
      currentStage.value++
    }
  }, 500)

  try {
    const response = await generate({
      user_id: user_id.value,
      course: course.value,
      message: message.value
    })
    resources.value = {
      ...response,
      profile: response.profile || mockProfile,
      learning_path: response.learning_path || mockLearningPath,
      resources: response.resources || mockResources,
      safety_report: response.safety_report || { status: 'pass', notes: [] }
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '生成失败'
    resources.value = mockFullData
  } finally {
    if (progressTimer) {
      clearInterval(progressTimer)
      progressTimer = null
    }
    currentStage.value = generationStages.length
    setTimeout(() => {
      loading.value = false
    }, 300)
  }
}

function textToMermaid(text: string): string {
  if (!text) return 'graph TD\n  A[空数据]'
  if (text.trim().startsWith('graph') || text.trim().startsWith('flowchart') || text.trim().startsWith('mindmap')) {
    return text
  }

  const lines = text.split('\n').filter(l => l.trim())
  const nodes: string[] = []
  const edges: string[] = []
  let idCounter = 0
  const idMap: Record<string, string> = {}

  function getId(label: string): string {
    const cleanLabel = label.replace(/[├──|│─]/g, '').trim()
    if (idMap[cleanLabel]) return idMap[cleanLabel]
    idCounter++
    const id = `N${idCounter}`
    idMap[cleanLabel] = id
    const escaped = cleanLabel.replace(/"/g, "'")
    nodes.push(`  ${id}["${escaped}"]`)
    return id
  }

  let rootId = ''
  const stack: { id: string; level: number }[] = []

  for (const line of lines) {
    const cleanLine = line.replace(/\s+$/, '')
    if (!cleanLine.trim()) continue

    const match = cleanLine.match(/^([├│└\s─]*)(.*)$/)
    if (!match) continue

    const prefix = match[1]
    const label = match[2].trim()
    if (!label || label === '##' || label.startsWith('##')) {
      if (label.startsWith('##')) {
        const realLabel = label.replace(/^##\s*/, '').trim()
        if (realLabel) {
          const id = getId(realLabel)
          rootId = id
          stack.length = 0
          stack.push({ id, level: 0 })
        }
      }
      continue
    }

    const level = Math.floor(prefix.length / 3)
    const id = getId(label)

    if (!rootId) {
      rootId = id
      stack.push({ id, level: 0 })
    } else {
      while (stack.length > 0 && stack[stack.length - 1].level >= level) {
        stack.pop()
      }
      if (stack.length > 0) {
        const parent = stack[stack.length - 1]
        edges.push(`  ${parent.id} --> ${id}`)
      }
      stack.push({ id, level })
    }
  }

  if (nodes.length === 0) {
    return `graph TD\n  A[学习内容] --> B[暂无数据]`
  }

  return 'graph TD\n' + nodes.join('\n') + '\n' + edges.join('\n')
}

const mockProfile = {
  major: '计算机科学与技术',
  course: '数据库系统',
  grade_level: '大三',
  learning_goal: '准备期末考试',
  knowledge_level: '中等',
  learning_style: '视觉型',
  weak_points: ['函数依赖', '候选码', '范式判断'],
  resource_preference: ['视频教程', '练习题', '思维导图'],
}

const mockLearningPath = [
  { stage: 1, title: '基础概念复习', estimated_time: '2小时', goal: '复习数据库基本概念', tasks: ['回顾关系模型', '复习SQL基础', '了解数据库设计原则'], recommended_resources: ['教材第一章', 'SQL入门教程'] },
  { stage: 2, title: '函数依赖深入', estimated_time: '3小时', goal: '掌握函数依赖理论', tasks: ['学习函数依赖定义', '练习闭包计算', '理解Armstrong公理'], recommended_resources: ['函数依赖详解', '例题集'] },
  { stage: 3, title: '范式判断练习', estimated_time: '3小时', goal: '熟练掌握范式判断', tasks: ['练习1NF判断', '练习2NF判断', '练习3NF和BCNF判断'], recommended_resources: ['范式讲解视频', '习题集'] },
]

const mockResources = {
  document: `## 函数依赖与范式判断复习指南

### 一、函数依赖基础

**定义**：设R(U)是属性集U上的关系模式。X,Y是U的子集。若对于R(U)的任意一个可能的关系r，r中不可能存在两个元组在X上的属性值相等，而在Y上的属性值不等，则称X函数确定Y或Y函数依赖于X，记作X→Y。

### 二、Armstrong公理

1. **自反律**：若Y⊆X⊆U，则X→Y为F所蕴含。
2. **增广律**：若X→Y为F所蕴含，且Z⊆U，则XZ→YZ为F所蕴含。
3. **传递律**：若X→Y及Y→Z为F所蕴含，则X→Z为F所蕴含。

### 三、范式判断

- **1NF**：关系中的每个属性都是不可再分的原子值。
- **2NF**：在1NF基础上，非主属性完全依赖于主键。
- **3NF**：在2NF基础上，非主属性不传递依赖于主键。
- **BCNF**：在3NF基础上，任何非平凡函数依赖的左部都包含候选码。

### 四、示例分析

\`\`\`
R(A, B, C, D)
F = {A→B, B→C}
判断是否满足3NF？

解答：
- 主键：A
- A→B (主属性→非主属性，直接依赖)
- B→C (非主属性→非主属性，传递依赖！)

结论：不满足3NF，需要分解为：
- R1(A, B)
- R2(B, C)
\`\`\`

> 💡 **学习建议**：理解范式判断的关键是识别各种依赖关系，特别是完全依赖、部分依赖和传递依赖。
`,
  mindmap: `graph TD
    A[数据库系统] --> B[关系模型]
    B --> B1[属性]
    B --> B2[元组]
    B --> B3[关系]
    A --> C[函数依赖]
    C --> C1[定义 X→Y]
    C --> C2[Armstrong公理]
    C --> C3[闭包计算]
    A --> D[范式理论]
    D --> D1[1NF 原子值]
    D --> D2[2NF 完全依赖]
    D --> D3[3NF 无传递依赖]
    D --> D4[BCNF 更严格]
    A --> E[候选码]
    E --> E1[定义]
    E --> E2[求解方法]`,
  quiz: [
    { type: '选择题', question: '下列关于函数依赖的说法，正确的是？', answer: 'B', explanation: '函数依赖要求对于X的每个值，Y只有唯一的值与之对应。' },
    { type: '判断题', question: '若X→Y且Y→Z，则X→Z一定成立。', answer: '正确', explanation: '根据Armstrong公理的传递律，该结论成立。' },
    { type: '应用题', question: '给定关系模式R(A,B,C,D)，F={A→B,B→C}，求属性集A的闭包。', answer: '{A,B,C}', explanation: 'A+ = A ∪ B ∪ C = {A,B,C}' },
  ],
  practice_case: `## 实践案例：学生选课数据库设计

### 需求分析

设计一个学生选课系统，包含以下信息：
- **学生信息**：学号、姓名、专业、年级
- **课程信息**：课程号、课程名、学分、授课教师
- **选课信息**：学号、课程号、成绩

### 设计过程

#### 步骤1：确定关系模式

\`\`\`sql
-- 学生表
Student(Sno, Sname, Major, Grade)

-- 课程表
Course(Cno, Cname, Credit, Teacher)

-- 选课表
SC(Sno, Cno, Grade)
\`\`\`

#### 步骤2：确定函数依赖

- **Student**: Sno → Sname, Major, Grade
- **Course**: Cno → Cname, Credit, Teacher
- **SC**: (Sno, Cno) → Grade

#### 步骤3：范式判断

| 表名 | 主键 | 1NF | 2NF | 3NF | BCNF |
|------|------|-----|-----|-----|------|
| Student | Sno | ✓ | ✓ | ✓ | ✓ |
| Course | Cno | ✓ | ✓ | ✓ | ✓ |
| SC | (Sno,Cno) | ✓ | ✓ | ✓ | ✓ |

三个关系都满足**BCNF**要求。

### 思考问题

1. 如果要求每个学生只能属于一个专业，这个约束如何体现？
2. 如果一门课可以有多个教师授课，如何修改设计？
3. 如果需要记录教师的职称信息，应该如何处理？

> 💡 **最佳实践**：在实际数据库设计中，通常需要权衡范式和性能，适度反范式化可以提高查询效率。
`,
  extended_reading: [
    { title: '数据库系统概论（第5版）', url: '#' },
    { title: '函数依赖与范式详解', url: '#' },
  ]
}

const mockFullData = {
  profile: mockProfile,
  learning_path: mockLearningPath,
  resources: mockResources,
  safety_report: { status: 'pass', notes: [] }
}
</script>

<template>
  <div class="space-y-6">
    <div class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-bold text-gray-800">✨ 资源生成设置</h2>
        <button
          @click="emit('navigate', 'resources')"
          class="px-4 py-2 bg-gray-100 text-gray-600 rounded-xl hover:bg-gray-200 transition-all flex items-center gap-2"
        >
          ← 返回资源库
        </button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">用户ID</label>
          <input
            v-model="user_id"
            type="text"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
            placeholder="输入用户ID"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">课程</label>
          <select
            v-model="course"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
          >
            <option value="数据库系统">数据库系统</option>
            <option value="数据结构">数据结构</option>
            <option value="算法设计">算法设计</option>
          </select>
        </div>
        <div class="lg:col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-2">学习需求</label>
          <textarea
            v-model="message"
            rows="2"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all resize-none"
            placeholder="描述您的学习需求，例如：我对函数依赖、候选码和范式判断不太会，希望通过例题准备考试..."
          ></textarea>
        </div>
      </div>

      <div class="mt-6">
        <label class="block text-sm font-medium text-gray-700 mb-3">生成资源类型</label>
        <div class="flex flex-wrap gap-3">
          <button
            v-for="type in resourceTypes"
            :key="type.id"
            @click="selectedTypes = selectedTypes.includes(type.id) 
              ? selectedTypes.filter(t => t !== type.id) 
              : [...selectedTypes, type.id]"
            :class="[
              'px-4 py-2 rounded-xl font-medium transition-all',
              selectedTypes.includes(type.id)
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            <span class="mr-2">{{ type.icon }}</span>
            {{ type.name }}
          </button>
        </div>
      </div>

      <button
        @click="handleGenerate"
        :disabled="loading"
        class="mt-6 w-full py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium rounded-xl hover:from-green-600 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <span v-if="loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        {{ loading ? '生成中...' : '🎯 生成学习资源' }}
      </button>

      <div v-if="error" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        ❌ {{ error }}
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-bold text-gray-800">⏳ 资源生成中...</h3>
        <span class="text-2xl font-bold text-green-600">{{ progressPercent }}%</span>
      </div>

      <div class="h-3 bg-gray-100 rounded-full overflow-hidden mb-6">
        <div
          class="h-full bg-gradient-to-r from-green-500 to-emerald-600 rounded-full transition-all duration-300"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div
          v-for="(stage, index) in generationStages"
          :key="stage.name"
          :class="[
            'p-4 rounded-xl border-2 transition-all',
            index < currentStage
              ? 'bg-green-50 border-green-200'
              : index === currentStage
              ? 'bg-white border-green-500 shadow-lg shadow-green-500/20'
              : 'bg-gray-50 border-gray-200 opacity-50'
          ]"
        >
          <div class="text-2xl mb-2">{{ stage.icon }}</div>
          <div :class="[
            'text-sm font-medium',
            index < currentStage ? 'text-green-700' :
            index === currentStage ? 'text-gray-800' : 'text-gray-400'
          ]">{{ stage.name }}</div>
          <div class="mt-2">
            <span v-if="index < currentStage" class="text-green-500 text-sm">✓ 完成</span>
            <span v-else-if="index === currentStage" class="flex items-center gap-1 text-green-600 text-sm">
              <span class="w-3 h-3 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></span>
              进行中
            </span>
            <span v-else class="text-gray-400 text-sm">等待中</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="resources && !loading" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">生成资源数</div>
          <div class="text-3xl font-bold mt-2">{{ Object.keys(resources.resources).length }}项</div>
        </div>
        <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">练习题数</div>
          <div class="text-3xl font-bold mt-2">{{ resources.resources.quiz?.length || 0 }}道</div>
        </div>
        <div class="bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl p-6 text-white shadow-lg">
          <div class="text-white/80 text-sm">安全状态</div>
          <div class="text-3xl font-bold mt-2">{{ resources.safety_report.status === 'pass' ? '✓ 通过' : '⚠ 警告' }}</div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div class="flex flex-wrap border-b border-gray-200">
          <button
            v-for="tab in resourceTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'px-6 py-4 font-medium transition-colors flex items-center gap-2',
              activeTab === tab.key ? 'text-green-600 border-b-2 border-green-600 bg-green-50' : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="p-6">
          <div v-if="activeTab === 'document'" class="prose max-w-none">
            <MarkdownRenderer :content="resources.resources.document" />
          </div>

          <div v-if="activeTab === 'mindmap'" class="prose max-w-none">
            <MermaidRenderer :chart="textToMermaid(resources.resources.mindmap)" />
          </div>

          <div v-if="activeTab === 'quiz'" class="space-y-4">
            <div
              v-for="(quiz, index) in resources.resources.quiz"
              :key="index"
              class="bg-gray-50 rounded-xl p-6"
            >
              <div class="flex items-start justify-between mb-4">
                <span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                  {{ quiz.type }}
                </span>
                <span class="text-sm text-gray-500">第 {{ index + 1 }} 题</span>
              </div>
              <div class="text-lg font-medium text-gray-800 mb-4">{{ quiz.question }}</div>
              <div class="bg-white rounded-lg p-4 space-y-2">
                <div>
                  <span class="font-medium text-gray-700">答案：</span>
                  <span class="text-green-600 font-bold">{{ quiz.answer }}</span>
                </div>
                <div>
                  <span class="font-medium text-gray-700">解析：</span>
                  <span class="text-gray-600">{{ quiz.explanation }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'practice'" class="prose max-w-none">
            <MarkdownRenderer :content="resources.resources.practice_case" />
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-lg p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-4">📚 学习路径</h3>
        <div class="space-y-4">
          <div
            v-for="(item, index) in resources.learning_path"
            :key="item.stage"
            class="flex gap-4"
          >
            <div class="flex flex-col items-center">
              <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-bold">
                {{ index + 1 }}
              </div>
              <div v-if="index < resources.learning_path.length - 1" class="w-0.5 h-8 bg-gray-200"></div>
            </div>
            <div class="flex-1 bg-gray-50 rounded-xl p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="font-medium text-gray-800">{{ item.title }}</span>
                <span class="text-sm text-gray-500">{{ item.estimated_time }}</span>
              </div>
              <div class="text-sm text-gray-600 mb-3">{{ item.goal }}</div>
              <div>
                <div class="text-sm font-medium text-gray-700 mb-1">任务:</div>
                <ul class="text-sm text-gray-600 list-disc list-inside">
                  <li v-for="(task, idx) in item.tasks" :key="idx">{{ task }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
