<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { loadUserProfile } from './../api/userProfile'
import { getDynamicProfile, getRecommendations, generateRecommendationContent } from './../api/client'
import type { DynamicProfile } from './../types/profile'
import type { RecommendedResource } from './../api/client'
import mermaid from 'mermaid'
import { marked } from 'marked'

// 初始化 mermaid
mermaid.initialize({ startOnLoad: false, theme: 'neutral' })

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

const emit = defineEmits<{
  navigate: [page: 'home' | 'analyze' | 'collaborative' | 'evaluate' | 'courses' | 'account']
}>()

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 18) return '下午好'
  return '晚上好'
}

const greeting = ref(getGreeting())
const showSplash = ref(false)

const weeklyStudyData = ref([
  { day: '周一', hours: 3.5 },
  { day: '周二', hours: 2.8 },
  { day: '周三', hours: 4.2 },
  { day: '周四', hours: 1.5 },
  { day: '周五', hours: 3.0 },
  { day: '周六', hours: 5.5 },
  { day: '周日', hours: 4.0 },
])

const maxStudyHours = computed(() => Math.max(...weeklyStudyData.value.map(d => d.hours)))

const studyStreak = ref(7)
const todayProgress = ref(72)

const portrait = ref<DynamicProfile | null>(null)
const portraitLoading = ref(false)

const recommendations = ref<RecommendedResource[]>([])
const recommendationsLoading = ref(false)

