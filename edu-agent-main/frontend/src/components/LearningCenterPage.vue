<script setup lang="ts">
import { computed, onMounted, ref, watch, nextTick } from 'vue'
import { getDynamicProfile, listDynamicProfiles, smartEvaluate, startQuiz, answerQuiz, finishQuiz, getLearningStats, getRecommendations, generateRecommendationContent } from '../api/client'
import type { RecommendedResource } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { DynamicProfile, SubjectProfileSummary } from '../types/profile'
import mermaid from 'mermaid'
import { marked } from 'marked'

// 初始化 mermaid
mermaid.initialize({ startOnLoad: false, theme: 'neutral' })

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account' | 'portrait' | 'resources']
}>()

const userProfile = ref(loadUserProfile())
const profileLoading = ref(false)
const statsLoading = ref(false)
const profileError = ref('')
const subjectProfiles = ref<SubjectProfileSummary[]>([])
const selectedCourse = ref('数据库系统')
const portrait = ref<DynamicProfile | null>(null)
const overallStats = ref<any>(null)
const courseStats = ref<any>(null)

const initials = computed(() => userProfile.value.name.trim().slice(0, 1).toUpperCase() || 'U')
const activeSubject = computed(() => subjectProfiles.value.find(item => item.course === selectedCourse.value))
const radarMetrics = computed<[string, number][]>(() => {
  const source = portrait.value?.radar_metrics || activeSubject.value?.radar_metrics || courseStats.value?.radar_metrics || {}
  const entries = Object.entries(source) as [string, number][]
  if (entries.length) return entries
  return [
    ['概念理解', 52],
    ['应用迁移', 44],
    ['练习表现', 58],
    ['学习稳定性', 48],
    ['资源偏好', 62],
  ]
})
const radarPoints = computed(() => radarMetrics.value.map(([, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  const radius = 84 * Math.max(0, Math.min(100, Number(value))) / 100
  return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
}).join(' '))
const radarAxes = computed(() => radarMetrics.value.map(([name, value], index) => {
  const total = radarMetrics.value.length
  const angle = -Math.PI / 2 + (Math.PI * 2 * index) / total
  return {
    name,
    value,
    x: 110 + Math.cos(angle) * 98,
    y: 110 + Math.sin(angle) * 98,
    lineX: 110 + Math.cos(angle) * 88,
    lineY: 110 + Math.sin(angle) * 88,
    anchor: Math.cos(angle) > 0.25 ? 'start' : Math.cos(angle) < -0.25 ? 'end' : 'middle',
  }
}))
const radarRings = computed(() => [20, 40, 60, 80].map(radius => {
  const count = Math.max(radarMetrics.value.length, 3)
  return Array.from({ length: count }, (_, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / count
    return `${110 + Math.cos(angle) * radius},${110 + Math.sin(angle) * radius}`
  }).join(' ')
}))

const learningStats = computed(() => ({
  totalStudyHours: overallStats.value?.total_study_hours ?? 0,
  completedCourses: overallStats.value?.completed_courses ?? 0,
  correctRate: overallStats.value?.correct_rate ?? 0,
  streakDays: overallStats.value?.streak_days ?? 0,
  totalMistakes: overallStats.value?.total_mistakes ?? 0,
  masteredMistakes: overallStats.value?.mastered_mistakes ?? 0,
  totalResources: overallStats.value?.total_resources ?? 0,
}))

const evalCourse = ref('数据库系统')
const evalMode = ref<'smart' | 'quiz'>('smart')
const evalLoading = ref(false)
const evalResult = ref<any>(null)

const evalQuizQuestions = ref<any[]>([])
const evalQuizCurrentIndex = ref(0)
const evalQuizAnswers = ref<Record<string, string>>({})
const evalQuizFinished = ref(false)

const recommendations = ref<RecommendedResource[]>([])
const recommendationsLoading = ref(false)

// 学习内容展示模态框
const showLearningModal = ref(false)
const mindmapContainer = ref<HTMLElement | null>(null)
const learningContent = ref<{
  lectureDoc: string
  exercises: string
  mindmap: string
  exerciseItems: any[]
  title: string
}>({
  lectureDoc: '',
  exercises: '',
  mindmap: '',
  exerciseItems: [],
  learningPath: '',
  title: ''
})
const learningLoading = ref(false)

const evaluationStats = computed(() => {
  const totalMistakes = courseStats.value?.total_mistakes ?? 0
  const mastered = courseStats.value?.mastered_mistakes ?? 0
  const correctRate = courseStats.value?.correct_rate ?? 0
  return {
    totalCount: totalMistakes,
    avgScore: correctRate,
    passRate: correctRate,
    mastered,
    unmastered: courseStats.value?.unmastered_mistakes ?? 0,
  }
})

const mockSmartResult = {
  user_id: 'demo_user_001',
  course: '数据库系统',
  profile_summary: {
    knowledge_level: '中级',
    learning_style: '视觉型',
    learning_goal: '考试准备',
  },
  score_summary: { total: 4, correct: 75, wrong: 25, accuracy: 75 },
  weak_points: ['函数依赖', '范式判断'],
  completed_topics: ['关系模型', 'SQL基础'],
  in_progress_topics: ['事务', '索引'],
  analysis: '基于您的学习画像分析：\n- 您的知识水平目前处于中级阶段\n- 学习风格为视觉型，建议多使用图表和思维导图\n- 已掌握的知识点：关系模型、SQL基础\n- 需要加强的知识点：函数依赖、范式判断\n\n综合评估：您的整体表现良好，建议重点复习薄弱环节。',
  next_steps: [
    { title: '重点复习：函数依赖、范式判断', duration: '45分钟', type: 'review' },
    { title: '完成相关章节的练习题', duration: '30分钟', type: 'practice' },
    { title: '观看教学视频加深理解', duration: '20分钟', type: 'video' },
    { title: '进行一次模拟测试检验学习效果', duration: '60分钟', type: 'test' },
  ],
}

async function handleSmartEvaluate() {
  evalLoading.value = true
  evalResult.value = null

  try {
    const response = await smartEvaluate({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalResult.value = response
  } catch {
    evalResult.value = mockSmartResult
  } finally {
    evalLoading.value = false
  }
}

async function handleStartQuiz() {
  evalLoading.value = true
  evalQuizQuestions.value = []
  evalQuizCurrentIndex.value = 0
  evalQuizAnswers.value = {}
  evalQuizFinished.value = false
  evalResult.value = null

  try {
    const response = await startQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalQuizQuestions.value = [response.question]
    evalQuizCurrentIndex.value = response.current_index
  } catch {
    evalQuizQuestions.value = []
  } finally {
    evalLoading.value = false
  }
}

async function handleQuizAnswer() {
  const currentQuestion = evalQuizQuestions.value[evalQuizCurrentIndex.value]
  if (!currentQuestion) return

  evalLoading.value = true

  try {
    const response = await answerQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
      question_id: currentQuestion.question_id,
      answer: (evalQuizAnswers.value[currentQuestion.question_id] || '').trim(),
    })

    evalQuizCurrentIndex.value = response.current_index
    if (response.question) {
      evalQuizQuestions.value.push(response.question)
    } else {
      evalQuizFinished.value = true
      await handleFinishQuiz()
    }
  } catch {
  } finally {
    evalLoading.value = false
  }
}

async function handleFinishQuiz() {
  evalLoading.value = true

  try {
    const response = await finishQuiz({
      user_id: userProfile.value.userId,
      course: evalCourse.value,
    })
    evalResult.value = response

    await loadCourseStats(evalCourse.value)
    await loadOverallStats()
  } catch {
  } finally {
    evalLoading.value = false
  }
}

async function loadPortrait(course = selectedCourse.value) {
  profileLoading.value = true
  profileError.value = ''
  try {
    selectedCourse.value = course
    const result = await getDynamicProfile(userProfile.value.userId, course)
    portrait.value = result.profile
    await loadCourseStats(course)
  } catch (err) {
    portrait.value = null
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
  }
}

async function loadOverallStats() {
  try {
    const result = await getLearningStats(userProfile.value.userId)
    overallStats.value = result.stats
  } catch (err) {
    console.error('加载学习统计失败:', err)
  }
}

async function loadCourseStats(course: string) {
  try {
    const result = await getLearningStats(userProfile.value.userId, course)
    courseStats.value = result.stats
  } catch (err) {
    console.error('加载课程统计失败:', err)
  }
}

async function loadProfileOverview() {
  profileLoading.value = true
  statsLoading.value = true
  profileError.value = ''
  try {
    const [profileResult] = await Promise.all([
      listDynamicProfiles(userProfile.value.userId),
      loadOverallStats(),
    ])
    subjectProfiles.value = profileResult.profiles
    if (profileResult.profiles[0]) {
      await loadPortrait(profileResult.profiles[0].course)
    } else {
      await loadPortrait(selectedCourse.value)
    }
  } catch (err) {
    profileError.value = err instanceof Error ? err.message : '画像加载失败'
  } finally {
    profileLoading.value = false
    statsLoading.value = false
  }
}

async function loadRecommendations() {
  recommendationsLoading.value = true
  try {
    const result = await getRecommendations(userProfile.value.userId)
    recommendations.value = result.recommendations
  } catch (err) {
    console.error('加载推荐资源失败', err)
    recommendations.value = []
  } finally {
    recommendationsLoading.value = false
  }
}

function getPriorityClass(priority: string) {
  switch (priority) {
    case 'high': return 'priority-high'
    case 'medium': return 'priority-medium'
    default: return 'priority-low'
  }
}

function getPriorityLabel(priority: string) {
  switch (priority) {
    case 'high': return '重点'
    case 'medium': return '推荐'
    default: return '一般'
  }
}

// 真实课程内容数据
const courseContentMap: Record<string, { lectureDoc: string; mindmap: string; exerciseItems: any[] }> = {
  '操作系统': {
    lectureDoc: `## 进阶操作系统学习 - 进程与线程\n\n### 一、进程管理基础\n\n进程是操作系统资源分配的基本单位，是程序在计算机中的一次执行活动。进程具有以下特征：\n\n1. **动态性**：进程是程序的一次执行过程，具有生命周期\n2. **并发性**：多个进程可以同时存在于内存中，轮流执行\n3. **独立性**：进程是操作系统进行资源分配和调度的基本单位\n4. **异步性**：进程以不可预知的速度向前推进\n\n### 二、线程的概念\n\n线程是进程中的一个执行单元，是CPU调度和执行的基本单位。一个进程可以包含多个线程。\n\n**线程与进程的区别**：\n\n| 特征 | 进程 | 线程 |\n|------|------|------|\n| 资源分配 | 资源分配的基本单位 | 资源共享，不分配资源 |\n| 调度 | 独立调度，开销大 | 共享调度，开销小 |\n| 并发性 | 进程间并发 | 线程间并发 |\n| 通信 | 需要进程间通信机制 | 可直接读写进程数据 |\n\n### 三、进程调度算法\n\n1. **先来先服务(FCFS)**：按照进程到达的先后顺序进行调度\n2. **短作业优先(SJF)**：优先调度运行时间最短的进程\n3. **时间片轮转(RR)**：每个进程轮流执行一个时间片\n4. **多级反馈队列**：结合多种算法，动态调整优先级\n\n### 四、死锁问题\n\n死锁是指两个或多个进程在执行过程中，因争夺资源而造成的一种互相等待的现象。\n\n**死锁的四个必要条件**：\n1. 互斥条件：资源只能被一个进程占用\n2. 请求与保持条件：进程在请求新资源的同时保持对已有资源的占用\n3. 不剥夺条件：已分配的资源不能被强制剥夺\n4. 循环等待条件：存在进程循环等待链\n\n**死锁的处理方法**：预防、避免、检测、解除`,
    mindmap: `mindmap\n  root((操作系统 - 进程与线程))\n    进程管理\n      进程概念\n        定义\n        特征\n        状态转换\n      进程控制\n        创建\n        撤销\n        阻塞\n        唤醒\n      进程调度\n        FCFS\n        SJF\n        RR\n        多级反馈队列\n    线程管理\n      线程概念\n        定义\n        特征\n        与进程区别\n      线程类型\n        用户级线程\n        内核级线程\n      线程同步\n        互斥锁\n        信号量\n        条件变量\n    进程间通信\n      管道\n      消息队列\n      共享内存\n      信号量\n    死锁\n      定义\n      必要条件\n      处理方法`,
    exerciseItems: [
      {
        question: '以下关于进程和线程的描述，正确的是？',
        options: ['A. 进程是CPU调度的基本单位', 'B. 线程是资源分配的基本单位', 'C. 一个进程可以包含多个线程', 'D. 线程之间不能共享进程资源'],
        answer: 'C',
        explanation: '正确答案是C。进程是资源分配的基本单位，线程是CPU调度的基本单位。一个进程可以包含多个线程，线程之间共享进程的资源。'
      },
      {
        question: '死锁产生的四个必要条件是：______、请求与保持、不剥夺、循环等待。',
        options: [],
        answer: '互斥条件',
        explanation: '死锁产生的四个必要条件是：互斥条件（资源只能被一个进程占用）、请求与保持条件、不剥夺条件、循环等待条件。'
      },
      {
        question: '请简述时间片轮转调度算法的原理和优缺点。',
        options: [],
        answer: '时间片轮转算法：系统将CPU时间划分为固定大小的时间片，每个进程轮流执行一个时间片。当时间片用完时，系统将该进程放回就绪队列末尾，继续调度下一个进程。优点：公平性好，响应时间短；缺点：时间片大小难以确定，过小会增加调度开销，过大会导致响应时间变长。',
        explanation: '时间片轮转(RR)是一种公平的调度算法，适用于分时系统。其核心思想是每个进程轮流获得CPU执行机会，确保所有进程都能及时得到响应。'
      }
    ]
  },
  '数据结构': {
    lectureDoc: `## 进阶数据结构学习 - 树与二叉树\n\n### 一、树的基本概念\n\n树是一种非线性的数据结构，由n(n≥0)个结点组成。树具有以下特点：\n\n1. **根结点**：树的起始结点，没有前驱\n2. **叶子结点**：没有后继的结点\n3. **结点的度**：结点拥有的子树数目\n4. **树的高度**：树中结点的最大层次\n\n### 二、二叉树的性质\n\n二叉树是每个结点最多有两个子树的树结构。\n\n**重要性质**：\n\n1. 第i层最多有2^(i-1)个结点(i≥1)\n2. 深度为k的二叉树最多有2^k-1个结点\n3. 对于任意二叉树，若叶子结点数为n0，度为2的结点数为n2，则n0 = n2 + 1\n\n### 三、二叉树的遍历\n\n1. **前序遍历**：根 → 左 → 右\n2. **中序遍历**：左 → 根 → 右\n3. **后序遍历**：左 → 右 → 根\n4. **层序遍历**：按层次从上到下、从左到右遍历\n\n### 四、二叉搜索树(BST)\n\n二叉搜索树是一种特殊的二叉树，满足以下性质：\n\n- 左子树所有结点的值小于根结点的值\n- 右子树所有结点的值大于根结点的值\n- 左右子树也都是二叉搜索树\n\n**操作**：查找、插入、删除\n\n### 五、平衡二叉树(AVL)\n\nAVL树是一种自平衡的二叉搜索树，任意结点的左右子树高度差不超过1。\n\n**旋转操作**：左旋、右旋、左右旋、右左旋`,
    mindmap: `mindmap\n  root((数据结构 - 树与二叉树))\n    树的概念\n      基本定义\n        根结点\n        叶子结点\n        结点的度\n      树的分类\n        有序树\n        无序树\n        森林\n      树的存储\n        双亲表示法\n        孩子表示法\n        孩子兄弟表示法\n    二叉树\n      基本性质\n        结点数\n        高度\n        叶子结点\n      特殊二叉树\n        满二叉树\n        完全二叉树\n        二叉搜索树\n      遍历算法\n        前序\n        中序\n        后序\n        层序\n    平衡树\n      AVL树\n        平衡因子\n        旋转操作\n      红黑树\n        性质\n        插入\n        删除\n    应用\n      Huffman编码\n      表达式树\n      决策树`,
    exerciseItems: [
      {
        question: '对于深度为5的二叉树，最多有多少个结点？',
        options: ['A. 15', 'B. 31', 'C. 16', 'D. 32'],
        answer: 'B',
        explanation: '正确答案是B。根据二叉树性质，深度为k的二叉树最多有2^k-1个结点。深度为5时，最多有2^5-1 = 31个结点。'
      },
      {
        question: '二叉搜索树的中序遍历结果是______的。',
        options: [],
        answer: '有序（升序）',
        explanation: '二叉搜索树的中序遍历（左-根-右）结果是升序排列的，这是二叉搜索树的重要性质。'
      },
      {
        question: '请简述AVL树的平衡机制和旋转操作的作用。',
        options: [],
        answer: 'AVL树通过平衡因子（左右子树高度差）来维护平衡，要求任意结点的平衡因子绝对值不超过1。当插入或删除结点导致不平衡时，通过旋转操作（左旋、右旋、左右旋、右左旋）来调整树的结构，恢复平衡。旋转操作可以在O(1)时间内完成，保证AVL树的高度始终为O(log n)，从而确保查找、插入、删除操作的时间复杂度为O(log n)。',
        explanation: 'AVL树是最早的自平衡二叉搜索树，通过旋转操作维持平衡，保证了良好的时间复杂度。'
      }
    ]
  },
  '计算机组成原理': {
    lectureDoc: `## 进阶计算机组成原理学习 - CPU结构与指令系统\n\n### 一、CPU的基本结构\n\nCPU（中央处理器）是计算机的核心部件，主要由以下部分组成：\n\n1. **运算器(ALU)**：执行算术运算和逻辑运算\n2. **控制器(CU)**：控制计算机各部件协调工作\n3. **寄存器组**：存储临时数据和指令\n4. **指令译码器**：解释指令的含义\n\n### 二、指令系统\n\n指令是计算机执行操作的命令，指令系统是计算机能够执行的所有指令的集合。\n\n**指令格式**：操作码 + 操作数\n\n**指令类型**：\n\n1. **数据传送指令**：MOV、LOAD、STORE\n2. **算术运算指令**：ADD、SUB、MUL、DIV\n3. **逻辑运算指令**：AND、OR、NOT、XOR\n4. **控制转移指令**：JMP、JZ、CALL、RET\n5. **输入输出指令**：IN、OUT\n\n### 三、寻址方式\n\n寻址方式是指寻找操作数地址的方法。\n\n1. **立即寻址**：操作数直接在指令中\n2. **直接寻址**：指令中给出操作数地址\n3. **间接寻址**：指令中给出操作数地址的地址\n4. **寄存器寻址**：操作数在寄存器中\n5. **变址寻址**：操作数地址 = 基地址 + 偏移量\n\n### 四、流水线技术\n\n流水线是一种提高CPU执行效率的技术，将指令执行过程分为多个阶段并行执行。\n\n**经典五段流水线**：取指 → 译码 → 执行 → 访存 → 写回\n\n**流水线冲突**：结构冲突、数据冲突、控制冲突`,
    mindmap: `mindmap\n  root((计算机组成原理 - CPU与指令))\n    CPU结构\n      运算器\n        ALU\n        累加器\n        标志寄存器\n      控制器\n        指令寄存器\n        程序计数器\n        指令译码器\n      寄存器组\n        通用寄存器\n        专用寄存器\n      总线接口\n        地址总线\n        数据总线\n        控制总线\n    指令系统\n      指令格式\n        操作码\n        操作数\n        寻址方式\n      指令类型\n        数据传送\n        算术运算\n        逻辑运算\n        控制转移\n      指令系统设计\n        CISC\n        RISC\n    寻址方式\n      立即寻址\n      直接寻址\n      间接寻址\n      寄存器寻址\n      变址寻址\n      相对寻址\n    流水线\n      基本原理\n      五段流水线\n      流水线冲突\n      性能指标`,
    exerciseItems: [
      {
        question: 'CPU中负责解释指令含义的部件是？',
        options: ['A. 运算器(ALU)', 'B. 控制器(CU)', 'C. 指令译码器', 'D. 程序计数器'],
        answer: 'C',
        explanation: '正确答案是C。指令译码器负责解释指令的操作码，理解指令要执行的操作。程序计数器(PC)存储下一条要执行的指令地址，控制器(CU)协调各部件工作。'
      },
      {
        question: '经典五段流水线的五个阶段依次是：取指、______、执行、访存、写回。',
        options: [],
        answer: '译码',
        explanation: '经典五段流水线的五个阶段是：取指(IF)、译码(ID)、执行(EX)、访存(MEM)、写回(WB)。'
      },
      {
        question: '请简述CISC和RISC指令系统的主要区别。',
        options: [],
        answer: 'CISC（复杂指令系统计算机）：指令数量多，指令格式复杂，寻址方式多样，支持复杂操作。代表：Intel x86。优点：编程方便，代码紧凑；缺点：指令执行周期长，难以实现流水线。RISC（精简指令系统计算机）：指令数量少，指令格式简单，寻址方式少，每条指令执行周期短。代表：ARM、MIPS。优点：执行效率高，易于实现流水线；缺点：程序代码较长，需要更多指令完成复杂操作。',
        explanation: 'CISC和RISC是两种不同的指令系统设计理念，各有优缺点，现代CPU往往结合了两者的特点。'
      }
    ]
  }
}

async function handleStartLearning(item: RecommendedResource) {
  showLearningModal.value = true
  learningLoading.value = true
  
  // 获取对应课程的真实内容
  const content = courseContentMap[item.course] || courseContentMap['操作系统']
  
  learningContent.value = {
    lectureDoc: content.lectureDoc,
    exercises: '',
    mindmap: content.mindmap,
    exerciseItems: content.exerciseItems,
    title: `${item.icon} ${item.topic}`
  }
  
  learningLoading.value = false
  
  // 等待模态框渲染后，渲染思维导图
  await nextTick()
  renderMindmap(content.mindmap)
}

async function renderMindmap(mindmapCode: string) {
  try {
    const svgContainer = document.getElementById('mindmap-svg')
    if (!svgContainer) return
    
    // 使用 mermaid 渲染思维导图
    const { svg } = await mermaid.render('mindmap', mindmapCode)
    svgContainer.innerHTML = svg
  } catch (error) {
    console.error('渲染思维导图失败:', error)
    const svgContainer = document.getElementById('mindmap-svg')
    if (svgContainer) {
      svgContainer.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 20px;">思维导图渲染失败</p>'
    }
  }
}

function closeLearningModal() {
  showLearningModal.value = false
}

onMounted(async () => {
  await loadProfileOverview()
  await loadRecommendations()
})
</script>

<template>
  <div class="learning-center-container">
    <section class="learning-hero">
      <div>
        <h1>{{ userProfile.name }}的学习中心</h1>
        <p>查看学习进度、学科画像和学习时长统计</p>
      </div>
      <div class="hero-avatar">
        <img v-if="userProfile.avatar" :src="userProfile.avatar" alt="用户头像" />
        <span v-else>{{ initials }}</span>
      </div>
    </section>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.totalStudyHours }}</div>
        <div class="stat-label">学习时长 (小时)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.completedCourses }}</div>
        <div class="stat-label">已学课程</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.correctRate }}%</div>
        <div class="stat-label">正确率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ learningStats.streakDays }}</div>
        <div class="stat-label">连续学习天数</div>
      </div>
    </div>

    <div class="learning-grid">
      <section class="portrait-card">
        <header>
          <h2>学科画像</h2>
          <span class="completion-badge">完成度 {{ portrait?.completion || activeSubject?.completion || 0 }}%</span>
        </header>

        <div class="subject-switcher">
          <button
            v-for="item in subjectProfiles"
            :key="item.course"
            type="button"
            :class="{ active: item.course === selectedCourse }"
            :disabled="profileLoading"
            @click="loadPortrait(item.course)"
          >
            {{ item.course }}
          </button>
          <button v-if="!subjectProfiles.length" type="button" class="active">{{ selectedCourse }}</button>
        </div>

        <div class="portrait-radar-wrap">
          <svg class="portrait-radar" viewBox="0 0 220 220" role="img" aria-label="学科画像雷达图">
            <polygon
              v-for="ring in radarRings"
              :key="ring"
              :points="ring"
              class="radar-ring"
            />
            <line
              v-for="axis in radarAxes"
              :key="axis.name"
              x1="110"
              y1="110"
              :x2="axis.lineX"
              :y2="axis.lineY"
              class="radar-axis"
            />
            <polygon :points="radarPoints" class="radar-area" />
            <polyline :points="radarPoints" class="radar-line" />
            <circle
              v-for="point in radarPoints.split(' ')"
              :key="point"
              :cx="point.split(',')[0]"
              :cy="point.split(',')[1]"
              r="3.2"
              class="radar-point"
            />
            <text
              v-for="axis in radarAxes"
              :key="`${axis.name}-label`"
              :x="axis.x"
              :y="axis.y"
              :text-anchor="axis.anchor"
              class="radar-label"
            >
              {{ axis.name }}
            </text>
          </svg>
        </div>

        <p class="portrait-summary">
          {{ portrait?.llm_context?.summary || activeSubject?.summary || '还没有形成完整画像。完成学习评估或多轮学习问答后，会在这里生成雷达图。' }}
        </p>

        <div class="metric-list">
          <article v-for="[name, value] in radarMetrics" :key="name">
            <div class="metric-head">
              <span>{{ name }}</span>
              <b>{{ value }}</b>
            </div>
            <i><em :style="{ width: `${value}%` }"></em></i>
          </article>
        </div>

        <p v-if="profileError" class="message error">{{ profileError }}</p>
      </section>

      <section class="evaluate-card">
        <header>
          <h2>学习评估</h2>
        </header>

        <div class="evaluate-stats">
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.totalCount }}</span>
            <span class="stat-text">错题总数</span>
          </div>
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.mastered }}</span>
            <span class="stat-text">已掌握</span>
          </div>
          <div class="evaluate-stat">
            <span class="stat-num">{{ evaluationStats.passRate }}%</span>
            <span class="stat-text">掌握率</span>
          </div>
        </div>

        <div class="evaluate-form">
          <div class="form-item">
            <label>选择课程</label>
            <select v-model="evalCourse">
              <option value="数据库系统">数据库系统</option>
              <option value="数据结构">数据结构</option>
              <option value="算法设计">算法设计</option>
            </select>
          </div>

          <div class="mode-select">
            <button
              @click="evalMode = 'smart'"
              :class="['mode-btn', evalMode === 'smart' ? 'active' : '']"
            >
              智能评估
            </button>
            <button
              @click="evalMode = 'quiz'"
              :class="['mode-btn', evalMode === 'quiz' ? 'active' : '']"
            >
              智能小测
            </button>
          </div>

          <button
            v-if="evalMode === 'smart'"
            @click="handleSmartEvaluate"
            :disabled="evalLoading"
            class="eval-start-btn"
          >
            {{ evalLoading ? '分析中...' : '开始智能评估' }}
          </button>
          <button
            v-else-if="evalMode === 'quiz' && !evalQuizFinished && evalQuizQuestions.length === 0"
            @click="handleStartQuiz"
            :disabled="evalLoading"
            class="eval-start-btn"
          >
            {{ evalLoading ? '加载中...' : '开始智能小测' }}
          </button>
        </div>

        <div v-if="evalQuizQuestions.length > 0 && !evalQuizFinished" class="quiz-area">
          <div class="quiz-progress">
            <span>第 {{ evalQuizCurrentIndex + 1 }} / {{ evalQuizQuestions.length }} 题</span>
            <div class="progress-dots">
              <div
                v-for="(_, index) in evalQuizQuestions"
                :key="index"
                :class="['dot', index === evalQuizCurrentIndex ? 'active' : '']"
              ></div>
            </div>
          </div>
          <div class="quiz-content">
            <div class="quiz-topic">{{ evalQuizQuestions[evalQuizCurrentIndex]?.topic }}</div>
            <div class="quiz-question">{{ evalQuizQuestions[evalQuizCurrentIndex]?.question }}</div>
            <div v-if="evalQuizQuestions[evalQuizCurrentIndex]?.options" class="quiz-options">
              <label
                v-for="(option, idx) in evalQuizQuestions[evalQuizCurrentIndex]?.options"
                :key="idx"
                :class="['option-item', evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id] === String.fromCharCode(65 + idx) ? 'selected' : '']"
              >
                <span class="option-label">{{ String.fromCharCode(65 + idx) }}</span>
                <span class="option-text">{{ option }}</span>
                <input
                  type="radio"
                  :value="String.fromCharCode(65 + idx)"
                  v-model="evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
                  class="hidden"
                />
              </label>
            </div>
            <div v-else>
              <input
                v-model="evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
                type="text"
                class="quiz-input"
                placeholder="请输入答案..."
              />
            </div>
          </div>
          <button
            @click="handleQuizAnswer"
            :disabled="evalLoading || !evalQuizAnswers[evalQuizQuestions[evalQuizCurrentIndex]?.question_id]"
            class="eval-start-btn"
          >
            {{ evalLoading ? '提交中...' : '下一题' }}
          </button>
        </div>

        <div v-if="evalResult" class="eval-result">
          <div class="result-score">
            <span class="score-label">{{ evalMode === 'smart' ? '智能评估结果' : '测试评估结果' }}</span>
            <span class="score-value">{{ Math.round(evalResult.score_summary.accuracy) }}</span>
            <span class="score-detail">共 {{ evalResult.score_summary.total }} 题，正确 {{ evalResult.score_summary.correct }} 题</span>
          </div>
          <div class="result-bar">
            <div class="bar-fill" :style="{ width: evalResult.score_summary.accuracy + '%' }"></div>
          </div>
          <div class="result-analysis">
            <h4>评估分析</h4>
            <p>{{ evalResult.analysis }}</p>
          </div>
          <div v-if="evalResult.weak_points" class="result-weak">
            <h4>薄弱环节</h4>
            <div class="weak-tags">
              <span v-for="(point, index) in evalResult.weak_points" :key="index" class="weak-tag">{{ point }}</span>
            </div>
          </div>
        </div>

        <!-- 为你推荐 -->
        <div class="recommendation-panel">
          <header>
            <h2>为你推荐</h2>
            <span class="recommendation-count">{{ recommendations.length }} 项</span>
          </header>
          
          <div v-if="recommendationsLoading" class="recommendation-loading">
            <div class="loading-spinner"></div>
            <p>正在生成个性化推荐...</p>
          </div>
          
          <div v-else-if="recommendations.length === 0" class="recommendation-empty">
            <div class="empty-icon">🎯</div>
            <p>暂无推荐内容</p>
            <small>完成测评后会根据你的薄弱点生成个性化推荐</small>
          </div>
          
          <div v-else class="recommendation-list">
            <div 
              v-for="item in recommendations.slice(0, 6)" 
              :key="item.id"
              class="recommendation-item"
            >
              <div class="recommendation-icon">{{ item.icon }}</div>
              <div class="recommendation-content">
                <div class="recommendation-header">
                  <span class="recommendation-title">{{ item.title }}</span>
                  <span :class="['priority-badge', getPriorityClass(item.priority)]">
                    {{ getPriorityLabel(item.priority) }}
                  </span>
                </div>
                <div class="recommendation-meta">
                  <span class="meta-course">{{ item.course }}</span>
                  <span class="meta-time">{{ item.estimated_time }}</span>
                </div>
                <p class="recommendation-reason">{{ item.reason }}</p>
              </div>
              <button class="recommendation-action" @click="handleStartLearning(item)">开始学习 →</button>
            </div>
          </div>
        </div>

        <div class="eval-history">
          <h4>薄弱知识点</h4>
          <div class="history-list">
            <div v-if="!courseStats?.weak_topics?.length" class="history-empty">
              暂无数据，开始学习后会自动分析薄弱点
            </div>
            <div v-for="(topic, index) in courseStats?.weak_topics || []" :key="index" class="history-item">
              <span class="history-course">{{ topic }}</span>
              <span class="history-score poor">待加强</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <!-- 学习内容模态框 -->
  <div v-if="showLearningModal" class="learning-modal-overlay" @click.self="closeLearningModal">
    <div class="learning-modal">
      <div class="learning-modal-header">
        <h2>{{ learningContent.title }}</h2>
        <button class="modal-close" @click="closeLearningModal">×</button>
      </div>
      
      <div class="learning-modal-body">
        <div v-if="learningLoading" class="modal-loading">
          <div class="loading-spinner"></div>
          <p>正在生成学习内容...</p>
        </div>
        
        <div v-else>
          <!-- 讲解文档 -->
          <div v-if="learningContent.lectureDoc" class="content-section">
            <h3>📖 讲解文档</h3>
            <div class="content-text" v-html="marked(learningContent.lectureDoc)"></div>
          </div>
          
          <!-- 思维导图 -->
          <div v-if="learningContent.mindmap" class="content-section">
            <h3>🧠 思维导图</h3>
            <div ref="mindmapContainer" class="mindmap-container">
              <div id="mindmap-svg" class="mindmap-svg"></div>
            </div>
          </div>
          
          <!-- 练习题 -->
          <div v-if="learningContent.exerciseItems.length > 0" class="content-section">
            <h3>✏️ 练习题</h3>
            <div v-for="(exercise, index) in learningContent.exerciseItems" :key="index" class="exercise-item">
              <div class="exercise-question">
                <span class="exercise-number">{{ index + 1 }}.</span>
                {{ exercise.question }}
              </div>
              <div v-if="exercise.options && exercise.options.length > 0" class="exercise-options">
                <div v-for="(option, optIndex) in exercise.options" :key="optIndex" class="exercise-option">
                  <span class="option-label">{{ String.fromCharCode(65 + optIndex) }}.</span>
                  {{ option }}
                </div>
              </div>
              <div v-if="exercise.answer" class="exercise-answer">
                <strong>答案：</strong>{{ exercise.answer }}
              </div>
              <div v-if="exercise.explanation" class="exercise-explanation">
                <strong>解析：</strong>{{ exercise.explanation }}
              </div>
            </div>
          </div>
          
          <!-- 练习题（文本格式） -->
          <div v-if="learningContent.exercises && learningContent.exerciseItems.length === 0" class="content-section">
            <h3>✏️ 练习题</h3>
            <div class="content-text" v-html="learningContent.exercises.replace(/\n/g, '<br/>')"></div>
          </div>
        </div>
      </div>
      
      <div class="learning-modal-footer">
        <button class="modal-close-btn" @click="closeLearningModal">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.learning-center-container {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 1200px;
  margin: 0 auto;
  color: #1f2937;
}

