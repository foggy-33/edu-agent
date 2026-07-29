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
const completedCount = computed(() => courses.value.filter(course => course.status === 'completed').length)
const inProgressCount = computed(() => courses.value.filter(course => course.status === 'in-progress').length)
const averageProgress = computed(() => {
  if (!courses.value.length) return 0
  return Math.round(courses.value.reduce((sum, course) => sum + course.progress, 0) / courses.value.length)
})
const resumeCourse = computed(() =>
  courses.value.find(course => course.status === 'in-progress') || courses.value[0]
)

const courseIconPaths: Record<string, string[]> = {
  database_system: ['M4 5.5C4 3.57 7.58 2 12 2s8 1.57 8 3.5S16.42 9 12 9 4 7.43 4 5.5Z', 'M4 5.5v6C4 13.43 7.58 15 12 15s8-1.57 8-3.5v-6', 'M4 11.5v6C4 19.43 7.58 21 12 21s8-1.57 8-3.5v-6'],
  data_structure: ['M5 4h5v5H5z', 'M14 4h5v5h-5z', 'M9.5 15h5v5h-5z', 'M7.5 9v3h9V9', 'M12 12v3'],
  algorithm_design: ['M6 3v4', 'M4 5h4', 'M16 17v4', 'M14 19h4', 'M8 5h4a5 5 0 0 1 5 5v4a5 5 0 0 0 5 5'],
  operating_system: ['M5 5h14v11H5z', 'M9 20h6', 'M12 16v4', 'M8 9h3v3H8z', 'M13 9h3v3h-3z'],
  computer_network: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z', 'M3 12h18', 'M12 3c2.2 2.46 3.4 5.46 3.4 9s-1.2 6.54-3.4 9c-2.2-2.46-3.4-5.46-3.4-9S9.8 5.46 12 3Z'],
}

function currentChapter(course: Course) {
  return course.chapters?.find(chapter => chapter.status === 'current') || course.chapters?.[0]
}

function focusTopics(course: Course) {
  return currentChapter(course)?.topics?.slice(0, 3) || []
}

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
        <span class="page-eyebrow"><i></i> LEARNING SPACE</span>
        <h1>课程</h1>
        <p>查看课程进度，继续学习或生成针对性练习。</p>
      </div>
      <button v-if="resumeCourse" type="button" class="resume-card" @click="openCourseDetail(resumeCourse)">
        <span class="resume-copy">
          <small>继续上次学习</small>
          <strong>{{ resumeCourse.name }}</strong>
          <em>{{ currentChapter(resumeCourse)?.name || '进入课程' }}</em>
        </span>
        <span class="resume-progress" :style="{ '--progress': `${resumeCourse.progress * 3.6}deg` }">
          <b>{{ resumeCourse.progress }}%</b>
        </span>
        <span class="resume-arrow">→</span>
      </button>
    </header>

    <div class="course-stats">
      <div class="stat-item stat-total">
        <span class="stat-icon"><svg viewBox="0 0 24 24"><path d="M4 5.5 12 3l8 2.5L12 8 4 5.5Zm2 3v6.7c2.9 2.1 9.1 2.1 12 0V8.5M20 6v7" /></svg></span>
        <div><span>课程总数</span><strong>{{ courses.length }}<small>门</small></strong><em>覆盖核心专业课程</em></div>
      </div>
      <div class="stat-item stat-complete">
        <span class="stat-icon"><svg viewBox="0 0 24 24"><path d="M5 12.5 9.2 17 19 7" /><circle cx="12" cy="12" r="9" /></svg></span>
        <div><span>已完成</span><strong>{{ completedCount }}<small>门</small></strong><em>保持稳定学习节奏</em></div>
      </div>
      <div class="stat-item stat-active">
        <span class="stat-icon"><svg viewBox="0 0 24 24"><path d="M5 19V9m7 10V5m7 14v-7" /><path d="m4 6 5-3 4 3 7-4" /></svg></span>
        <div><span>进行中</span><strong>{{ inProgressCount }}<small>门</small></strong><em>平均进度 {{ averageProgress }}%</em></div>
      </div>
      <div class="stat-item stat-hours">
        <span class="stat-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" /></svg></span>
        <div><span>已学时长</span><strong>{{ totalHours }}<small>小时</small></strong><em>持续积累学习投入</em></div>
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
          <span class="card-glow"></span>
          <div class="course-card-head">
            <div class="course-monogram">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path v-for="path in (courseIconPaths[String(course.id)] || courseIconPaths.database_system)" :key="path" :d="path" />
              </svg>
            </div>
            <span :class="['status-chip', `status-${course.status}`]">
              {{ getStatusLabel(course.status) }}
            </span>
          </div>

          <h3>{{ course.name }}</h3>
          <p class="course-description">{{ course.description }}</p>

          <div v-if="focusTopics(course).length" class="focus-block">
            <span class="focus-label">当前重点</span>
            <div class="focus-tags">
              <span v-for="topic in focusTopics(course)" :key="topic">{{ topic }}</span>
            </div>
          </div>

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
          <div class="course-action">
            <span>{{ course.status === 'completed' ? '查看课程' : '继续学习' }}</span>
            <i>→</i>
          </div>
        </button>
      </div>
      <div v-else class="course-state">当前筛选下暂无课程</div>
    </section>
  </div>
