<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { listCourseMaterials } from '../api/client'
import { loadUserProfile } from '../api/userProfile'
import type { Course, CourseChapter, CoursePdfMaterial } from '../types'
import CoursePdfReader from './CoursePdfReader.vue'

const props = defineProps<{
  course: Course
}>()

const emit = defineEmits<{
  navigate: [page: 'courses' | 'exercise' | 'analyze' | 'mistakes']
}>()

const chapters = computed(() => props.course.chapters || [])
const goals = computed(() => props.course.goals || [])
const suggestions = computed(() => props.course.suggestions || [])
const materials = ref<CoursePdfMaterial[]>([])
const materialsLoading = ref(false)
const materialsError = ref('')
const activeMaterial = ref<CoursePdfMaterial | null>(null)
const userId = loadUserProfile().userId

function chapterMaterials(chapter: CourseChapter) {
  const chapterName = chapter.name.toLowerCase()
  return materials.value.filter((material) => {
    const name = material.name.toLowerCase()
    if (name.includes('绪论')) return chapterName.includes('导论') || chapterName.includes('绪论')
    if (name.includes('关系模型')) return chapterName.includes('关系模型')
    if (name.includes('sql')) return chapterName.includes('sql')
    if (name.includes('安全')) return chapterName.includes('安全')
    return false
  })
}

const supplementalMaterials = computed(() => {
  const assignedIds = new Set(chapters.value.flatMap((chapter) => chapterMaterials(chapter).map((item) => item.id)))
  return materials.value.filter((item) => !assignedIds.has(item.id))
})

async function loadMaterials() {
  materialsLoading.value = true
  materialsError.value = ''
  activeMaterial.value = null
  try {
    const result = await listCourseMaterials(props.course.name)
    materials.value = result.materials
  } catch (cause) {
    materials.value = []
    materialsError.value = cause instanceof Error ? cause.message : '课程资料加载失败'
  } finally {
    materialsLoading.value = false
  }
}

function formatFileSize(size: number) {
  return size >= 1024 * 1024
    ? `${(size / 1024 / 1024).toFixed(1)} MB`
    : `${Math.max(1, Math.round(size / 1024))} KB`
}

onMounted(loadMaterials)
watch(() => props.course.name, loadMaterials)

const courseSummary = computed(() => [
  { label: '章节数', value: `${chapters.value.length}章` },
  { label: '最近学习', value: props.course.lastAccess },
  { label: '基础题', value: `${props.course.questions.length}道` },
])

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

function getChapterStatusClass(status: string) {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-600'
    case 'current': return 'bg-amber-100 text-amber-600'
    default: return 'bg-gray-100 text-gray-400'
  }
}

function chapterStatusLabel(chapter: CourseChapter) {
  switch (chapter.status) {
    case 'completed': return '已完成'
    case 'current': return '学习中'
    default: return '待学习'
  }
}
</script>