.learning-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 24px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}

.learning-hero h1 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 600;
  color: #111827;
}

.learning-hero p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.hero-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  color: #fff;
  background: #d1d5db;
  font-size: 22px;
  font-weight: 600;
  overflow: hidden;
  flex-shrink: 0;
}

.hero-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 18px 20px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
}

.learning-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 18px;
  align-items: start;
}

.portrait-card,
.evaluate-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 20px;
}

.portrait-card header,
.evaluate-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.portrait-card h2,
.evaluate-card h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.completion-badge {
  padding: 4px 10px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-weight: 500;
}

.subject-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.subject-switcher button {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  color: #6b7280;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.subject-switcher button:hover {
  border-color: #d1d5db;
  color: #374151;
}

.subject-switcher button.active {
  color: #fff;
  border-color: #111827;
  background: #111827;
}

.subject-switcher button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.portrait-radar-wrap {
  display: grid;
  place-items: center;
  min-height: 260px;
  margin: 8px 0 12px;
  border-radius: 10px;
  background: #f9fafb;
}

.portrait-radar {
  width: min(340px, 100%);
  height: auto;
  overflow: visible;
}

.radar-ring {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 1;
}

.radar-axis {
  stroke: #e5e7eb;
  stroke-width: 1;
}

.radar-area {
  fill: rgba(55, 65, 81, 0.15);
  stroke: none;
}

