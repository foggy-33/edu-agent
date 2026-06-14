<script setup lang="ts">
import { ref } from 'vue'
import type { Course } from '../types'

const emit = defineEmits<{
  navigate: [page: 'detail' | 'exercise', course?: Course]
}>()

const courses = ref<Course[]>([
  { 
    id: 1, 
    name: '数据库系统', 
    icon: '🗄️', 
    progress: 75, 
    totalHours: 32, 
    completedHours: 24, 
    status: 'in-progress', 
    lastAccess: '2小时前', 
    difficulty: '中等',
    questions: [
      {
        id: 1,
        type: 'single',
        chapter: '关系模型',
        question: '以下哪个是关系数据库的基本操作？',
        options: [
          { label: 'A', text: '插入(Insert)' },
          { label: 'B', text: '排序(Sort)' },
          { label: 'C', text: '合并(Merge)' },
          { label: 'D', text: '哈希(Hash)' }
        ],
        answer: 'A',
        analysis: '关系数据库的基本操作包括：选择(Select)、投影(Project)、连接(Join)、插入(Insert)、删除(Delete)、更新(Update)等。'
      },
      {
        id: 2,
        type: 'single',
        chapter: '函数依赖',
        question: '若X→Y且Y→Z，则下列哪个依赖一定成立？',
        options: [
          { label: 'A', text: 'X→YZ' },
          { label: 'B', text: 'X→Z' },
          { label: 'C', text: 'Y→X' },
          { label: 'D', text: 'Z→X' }
        ],
        answer: 'B',
        analysis: '根据Armstrong公理的传递律，如果X→Y且Y→Z，则X→Z一定成立。'
      },
      {
        id: 3,
        type: 'multiple',
        chapter: '范式',
        question: '以下哪些属于数据库范式？',
        options: [
          { label: 'A', text: '1NF' },
          { label: 'B', text: '2NF' },
          { label: 'C', text: '3NF' },
          { label: 'D', text: 'BCNF' }
        ],
        answer: ['A', 'B', 'C', 'D'],
        analysis: '1NF、2NF、3NF和BCNF都是数据库设计中的规范化范式，用于减少数据冗余和异常。'
      },
      {
        id: 4,
        type: 'judge',
        chapter: 'SQL基础',
        question: 'SQL中的SELECT语句用于查询数据。',
        answer: true,
        analysis: 'SELECT是SQL中最常用的查询语句，用于从数据库表中检索数据。'
      }
    ]
  },
  { 
    id: 2, 
    name: '数据结构', 
    icon: '📊', 
    progress: 60, 
    totalHours: 40, 
    completedHours: 24, 
    status: 'in-progress', 
    lastAccess: '1天前', 
    difficulty: '困难',
    questions: [
      {
        id: 101,
        type: 'single',
        chapter: '树与二叉树',
        question: '一棵完全二叉树有100个节点，则它的叶子节点数是？',
        options: [
          { label: 'A', text: '49' },
          { label: 'B', text: '50' },
          { label: 'C', text: '51' },
          { label: 'D', text: '52' }
        ],
        answer: 'B',
        analysis: '完全二叉树的性质：若节点总数为n，则叶子节点数为(n+1)/2向下取整或n/2向上取整。100个节点时，叶子节点数为50。'
      },
      {
        id: 102,
        type: 'single',
        chapter: '栈和队列',
        question: '栈的特点是？',
        options: [
          { label: 'A', text: '先进先出' },
          { label: 'B', text: '后进先出' },
          { label: 'C', text: '随机访问' },
          { label: 'D', text: '双向访问' }
        ],
        answer: 'B',
        analysis: '栈是一种后进先出(LIFO, Last In First Out)的数据结构，最后插入的元素最先被取出。'
      },
      {
        id: 103,
        type: 'judge',
        chapter: '链表',
        question: '链表的优点是插入和删除操作效率高。',
        answer: true,
        analysis: '链表不需要连续的内存空间，插入和删除操作只需要修改指针，时间复杂度为O(1)。'
      }
    ]
  },
  { 
    id: 3, 
    name: '算法设计', 
    icon: '🧮', 
    progress: 45, 
    totalHours: 48, 
    completedHours: 21, 
    status: 'in-progress', 
    lastAccess: '3天前', 
    difficulty: '困难',
    questions: [
      {
        id: 201,
        type: 'single',
        chapter: '动态规划',
        question: '动态规划算法通常适用于具有什么性质的问题？',
        options: [
          { label: 'A', text: '最优子结构和重叠子问题' },
          { label: 'B', text: '贪心选择性质' },
          { label: 'C', text: '分治性质' },
          { label: 'D', text: '回溯性质' }
        ],
        answer: 'A',
        analysis: '动态规划适用于具有最优子结构（大问题的最优解包含子问题的最优解）和重叠子问题（子问题会被重复计算）性质的问题。'
      },
      {
        id: 202,
        type: 'multiple',
        chapter: '排序算法',
        question: '以下哪些排序算法的平均时间复杂度是O(n log n)？',
        options: [
          { label: 'A', text: '快速排序' },
          { label: 'B', text: '归并排序' },
          { label: 'C', text: '堆排序' },
          { label: 'D', text: '冒泡排序' }
        ],
        answer: ['A', 'B', 'C'],
        analysis: '快速排序、归并排序和堆排序的平均时间复杂度都是O(n log n)，而冒泡排序的平均时间复杂度是O(n²)。'
      }
    ]
  },
  { 
    id: 4, 
    name: '操作系统', 
    icon: '💻', 
    progress: 30, 
    totalHours: 36, 
    completedHours: 11, 
    status: 'in-progress', 
    lastAccess: '1周前', 
    difficulty: '中等',
    questions: [
      {
        id: 301,
        type: 'single',
        chapter: '进程管理',
        question: '以下哪个不是进程调度算法？',
        options: [
          { label: 'A', text: 'FCFS' },
          { label: 'B', text: 'SJF' },
          { label: 'C', text: 'LRU' },
          { label: 'D', text: 'RR' }
        ],
        answer: 'C',
        analysis: 'FCFS(先来先服务)、SJF(短作业优先)、RR(时间片轮转)都是进程调度算法。LRU是页面置换算法。'
      },
      {
        id: 302,
        type: 'judge',
        chapter: '死锁',
        question: '死锁的四个必要条件是：互斥、请求与保持、不剥夺、循环等待。',
        answer: true,
        analysis: '这四个条件是死锁发生的必要条件，缺一不可。破坏任意一个条件即可预防死锁。'
      }
    ]
  },
  { 
    id: 5, 
    name: '计算机网络', 
    icon: '🌐', 
    progress: 100, 
    totalHours: 30, 
    completedHours: 30, 
    status: 'completed', 
    lastAccess: '2周前', 
    difficulty: '中等',
    questions: [
      {
        id: 401,
        type: 'single',
        chapter: 'TCP/IP协议',
        question: 'TCP协议是面向连接的可靠传输协议。',
        answer: 'A',
        options: [
          { label: 'A', text: '正确' },
          { label: 'B', text: '错误' }
        ],
        analysis: 'TCP(传输控制协议)是面向连接的、可靠的、基于字节流的传输层协议。'
      },
      {
        id: 402,
        type: 'single',
        chapter: 'OSI模型',
        question: 'HTTP协议工作在OSI模型的哪一层？',
        options: [
          { label: 'A', text: '传输层' },
          { label: 'B', text: '网络层' },
          { label: 'C', text: '应用层' },
          { label: 'D', text: '数据链路层' }
        ],
        answer: 'C',
        analysis: 'HTTP是应用层协议，工作在OSI模型的第七层——应用层。'
      }
    ]
  },
  { 
    id: 6, 
    name: '软件工程', 
    icon: '🔧', 
    progress: 0, 
    totalHours: 28, 
    completedHours: 0, 
    status: 'not-started', 
    lastAccess: '未开始', 
    difficulty: '简单',
    questions: [
      {
        id: 501,
        type: 'single',
        chapter: '软件生命周期',
        question: '软件开发生命周期中，哪个阶段确定系统必须做什么？',
        options: [
          { label: 'A', text: '需求分析' },
          { label: 'B', text: '设计' },
          { label: 'C', text: '编码' },
          { label: 'D', text: '测试' }
        ],
        answer: 'A',
        analysis: '需求分析阶段的主要任务是确定系统必须做什么，即确定系统的功能需求和非功能需求。'
      }
    ]
  },
])