<template>
  <div class="space-y-6">
    <section class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <div class="flex flex-col xl:flex-row xl:items-start justify-between gap-5">
        <div class="flex items-start gap-4">
          <div class="w-16 h-16 bg-gray-100 border border-gray-200 rounded-2xl flex items-center justify-center text-sm font-bold text-gray-700">
            {{ course.icon }}
          </div>
          <div>
            <div class="flex items-center gap-3 flex-wrap">
              <h1 class="text-2xl font-bold text-gray-900">{{ course.name }}</h1>
              <span class="px-3 py-1 bg-gray-100 rounded-full text-sm font-medium text-gray-700">
                {{ course.progress }}%
              </span>
            </div>
            <p class="text-gray-500 mt-2 max-w-3xl">{{ course.description }}</p>
            <div class="flex items-center gap-2 mt-3 flex-wrap">
              <span :class="['px-3 py-1 rounded-full text-sm font-medium', getStatusClass(course.status)]">
                {{ getStatusLabel(course.status) }}
              </span>
              <span :class="['px-3 py-1 rounded-full text-sm font-medium', getDifficultyClass(course.difficulty)]">
                {{ course.difficulty }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3 flex-wrap">
          <button @click="emit('navigate', 'courses')" class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-all">
            返回课程
          </button>
          <button @click="emit('navigate', 'exercise')" class="px-5 py-2.5 bg-gray-900 hover:bg-black text-white rounded-xl font-medium transition-all shadow-sm">
            开始练习
          </button>
          <button @click="emit('navigate', 'analyze')" class="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-all">
            学习分析
          </button>
        </div>
      </div>

      <div class="mt-6">
        <div class="h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
          <div class="h-full bg-gray-900 rounded-full transition-all duration-500" :style="{ width: course.progress + '%' }"></div>
        </div>
        <div class="flex justify-between text-xs text-gray-500">
          <span>{{ course.completedHours }}h / {{ course.totalHours }}h</span>
          <span>总课时 {{ course.totalHours }} 小时</span>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-4 mt-6 pt-5 border-t border-gray-100">
        <div v-for="item in courseSummary" :key="item.label" class="text-center">
          <div class="text-2xl font-bold text-gray-900">{{ item.value }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ item.label }}</div>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <section class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div class="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-900">课程章节</h2>
            <p class="text-xs text-gray-400 mt-1">章节内可直接预览 PDF 并添加页面批注</p>
          </div>
          <span v-if="materials.length" class="px-3 py-1 rounded-full bg-gray-100 text-xs text-gray-600">{{ materials.length }} 份资料</span>
        </div>
        <div v-if="materialsLoading" class="py-8 text-center text-sm text-gray-400">正在加载章节资料…</div>
        <div v-else-if="materialsError" class="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-600">{{ materialsError }}</div>
        <div class="space-y-3">
          <article
            v-for="chapter in chapters"
            :key="chapter.id"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-transparent hover:border-gray-200 transition-colors"
          >
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center font-bold', getChapterStatusClass(chapter.status)]">
              {{ chapter.id.toString().split('-').pop() }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-900">{{ chapter.name }}</div>
              <div class="text-sm text-gray-500">{{ chapter.hours }} 小时 · {{ chapterStatusLabel(chapter) }}</div>
              <div v-if="chapter.topics?.length" class="flex flex-wrap gap-2 mt-2">
                <span v-for="topic in chapter.topics" :key="topic" class="text-xs px-2 py-1 bg-white border border-gray-200 rounded-full text-gray-500">
                  {{ topic }}
                </span>
              </div>
              <div v-if="chapterMaterials(chapter).length" class="flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-200">
                <button
                  v-for="material in chapterMaterials(chapter)"
                  :key="material.id"
                  class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 hover:border-gray-900 hover:text-gray-900 transition-colors"
                  @click="activeMaterial = material"
                >
                  <span class="font-extrabold text-[9px]">PDF</span>
                  <span>{{ material.name }}</span>
                  <small class="text-gray-400">{{ formatFileSize(material.size) }}</small>
                  <span>↗</span>
                </button>
              </div>
            </div>
          </article>

          <article v-if="supplementalMaterials.length" class="p-4 bg-gray-50 rounded-xl border border-dashed border-gray-200">
            <div class="font-medium text-gray-900">补充章节资料</div>
            <div class="text-xs text-gray-400 mt-1">尚未匹配到现有章节的课程 PDF</div>
            <div class="flex flex-wrap gap-2 mt-3">
              <button
                v-for="material in supplementalMaterials"
                :key="material.id"
                class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 hover:border-gray-900 transition-colors"
                @click="activeMaterial = material"
              >
                <span class="font-extrabold text-[9px]">PDF</span>
                <span>{{ material.name }}</span>
                <small class="text-gray-400">{{ formatFileSize(material.size) }}</small>
                <span>↗</span>
              </button>
            </div>
          </article>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">AI 练习</h2>
          <div class="bg-gray-50 rounded-xl p-5">
            <div class="font-bold text-lg text-gray-900">按《{{ course.name }}》实时生成</div>
            <p class="text-sm text-gray-500 mt-2">点击后会调用当前硅基流动模型生成对应课程的分层题目，生成失败时使用课程基础题兜底。</p>
            <button
              @click="emit('navigate', 'exercise')"
              class="w-full mt-5 py-3 bg-gray-900 text-white font-medium rounded-xl hover:bg-black transition-all"
            >
              开始练习
            </button>
          </div>
        </section>

        <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">错题本</h2>
          <div class="bg-red-50 rounded-xl p-5">
            <div class="font-bold text-lg text-gray-900">复习错题，巩固薄弱</div>
            <p class="text-sm text-gray-500 mt-2">查看做错的题目，重做并标记掌握，系统会根据薄弱点生成针对性练习。</p>
            <button
              @click="emit('navigate', 'mistakes')"
              class="w-full mt-5 py-3 bg-red-600 text-white font-medium rounded-xl hover:bg-red-700 transition-all"
            >
              进入错题本
            </button>
          </div>
        </section>

        <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">学习建议</h2>
          <ul class="space-y-3">
            <li v-for="item in suggestions" :key="item" class="flex gap-2 text-sm text-gray-600">
              <span class="mt-1 h-1.5 w-1.5 rounded-full bg-gray-400"></span>
              <span>{{ item }}</span>
            </li>
          </ul>
        </section>

        <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h2 class="text-xl font-bold text-gray-900 mb-4">课程目标</h2>
          <ul class="space-y-3">
            <li v-for="item in goals" :key="item" class="text-sm text-gray-600 leading-relaxed">
              {{ item }}
            </li>
          </ul>
        </section>
      </aside>
    </div>

    <CoursePdfReader
      v-if="activeMaterial"
      :material="activeMaterial"
      :course="course.name"
      :user-id="userId"
      @close="activeMaterial = null"
    />
  </div>
</template>