</template>

<style scoped>
.course-page { width: min(1240px, 100%); margin: 0 auto; color: #202123; }
.course-page-header { position: relative; display: flex; align-items: center; justify-content: space-between; gap: 30px; min-height: 150px; padding: 24px 28px; overflow: hidden; border: 1px solid #e6e3f5; border-radius: 24px; background: linear-gradient(118deg, #fff 0%, #faf9ff 58%, #f2f0ff 100%); box-shadow: 0 14px 42px rgba(38, 30, 84, .06); }
.course-page-header::after { content: ''; position: absolute; top: -110px; right: 22%; width: 260px; height: 260px; border: 1px solid rgba(109,93,231,.12); border-radius: 50%; box-shadow: 0 0 0 36px rgba(109,93,231,.025), 0 0 0 72px rgba(109,93,231,.018); pointer-events: none; }
.page-eyebrow { display: flex; align-items: center; gap: 7px; margin-bottom: 10px; color: #6d5de7; font-size: 10px; font-weight: 760; letter-spacing: .14em; }
.page-eyebrow i { width: 18px; height: 1px; background: #6d5de7; }
.course-page-header h1 { margin: 0 0 8px; font-size: 34px; font-weight: 680; letter-spacing: -.045em; }
.course-page-header p { margin: 0; color: #6e6e80; font-size: 13px; }
.resume-card { z-index: 1; display: flex; align-items: center; gap: 15px; min-width: 330px; padding: 14px 14px 14px 18px; border: 1px solid rgba(109,93,231,.16); border-radius: 18px; color: #202123; background: rgba(255,255,255,.76); text-align: left; box-shadow: 0 10px 32px rgba(58,45,129,.08); backdrop-filter: blur(10px); transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
.resume-card:hover { border-color: rgba(109,93,231,.34); transform: translateY(-2px); box-shadow: 0 16px 40px rgba(58,45,129,.13); }
.resume-copy { display: flex; flex: 1; flex-direction: column; min-width: 0; }
.resume-copy small { color: #858592; font-size: 10px; }
.resume-copy strong { margin-top: 4px; overflow: hidden; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.resume-copy em { margin-top: 3px; overflow: hidden; color: #6d5de7; font-size: 10px; font-style: normal; text-overflow: ellipsis; white-space: nowrap; }
.resume-progress { display: grid; place-items: center; width: 50px; height: 50px; border-radius: 50%; background: conic-gradient(#6d5de7 var(--progress), #eceaf7 0); }
.resume-progress::before { content: ''; grid-area: 1/1; width: 40px; height: 40px; border-radius: 50%; background: #fff; }
.resume-progress b { z-index: 1; grid-area: 1/1; font-size: 10px; }
.resume-arrow { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; color: #fff; background: #202123; transition: transform .25s ease; }
.resume-card:hover .resume-arrow { transform: translateX(2px); }
.course-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0 38px; }
.stat-item { display: flex; align-items: center; gap: 14px; min-height: 106px; padding: 18px; border: 1px solid #e8e8ec; border-radius: 18px; background: #fff; box-shadow: 0 8px 25px rgba(24,24,27,.035); animation: course-rise .45s both; transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease; }
.stat-item:nth-child(2) { animation-delay: .05s; }
.stat-item:nth-child(3) { animation-delay: .1s; }
.stat-item:nth-child(4) { animation-delay: .15s; }
.stat-item:hover { border-color: #d8d4f4; transform: translateY(-2px); box-shadow: 0 12px 30px rgba(45,38,82,.07); }
.stat-icon { display: grid; place-items: center; width: 42px; height: 42px; flex: 0 0 auto; border-radius: 13px; color: #6254ce; background: #f2f0ff; }
.stat-icon svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
.stat-item > div { display: grid; grid-template-columns: auto auto; align-items: baseline; column-gap: 5px; }
.stat-item div > span { grid-column: 1/-1; color: #777785; font-size: 11px; }
.stat-item strong { color: #202123; font-size: 27px; font-weight: 680; letter-spacing: -.04em; }
.stat-item strong small { margin-left: 4px; color: #9696a1; font-size: 10px; font-weight: 500; }
.stat-item em { grid-column: 1/-1; margin-top: 2px; color: #aaa9b3; font-size: 9px; font-style: normal; }
.courses-section { padding: 0; }
.courses-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 18px; }
.courses-toolbar h2 { margin: 0 0 5px; font-size: 22px; font-weight: 670; letter-spacing: -.025em; }
.courses-toolbar p { margin: 0; color: #858592; font-size: 12px; }
.course-filters { display: flex; flex-wrap: wrap; gap: 6px; padding: 4px; border: 1px solid #ededf0; border-radius: 999px; background: #f7f7f8; }
.course-filters button { min-height: 32px; padding: 6px 14px; border: 0; border-radius: 999px; color: #666674; background: transparent; font-size: 11px; font-weight: 620; transition: color .2s ease, background .2s ease, transform .2s ease; }
.course-filters button:hover { color: #202123; background: #fff; }
.course-filters button.active { color: #fff; background: #202123; box-shadow: 0 5px 14px rgba(0,0,0,.15); }
.course-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.course-card { position: relative; display: flex; flex-direction: column; min-height: 390px; padding: 22px; overflow: hidden; border: 1px solid #e7e7eb; border-radius: 20px; color: #202123; background: linear-gradient(150deg, #fff 60%, #fbfaff 100%); text-align: left; box-shadow: 0 8px 28px rgba(31,31,35,.035); animation: course-rise .5s both; transition: transform .28s cubic-bezier(.2,.8,.2,1), border-color .28s ease, box-shadow .28s ease; }
.course-card:nth-child(2) { animation-delay: .06s; }
.course-card:nth-child(3) { animation-delay: .12s; }
.course-card:nth-child(4) { animation-delay: .18s; }
.course-card:nth-child(5) { animation-delay: .24s; }
.course-card::before { content: ''; position: absolute; inset: 0 auto 0 0; width: 3px; background: linear-gradient(180deg, #6d5de7, rgba(109,93,231,0)); opacity: 0; transition: opacity .25s ease; }
.card-glow { position: absolute; top: -90px; right: -80px; width: 190px; height: 190px; border-radius: 50%; background: radial-gradient(circle, rgba(109,93,231,.11), transparent 67%); opacity: .45; transition: opacity .25s ease, transform .4s ease; }
.course-card:hover { border-color: #d4cff2; transform: translateY(-5px); box-shadow: 0 18px 44px rgba(41,33,86,.105); }
.course-card:hover::before { opacity: 1; }
.course-card:hover .card-glow { opacity: 1; transform: scale(1.15); }
.course-card-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.course-monogram { display: grid; place-items: center; width: 48px; height: 48px; border: 1px solid #ddd9f3; border-radius: 15px; color: #5548bc; background: #f3f1ff; }
.course-monogram svg { width: 24px; height: 24px; fill: none; stroke: currentColor; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
.status-chip { padding: 5px 9px; border: 1px solid #e2dff3; border-radius: 999px; color: #6254ce; background: #f5f3ff; font-size: 10px; font-weight: 650; }
.status-completed { color: #202123; border-color: #dfdfe2; background: #f1f1f2; }
.status-not-started { color: #8a8a96; border-color: #e7e7e9; background: #fff; }
.course-card h3 { position: relative; margin: 0; font-size: 18px; font-weight: 670; letter-spacing: -.015em; }
.course-description { position: relative; min-height: 48px; margin: 9px 0 0; overflow: hidden; color: #6e6e80; font-size: 12px; line-height: 1.7; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.focus-block { position: relative; margin-top: 15px; padding: 12px; border: 1px solid #efedf8; border-radius: 13px; background: rgba(248,247,253,.82); }
.focus-label { display: block; margin-bottom: 8px; color: #8a849e; font-size: 9px; font-weight: 650; letter-spacing: .08em; }
.focus-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.focus-tags span { padding: 4px 7px; border: 1px solid #e4e1f3; border-radius: 999px; color: #5f5875; background: #fff; font-size: 9px; }
.course-meta { position: relative; display: flex; align-items: center; gap: 8px; margin-top: 13px; }
.course-meta span { padding: 3px 7px; border-radius: 6px; color: #555563; background: #f1f1f2; font-size: 10px; }
.course-meta small { color: #92929e; font-size: 10px; }
.course-progress { position: relative; margin-top: auto; padding-top: 20px; }
.progress-label,.progress-foot { display: flex; align-items: center; justify-content: space-between; }
.progress-label { margin-bottom: 8px; color: #666674; font-size: 11px; }
.progress-label strong { color: #4f43b1; font-size: 11px; }
.progress-track { height: 6px; overflow: hidden; border-radius: 999px; background: #e9e8ef; }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #202123 0%, #6d5de7 100%); transition: width .65s cubic-bezier(.2,.8,.2,1); }
.progress-foot { margin-top: 8px; color: #92929e; font-size: 10px; }
.course-action { position: relative; display: flex; align-items: center; justify-content: space-between; margin-top: 17px; padding-top: 14px; border-top: 1px solid #ededf0; color: #35323f; font-size: 11px; font-weight: 650; }
.course-action i { display: grid; place-items: center; width: 27px; height: 27px; border-radius: 50%; color: #fff; background: #202123; font-style: normal; transition: transform .22s ease, background .22s ease; }
.course-card:hover .course-action i { background: #6d5de7; transform: translateX(3px); }
.course-state { display: grid; place-items: center; min-height: 280px; border: 1px solid #ededf0; border-radius: 18px; color: #777785; background: #fafafa; font-size: 13px; }
.course-error { color: #7f1d1d; background: #faf3f3; }
@keyframes course-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 1060px) { .course-page-header { align-items: flex-start; flex-direction: column; } .resume-card { width: 100%; min-width: 0; } .course-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .course-stats { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .course-page-header { padding: 22px; border-radius: 20px; } .course-page-header h1 { font-size: 28px; } .resume-progress { width: 46px; height: 46px; } .course-stats { grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; } .stat-item { align-items: flex-start; flex-direction: column; min-height: 122px; padding: 14px; } .stat-icon { width: 36px; height: 36px; } .courses-toolbar { align-items: stretch; flex-direction: column; } .course-filters { width: max-content; max-width: 100%; } .course-grid { grid-template-columns: 1fr; } .course-card { min-height: 380px; } }
@media (prefers-reduced-motion: reduce) { .course-card,.card-glow,.resume-card,.resume-arrow,.stat-item,.progress-track i { animation: none; transition: none; } }
</style>