const activeFilter = ref('all')
const filters = [
  { key: 'all', label: '全部' },
  { key: 'in-progress', label: '进行中' },
  { key: 'completed', label: '已完成' },
  { key: 'not-started', label: '未开始' },
]

function getStatusClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-700'
    case 'in-progress': return 'bg-blue-100 text-blue-700'
    case 'not-started': return 'bg-gray-100 text-gray-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'completed': return '已完成'
    case 'in-progress': return '进行中'
    case 'not-started': return '未开始'
    default: return status
  }
}

function getDifficultyClass(difficulty: string) {
  switch (difficulty) {
    case '简单': return 'bg-green-100 text-green-700'
    case '中等': return 'bg-yellow-100 text-yellow-700'
    case '困难': return 'bg-red-100 text-red-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function openCourseDetail(course: Course) {
  emit('navigate', 'detail', course)
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">总课程数</div>
        <div class="text-3xl font-bold mt-2">{{ courses.length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">已完成</div>
        <div class="text-3xl font-bold mt-2">{{ courses.filter(c => c.status === 'completed').length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">进行中</div>
        <div class="text-3xl font-bold mt-2">{{ courses.filter(c => c.status === 'in-progress').length }}门</div>
      </div>
      <div class="bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl p-6 text-white shadow-lg">
        <div class="text-white/80 text-sm">总学习时长</div>
        <div class="text-3xl font-bold mt-2">{{ courses.reduce((sum, c) => sum + c.completedHours, 0) }}小时</div>
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-lg p-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 class="text-lg font-bold text-gray-800">📚 我的课程</h2>
          <p class="text-sm text-gray-500 mt-1">管理您的学习课程和进度</p>
        </div>
        <div class="flex gap-2">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              activeFilter === filter.key
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="course in courses.filter(c => activeFilter === 'all' || c.status === activeFilter)"
          :key="course.id"
          @click="openCourseDetail(course)"
          class="bg-gray-50 rounded-xl p-5 cursor-pointer hover:bg-gray-100 hover:shadow-lg transition-all group"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="w-14 h-14 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
              {{ course.icon }}
            </div>
            <span :class="['px-3 py-1 rounded-full text-xs font-medium', getStatusClass(course.status)]">
              {{ getStatusLabel(course.status) }}
            </span>
          </div>
          
          <div class="mb-3">
            <h3 class="font-medium text-gray-800 group-hover:text-indigo-600 transition-colors">{{ course.name }}</h3>
            <div class="flex items-center gap-2 mt-1">
              <span :class="['px-2 py-0.5 rounded text-xs', getDifficultyClass(course.difficulty)]">
                {{ course.difficulty }}
              </span>
              <span class="text-xs text-gray-500">{{ course.lastAccess }}</span>
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between text-sm mb-2">
              <span class="text-gray-600">学习进度</span>
              <span class="font-medium text-indigo-600">{{ course.progress }}%</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                :style="{ width: course.progress + '%' }"
              ></div>
            </div>
            <div class="text-xs text-gray-500 mt-2">{{ course.completedHours }} / {{ course.totalHours }} 小时</div>
            <div class="text-xs text-gray-500">📝 {{ course.questions.length }} 道习题</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