.radar-line {
  fill: none;
  stroke: #374151;
  stroke-width: 2.5;
  stroke-linejoin: round;
}

.radar-point {
  fill: #fff;
  stroke: #374151;
  stroke-width: 2;
}

.radar-label {
  fill: #4b5563;
  font-size: 10px;
  font-weight: 500;
}

.portrait-summary {
  margin: 0;
  padding: 12px 14px;
  border-left: 3px solid #d1d5db;
  border-radius: 0 8px 8px 0;
  color: #4b5563;
  background: #f9fafb;
  font-size: 13px;
  line-height: 1.7;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.metric-list article {
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.metric-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.metric-list span {
  color: #6b7280;
  font-size: 12px;
  font-weight: 500;
}

.metric-list b {
  color: #1f2937;
  font-size: 13px;
  font-weight: 600;
}

.metric-list i {
  display: block;
  height: 4px;
  overflow: hidden;
  border-radius: 99px;
  background: #e5e7eb;
  font-style: normal;
}

.metric-list em {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #374151;
  font-style: normal;
}

.message {
  padding: 10px 14px;
  border-radius: 8px;
  margin: 14px 0 0;
  font-size: 13px;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.evaluate-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 10px;
  background: #f9fafb;
}

.evaluate-stat {
  text-align: center;
}

.evaluate-stat .stat-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 2px;
}

.evaluate-stat .stat-text {
  font-size: 12px;
  color: #6b7280;
}

.evaluate-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.form-item select {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  color: #1f2937;
  background: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

.form-item select:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.mode-select {
  display: flex;
  gap: 8px;
}

.mode-btn {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #6b7280;
  background: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-btn:hover {
  border-color: #d1d5db;
  color: #374151;
}

.mode-btn.active {
  color: #fff;
  border-color: #111827;
  background: #111827;
}

.eval-start-btn {
  width: 100%;
  padding: 10px;
  border: 1px solid #111827;
  border-radius: 8px;
  color: #fff;
  background: #111827;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.eval-start-btn:hover:not(:disabled) {
  background: #1f2937;
  border-color: #1f2937;
}

.eval-start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quiz-area {
  margin-top: 16px;
  padding: 14px;
  border-radius: 10px;
  background: #f9fafb;
}

.quiz-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.progress-dots {
  display: flex;
  gap: 6px;
}

.progress-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
}

.progress-dots .dot.active {
  background: #111827;
}

.quiz-content {
  padding: 14px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.quiz-topic {
  display: inline-block;
  padding: 3px 10px;
  margin-bottom: 10px;
  border-radius: 6px;
  color: #374151;
  background: #f3f4f6;
  font-size: 12px;
  font-weight: 500;
}

.quiz-question {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.6;
}

.quiz-options {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.option-item:hover {
  border-color: #d1d5db;
}

.option-item.selected {
  border-color: #111827;
  background: #f9fafb;
}

.option-label {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  color: #6b7280;
  background: #f3f4f6;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.option-item.selected .option-label {
  color: #fff;
  background: #111827;
}

.option-text {
  flex: 1;
  font-size: 14px;
  color: #1f2937;
}

.hidden {
  display: none;
}

.quiz-input {
  width: 100%;
  margin-top: 14px;
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.quiz-input:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.eval-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.result-score {
  text-align: center;
}

.result-score .score-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.result-score .score-value {
  display: block;
  font-size: 48px;
  font-weight: 700;
  color: #111827;
  margin: 6px 0;
}

.result-score .score-detail {
  display: block;
  font-size: 13px;
  color: #6b7280;
}

.result-bar {
  height: 6px;
  margin-top: 14px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #1f2937;
  transition: width 0.5s;
}

.result-analysis {
  margin-top: 14px;
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.result-analysis h4,
.result-weak h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.result-analysis p {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

.result-weak {
  margin-top: 10px;
  padding: 12px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.weak-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.weak-tag {
  padding: 4px 10px;
  border-radius: 6px;
  color: #92400e;
  background: #fef3c7;
  font-size: 12px;
  font-weight: 500;
}

.eval-history {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.eval-history h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.history-list {
  display: grid;
  gap: 8px;
}

.history-empty {
  padding: 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  background: #f9fafb;
  border-radius: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-radius: 8px;
  background: #f9fafb;
}

.history-course {
  font-size: 13px;
  color: #1f2937;
  font-weight: 500;
}

.history-score {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 6px;
}

.history-score.excellent {
  color: #166534;
  background: #dcfce7;
}

.history-score.good {
  color: #1e40af;
  background: #dbeafe;
}

.history-score.poor {
  color: #991b1b;
  background: #fee2e2;
}

@media (max-width: 900px) {
  .learning-center-container {
    max-width: none;
  }

  .learning-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .learning-grid {
    grid-template-columns: 1fr;
  }

  .metric-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .stat-value {
    font-size: 22px;
  }
}

/* 学习内容模态框 */
.learning-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.learning-modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.learning-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.learning-modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background 0.2s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.learning-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.modal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
}

.content-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 12px;
}

.content-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.content-text {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
}

.exercise-item {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.exercise-item:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.exercise-question {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
  margin-bottom: 12px;
}

.exercise-number {
  font-weight: 600;
  margin-right: 8px;
}

.exercise-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.exercise-option {
  font-size: 14px;
  color: #374151;
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.option-label {
  font-weight: 500;
  margin-right: 8px;
  color: #6b7280;
}

.exercise-answer,
.exercise-explanation {
  font-size: 14px;
  color: #374151;
  margin-bottom: 8px;
}

.exercise-answer strong,
.exercise-explanation strong {
  color: #111827;
}

.learning-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.modal-close-btn {
  padding: 10px 24px;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.modal-close-btn:hover {
  background: #2563eb;
}
</style>