// 学习内容展示模态框
const showLearningModal = ref(false)
const learningContent = ref<{
  lectureDoc: string
  exercises: string
  mindmap: string
  exerciseItems: any[]
  learningPath: string
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

interface AvatarTag {
  label: string
  value: string
  icon: string
  color: string
  category: string
}

const avatarTags = computed<AvatarTag[]>(() => {
  if (!portrait.value) return []
  
  const tags: AvatarTag[] = []
  const dims = portrait.value.dimensions || {}
  
  const iconMap: Record<string, string> = {
    '专业与年级': '🎓',
    '学习目标': '🎯',
    '知识基础': '📚',
    '认知风格': '🧠',
    '学习偏好': '⚡',
    '时间安排': '⏰',
    '学习动机': '🔥',
    '能力水平': '💪'
  }
  
  const colorMap = ['#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#10b981', '#3b82f6', '#f59e0b', '#14b8a6']
  
  Object.entries(dims).forEach(([key, dimension], index) => {
    if (dimension.value) {
      const displayValue = Array.isArray(dimension.value) ? dimension.value.slice(0, 2).join('、') : String(dimension.value)
      const confidence = dimension.confidence || 0
      
      tags.push({
        label: key,
        value: displayValue.length > 10 ? displayValue.slice(0, 10) + '…' : displayValue,
        icon: iconMap[key] || '📊',
        color: colorMap[index % colorMap.length],
        category: confidence >= 0.8 ? '核心' : confidence >= 0.5 ? '重要' : '基础'
      })
    }
  })
  
  return tags
})

const coreTags = computed(() => avatarTags.value.filter(t => t.category === '核心'))
const importantTags = computed(() => avatarTags.value.filter(t => t.category === '重要'))
const basicTags = computed(() => avatarTags.value.filter(t => t.category === '基础'))

async function loadPortrait() {
  portraitLoading.value = true
  try {
    const userProfile = loadUserProfile()
    const result = await getDynamicProfile(userProfile.userId)
    portrait.value = result.profile
  } catch (err) {
    console.error('加载画像失败', err)
    portrait.value = null
  } finally {
    portraitLoading.value = false
  }
}

async function loadRecommendations() {
  recommendationsLoading.value = true
  try {
    const userProfile = loadUserProfile()
    const result = await getRecommendations(userProfile.userId)
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
        explanation: '时间片轮转(RR)是一种公平的调度算法，适用于分时系统。'
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
        explanation: '二叉搜索树的中序遍历（左-根-右）结果是升序排列的。'
      },
      {
        question: '请简述AVL树的平衡机制和旋转操作的作用。',
        options: [],
        answer: 'AVL树通过平衡因子（左右子树高度差）维护平衡，要求任意结点的平衡因子绝对值不超过1。当插入或删除导致不平衡时，通过旋转操作（左旋、右旋、左右旋、右左旋）调整结构，恢复平衡。旋转操作在O(1)时间内完成，保证AVL树高度为O(log n)，确保操作时间复杂度为O(log n)。',
        explanation: 'AVL树是自平衡二叉搜索树，通过旋转维持平衡。'
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
        explanation: '正确答案是C。指令译码器负责解释指令的操作码，理解指令要执行的操作。'
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
        answer: 'CISC：指令数量多，格式复杂，寻址方式多样，支持复杂操作。代表：Intel x86。优点：编程方便，代码紧凑；缺点：执行周期长，难以流水线。RISC：指令数量少，格式简单，寻址方式少，每条指令执行周期短。代表：ARM、MIPS。优点：执行效率高，易于流水线；缺点：代码较长。',
        explanation: 'CISC和RISC是两种不同的指令系统设计理念。'
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
  renderMindmap(content.mindmap, 'home-mindmap-svg')
}

async function renderMindmap(mindmapCode: string, containerId: string) {
  try {
    const svgContainer = document.getElementById(containerId)
    if (!svgContainer) return
    
    // 使用 mermaid 渲染思维导图
    const { svg } = await mermaid.render('mindmap', mindmapCode)
    svgContainer.innerHTML = svg
  } catch (error) {
    console.error('渲染思维导图失败:', error)
    const svgContainer = document.getElementById(containerId)
    if (svgContainer) {
      svgContainer.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 20px;">思维导图渲染失败</p>'
    }
  }
}

function closeLearningModal() {
  showLearningModal.value = false
}

onMounted(() => {
  const justLoggedIn = localStorage.getItem('justLoggedIn')
  if (justLoggedIn === 'true') {
    showSplash.value = true
    localStorage.removeItem('justLoggedIn')
    setTimeout(() => {
      showSplash.value = false
    }, 2500)
  }
  loadPortrait()
  loadRecommendations()
})
</script>

<template>
  <div class="dashboard">
    <Transition name="splash">
      <div v-if="showSplash" class="splash-screen">
        <div class="splash-content">
          <div class="splash-logo">
            <span class="logo-icon">AI</span>
          </div>
          <div class="splash-text">
            <h1>{{ greeting }}，欢迎回来</h1>
            <p>正在准备您的学习环境...</p>
          </div>
          <div class="splash-progress">
            <div class="progress-bar-full">
              <div class="progress-fill-full"></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <div class="dashboard-main">
      <div class="surface study-panel-full">
        <div class="study-header-row">
          <div class="section-heading-small">
            <span class="section-kicker">学习习惯</span>
            <h2>本周学习趋势</h2>
          </div>
          <div class="study-stats-row">
            <div class="streak-badge">
              <span class="streak-icon">🔥</span>
              <span class="streak-text">连续学习 <strong>{{ studyStreak }}</strong> 天</span>
            </div>
            <div class="daily-progress">
              <span class="progress-label">今日目标</span>
              <div class="mini-progress-bar">
                <div class="mini-progress-fill" :style="{ width: todayProgress + '%' }"></div>
              </div>
              <span class="progress-value">{{ todayProgress }}%</span>
            </div>
          </div>
        </div>
        <div class="chart-container-full">
          <div class="chart-bars-full">
            <div
              v-for="data in weeklyStudyData"
              :key="data.day"
              class="bar-wrapper-full"
            >
              <div
                class="bar-full"
                :style="{ height: (Math.max(data.hours / maxStudyHours * 100, 20)) + '%' }"
              >
                <span class="bar-value-full">{{ data.hours }}h</span>
              </div>
              <span class="bar-label-full">{{ data.day.slice(1) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="surface portrait-panel-home">
        <div class="section-heading-small">
          <span class="section-kicker">学习画像</span>
          <h2>我的标签</h2>
          <button class="view-portrait-btn" @click="emit('navigate', 'account')">查看详情 →</button>
        </div>
        <div v-if="portraitLoading" class="portrait-loading">
          <div class="loading-spinner"></div>
          <p>加载画像中...</p>
        </div>
        <div v-else class="portrait-tags-container">
          <div v-if="coreTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">✨ 核心</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in coreTags" 
                :key="tag.label"
                class="portrait-tag-home core-tag-home"
                :style="{ '--tag-color': tag.color }"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="importantTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">📌 重要</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in importantTags" 
                :key="tag.label"
                class="portrait-tag-home important-tag-home"
                :style="{ '--tag-color': tag.color }"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="basicTags.length > 0" class="tags-group-home">
            <div class="tags-label-home">📋 基础</div>
            <div class="tags-row-home">
              <span 
                v-for="tag in basicTags" 
                :key="tag.label"
                class="portrait-tag-home basic-tag-home"
              >
                {{ tag.icon }} {{ tag.value }}
              </span>
            </div>
          </div>
          <div v-if="avatarTags.length === 0" class="empty-tags-home">
            <p>暂无画像数据</p>
            <small>开始学习后会自动生成</small>
          </div>
        </div>
      </div>

      <!-- 为你推荐板块 -->
      <div class="surface recommendation-panel">
        <div class="section-heading-small">
          <span class="section-kicker">个性化推荐</span>
          <h2>为你推荐</h2>
          <span class="recommendation-count">{{ recommendations.length }} 项</span>
        </div>
        
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
            v-for="item in recommendations.slice(0, 5)" 
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
    </div>

    <div class="dashboard-bottom">
      <div class="surface assessment-panel-new">
        <div class="section-heading-bottom">
          <div>
            <span class="section-kicker">评估概览</span>
            <h2>最近评估记录</h2>
          </div>
          <button @click="emit('navigate', 'evaluate')">查看详情 →</button>
        </div>
        <div class="assessment-list-new">
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">数据库系统</span>
              <span class="assessment-date">2小时前</span>
            </div>
            <div class="assessment-score high">95分</div>
          </div>
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">数据结构</span>
              <span class="assessment-date">1天前</span>
            </div>
            <div class="assessment-score medium">78分</div>
          </div>
          <div class="assessment-item-new">
            <div class="assessment-info">
              <span class="assessment-course">算法设计</span>
              <span class="assessment-date">3天前</span>
            </div>
            <div class="assessment-score low">65分</div>
          </div>
        </div>
      </div>

      <div class="surface progress-panel-new">
        <div class="section-heading-bottom">
          <div>
            <span class="section-kicker">学习进度</span>
            <h2>课程完成情况</h2>
          </div>
          <button @click="emit('navigate', 'courses')">查看全部 →</button>
        </div>
        <div class="progress-list-new">
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">🗄️</span>
              <span class="progress-name">数据库系统</span>
              <span class="progress-percent">75%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 75%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">📊</span>
              <span class="progress-name">数据结构</span>
              <span class="progress-percent">60%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 60%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">🧮</span>
              <span class="progress-name">算法设计</span>
              <span class="progress-percent">45%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 45%"></div>
            </div>
          </div>
          <div class="progress-item-new">
            <div class="progress-header">
              <span class="progress-icon">💻</span>
              <span class="progress-name">操作系统</span>
              <span class="progress-percent">30%</span>
            </div>
            <div class="progress-bar-new">
              <div class="progress-fill" style="width: 30%"></div>
            </div>
          </div>
        </div>
      </div>
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
            <div class="mindmap-container">
              <div id="home-mindmap-svg" class="mindmap-svg"></div>
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