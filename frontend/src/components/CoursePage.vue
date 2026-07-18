<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getCourses } from '../api/client'
import type { Course } from '../types'

const emit = defineEmits<{
  navigate: [page: 'detail' | 'exercise', course?: Course]
}>()

const courses = ref<Course[]>([])
const loading = ref(false)
const error = ref('')
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: '全部' },
  { key: 'in-progress', label: '进行中' },
  { key: 'completed', label: '已完成' },
  { key: 'not-started', label: '未开始' },
]

const filteredCourses = computed(() =>
  courses.value.filter(course => activeFilter.value === 'all' || course.status === activeFilter.value)
)

const totalHours = computed(() => courses.value.reduce((sum, course) => sum + course.completedHours, 0))

async function loadCourses() {
  loading.value = true
  error.value = ''
  try {
    courses.value = (await getCourses()).courses
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '课程数据加载失败'
  } finally {
    loading.value = false
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

function openCourseDetail(course: Course) {
  emit('navigate', 'detail', course)
}

onMounted(loadCourses)
</script>

<template>
  <div class="course-page">
    <header class="course-page-header">
      <div>
        <h1>课程</h1>
        <p>查看课程进度，继续学习或生成针对性练习。</p>
      </div>
    </header>

    <div class="course-stats">
      <div class="stat-item">
        <span>课程总数</span>
        <strong>{{ courses.length }}</strong>
        <small>门课程</small>
      </div>
      <div class="stat-item">
        <span>已完成</span>
        <strong>{{ courses.filter(c => c.status === 'completed').length }}</strong>
        <small>门课程</small>
      </div>
      <div class="stat-item">
        <span>进行中</span>
        <strong>{{ courses.filter(c => c.status === 'in-progress').length }}</strong>
        <small>门课程</small>
      </div>
      <div class="stat-item">
        <span>已学时长</span>
        <strong>{{ totalHours }}</strong>
        <small>小时</small>
      </div>
    </div>

    <section class="courses-section">
      <div class="courses-toolbar">
        <div>
          <h2>我的课程</h2>
          <p>课程数据来自课程目录，练习题可按课程实时生成。</p>
        </div>
        <div class="course-filters" role="tablist" aria-label="课程状态筛选">
          <button
            v-for="filter in filters"
            :key="filter.key"
            @click="activeFilter = filter.key"
            :class="{ active: activeFilter === filter.key }"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="course-state">正在加载课程...</div>
      <div v-else-if="error" class="course-state course-error">{{ error }}</div>
      <div v-else-if="filteredCourses.length" class="course-grid">
        <button
          v-for="course in filteredCourses"
          :key="course.id"
          type="button"
          @click="openCourseDetail(course)"
          class="course-card"
        >
          <div class="course-card-head">
            <div class="course-monogram">
              {{ course.icon }}
            </div>
            <span :class="['status-chip', `status-${course.status}`]">
              {{ getStatusLabel(course.status) }}
            </span>
          </div>

          <h3>{{ course.name }}</h3>
          <p class="course-description">{{ course.description }}</p>

          <div class="course-meta">
            <span>{{ course.difficulty }}</span>
            <small>{{ course.lastAccess }}</small>
          </div>

          <div class="course-progress">
            <div class="progress-label">
              <span>学习进度</span>
              <strong>{{ course.progress }}%</strong>
            </div>
            <div class="progress-track">
              <i :style="{ width: course.progress + '%' }"></i>
            </div>
            <div class="progress-foot">
              <span>{{ course.completedHours }} / {{ course.totalHours }} 小时</span>
              <span>{{ course.questions.length }} 道基础题</span>
            </div>
          </div>
        </button>
      </div>
      <div v-else class="course-state">当前筛选下暂无课程</div>
    </section>
  </div>
</template>

<style scoped>
.course-page { width: min(1120px, 100%); margin: 0 auto; color: #202123; }
.course-page-header { display: flex; align-items: center; justify-content: space-between; padding: 2px 0 18px; border-bottom: 1px solid #ececec; }
.course-page-header h1 { margin: 0 0 7px; font-size: 30px; font-weight: 650; letter-spacing: -.035em; }
.course-page-header p { margin: 0; color: #6e6e80; font-size: 13px; }
.course-stats { display: grid; grid-template-columns: repeat(4, 1fr); margin: 24px 0 32px; border: 1px solid #e6e6e8; border-radius: 14px; overflow: hidden; }
.stat-item { position: relative; display: grid; grid-template-columns: auto 1fr; align-items: baseline; gap: 2px 6px; min-height: 108px; padding: 22px 24px; border-right: 1px solid #ececee; background: #fff; }
.stat-item:last-child { border-right: 0; }
.stat-item span { grid-column: 1 / -1; color: #777785; font-size: 12px; }
.stat-item strong { color: #202123; font-size: 30px; font-weight: 650; letter-spacing: -.04em; }
.stat-item small { color: #9696a1; font-size: 11px; }
.courses-section { padding: 0; }
.courses-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.courses-toolbar h2 { margin: 0 0 5px; font-size: 20px; font-weight: 650; letter-spacing: -.02em; }
.courses-toolbar p { margin: 0; color: #858592; font-size: 12px; }
.course-filters { display: flex; flex-wrap: wrap; gap: 6px; }
.course-filters button { min-height: 34px; padding: 7px 13px; border: 1px solid transparent; border-radius: 999px; color: #666674; background: #f5f5f6; font-size: 12px; font-weight: 600; }
.course-filters button:hover { color: #202123; background: #ececee; }
.course-filters button.active { color: #fff; background: #202123; }
.course-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-top: 1px solid #ececee; border-left: 1px solid #ececee; }
.course-card { display: flex; flex-direction: column; min-height: 342px; padding: 22px; border: 0; border-right: 1px solid #ececee; border-bottom: 1px solid #ececee; color: #202123; background: #fff; text-align: left; transition: background .15s ease; }
.course-card:hover { background: #fafafa; }
.course-card-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 22px; }
.course-monogram { display: grid; place-items: center; width: 42px; height: 42px; border: 1px solid #dedee2; border-radius: 11px; color: #444654; background: #f7f7f8; font-size: 11px; font-weight: 750; }
.status-chip { padding: 4px 8px; border: 1px solid #e1e1e4; border-radius: 999px; color: #6e6e80; background: #f7f7f8; font-size: 10px; font-weight: 600; }
.status-completed { color: #202123; background: #ececee; }
.status-not-started { color: #8a8a96; background: #fff; }
.course-card h3 { margin: 0; font-size: 16px; font-weight: 650; }
.course-description { min-height: 46px; margin: 8px 0 0; overflow: hidden; color: #6e6e80; font-size: 12px; line-height: 1.65; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.course-meta { display: flex; align-items: center; gap: 8px; margin-top: 16px; }
.course-meta span { padding: 3px 7px; border-radius: 6px; color: #555563; background: #f1f1f2; font-size: 10px; }
.course-meta small { color: #92929e; font-size: 10px; }
.course-progress { margin-top: auto; padding-top: 22px; }
.progress-label,.progress-foot { display: flex; align-items: center; justify-content: space-between; }
.progress-label { margin-bottom: 8px; color: #666674; font-size: 11px; }
.progress-label strong { color: #202123; font-size: 11px; }
.progress-track { height: 5px; overflow: hidden; border-radius: 999px; background: #e7e7ea; }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: #202123; transition: width .4s ease; }
.progress-foot { margin-top: 8px; color: #92929e; font-size: 10px; }
.course-state { display: grid; place-items: center; min-height: 280px; border-radius: 14px; color: #777785; background: #fafafa; font-size: 13px; }
.course-error { color: #7f1d1d; background: #faf3f3; }
@media (max-width: 960px) { .course-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .course-stats { grid-template-columns: repeat(2, 1fr); } .stat-item:nth-child(2) { border-right: 0; } .stat-item:nth-child(-n+2) { border-bottom: 1px solid #ececee; } }
@media (max-width: 640px) { .course-page-header h1 { font-size: 26px; } .course-stats { grid-template-columns: 1fr 1fr; margin-top: 20px; } .stat-item { min-height: 94px; padding: 17px; } .courses-toolbar { align-items: stretch; flex-direction: column; } .course-grid { grid-template-columns: 1fr; } .course-card { min-height: 320px; } }
</style>
