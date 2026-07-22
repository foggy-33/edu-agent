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
  navigate: [page: 'courses' | 'exercise' | 'analyze' | 'mistakes', chapterId?: string]
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
  const chapterNumber = Number(String(chapter.id).split('-').pop())
  const chapterName = chapter.name.toLowerCase()
  return materials.value.filter((material) => {
    if (material.chapter != null) return material.chapter === chapterNumber
    const name = material.name.toLowerCase()
    if (name.includes('绪论')) return chapterName.includes('导论') || chapterName.includes('绪论')
    if (name.includes('关系模型')) return chapterName.includes('关系模型')
    if (name.includes('sql')) return chapterName.includes('sql')
    if (name.includes('安全')) return chapterName.includes('安全')
    return false
  })
}

function chapterMaterial(chapter: CourseChapter) {
  return chapterMaterials(chapter)[0] || null
}

function openChapterMaterial(chapter: CourseChapter) {
  const material = chapterMaterial(chapter)
  if (material) activeMaterial.value = material
}

function openMaterial(material: CoursePdfMaterial) {
  activeMaterial.value = material
}

function materialTitle(material: CoursePdfMaterial) {
  return material.name.replace(/^\d+\s*/, '').replace(/-\d+$/, '').trim() || '补充章节'
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
            <p class="text-xs text-gray-400 mt-1">点击章节可阅读资料，也可按章节生成 AI 练习</p>
          </div>
          <span v-if="materials.length" class="px-3 py-1 rounded-full bg-gray-100 text-xs text-gray-600">{{ materials.length }} 份资料</span>
        </div>
        <div v-if="materialsLoading" class="py-8 text-center text-sm text-gray-400">正在加载章节资料…</div>
        <div v-else-if="materialsError" class="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-600">{{ materialsError }}</div>
        <div class="space-y-3">
          <article
            v-for="chapter in chapters"
            :key="chapter.id"
            :class="[
              'flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-transparent transition-all',
              chapterMaterial(chapter) ? 'cursor-pointer hover:border-gray-300 hover:bg-white hover:shadow-sm' : ''
            ]"
            :role="chapterMaterial(chapter) ? 'button' : undefined"
            :tabindex="chapterMaterial(chapter) ? 0 : undefined"
            @click="openChapterMaterial(chapter)"
            @keydown.enter="openChapterMaterial(chapter)"
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
              <div v-if="chapterMaterials(chapter).length > 1" class="flex flex-wrap gap-2 mt-3" @click.stop>
                <button
                  v-for="(material, materialIndex) in chapterMaterials(chapter)"
                  :key="material.id"
                  type="button"
                  class="h-8 px-3 rounded-full border border-gray-200 bg-white text-xs font-medium text-gray-600 hover:border-violet-300 hover:text-violet-700 transition-colors"
                  @click="openMaterial(material)"
                >
                  课件 {{ materialIndex + 1 }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                type="button"
                class="h-9 px-4 rounded-full bg-gray-900 text-white text-xs font-medium hover:bg-black transition-colors"
                @click.stop="emit('navigate', 'exercise', String(chapter.id))"
              >
                AI 练习
              </button>
              <span v-if="chapterMaterial(chapter)" class="w-9 h-9 rounded-full border border-gray-200 bg-white grid place-items-center text-gray-500">→</span>
            </div>
          </article>

          <article
            v-for="material in supplementalMaterials"
            :key="material.id"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-dashed border-gray-200 cursor-pointer hover:border-gray-400 hover:bg-white hover:shadow-sm transition-all"
            role="button"
            tabindex="0"
            @click="activeMaterial = material"
            @keydown.enter="activeMaterial = material"
          >
            <div class="w-10 h-10 shrink-0 rounded-xl border border-gray-200 bg-white grid place-items-center text-xs font-bold text-gray-500">＋</div>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-900">{{ materialTitle(material) }}</div>
              <div class="text-sm text-gray-500 mt-1">补充章节 · 点击进入学习</div>
            </div>
            <span class="w-9 h-9 shrink-0 rounded-full border border-gray-200 bg-white grid place-items-center text-gray-500">→</span>
          </article>
        </div>
      </section>

      <aside class="space-y-6">
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
