<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  navigate: [page: 'generate' | 'courses']
}>()

const courses = ref([
  { id: '1', name: '数据库系统', icon: '🗄️' },
  { id: '2', name: '数据结构', icon: '📊' },
  { id: '3', name: '算法设计', icon: '🧮' },
  { id: '4', name: '操作系统', icon: '💻' },
])

const resourceTypes = ref([
  { id: 'all', name: '全部类型', icon: '📁' },
  { id: 'document', name: '文档', icon: '📄' },
  { id: 'mindmap', name: '思维导图', icon: '🧠' },
  { id: 'quiz', name: '题库', icon: '📝' },
  { id: 'video', name: '视频', icon: '🎬' },
  { id: 'practice', name: '实践案例', icon: '💡' },
])

const selectedCourse = ref('all')
const selectedType = ref('all')
const searchQuery = ref('')

const resources = ref([
  { id: '1', courseId: '1', type: 'document', name: '关系模型与SQL基础详解', size: '2.3 MB', date: '2024-01-15', source: '生成' },
  { id: '2', courseId: '1', type: 'mindmap', name: '数据库系统知识结构', size: '1.1 MB', date: '2024-01-14', source: '生成' },
  { id: '3', courseId: '1', type: 'quiz', name: '关系代数练习题集', size: '512 KB', date: '2024-01-13', source: '生成' },
  { id: '4', courseId: '2', type: 'document', name: '链表与树结构总结', size: '1.8 MB', date: '2024-01-12', source: '上传' },
  { id: '5', courseId: '2', type: 'video', name: '快速排序算法演示', size: '45 MB', date: '2024-01-11', source: '上传' },
  { id: '6', courseId: '3', type: 'practice', name: '动态规划实战案例', size: '890 KB', date: '2024-01-10', source: '生成' },
  { id: '7', courseId: '3', type: 'document', name: '图算法入门指南', size: '3.2 MB', date: '2024-01-09', source: '上传' },
  { id: '8', courseId: '4', type: 'mindmap', name: '进程管理知识图谱', size: '956 KB', date: '2024-01-08', source: '生成' },
])

const filteredResources = computed(() => {
  return resources.value.filter(r => {
    const matchCourse = selectedCourse.value === 'all' || r.courseId === selectedCourse.value
    const matchType = selectedType.value === 'all' || r.type === selectedType.value
    const matchSearch = searchQuery.value === '' || 
      r.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchCourse && matchType && matchSearch
  })
})

const getCourseName = (courseId: string) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? course.name : '未知课程'
}

const getTypeName = (typeId: string) => {
  const type = resourceTypes.value.find(t => t.id === typeId)
  return type ? type.name : '未知类型'
}

const getTypeIcon = (typeId: string) => {
  const type = resourceTypes.value.find(t => t.id === typeId)
  return type ? type.icon : '📄'
}
</script>

<template>
  <div class="resource-library">
    <div class="library-header">
      <div>
        <span class="section-kicker">学习资源</span>
        <h1>资源库</h1>
      </div>
      <div class="header-actions">
        <button class="generate-btn" @click="emit('navigate', 'generate')">
          <span>✨</span>
          <span>生成资料</span>
        </button>
        <button class="upload-btn" @click="emit('navigate', 'courses')">
          <span>📤</span>
          <span>上传资料</span>
        </button>
      </div>
    </div>

    <div class="library-filters">
      <div class="filter-group">
        <label>课程分类</label>
        <div class="filter-tags">
          <button
            :class="['filter-tag', selectedCourse === 'all' ? 'active' : '']"
            @click="selectedCourse = 'all'"
          >
            📚 全部课程
          </button>
          <button
            v-for="course in courses"
            :key="course.id"
            :class="['filter-tag', selectedCourse === course.id ? 'active' : '']"
            @click="selectedCourse = course.id"
          >
            {{ course.icon }} {{ course.name }}
          </button>
        </div>
      </div>

      <div class="filter-group">
        <label>资料类型</label>
        <div class="filter-tags">
          <button
            v-for="type in resourceTypes"
            :key="type.id"
            :class="['filter-tag', selectedType === type.id ? 'active' : '']"
            @click="selectedType = type.id"
          >
            {{ type.icon }} {{ type.name }}
          </button>
        </div>
      </div>
    </div>

    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索资源..."
        class="search-input"
      />
      <span class="search-icon">🔍</span>
    </div>

    <div class="resources-grid">
      <div
        v-for="resource in filteredResources"
        :key="resource.id"
        class="resource-card"
      >
        <div class="resource-icon">
          {{ getTypeIcon(resource.type) }}
        </div>
        <div class="resource-info">
          <h3 class="resource-name">{{ resource.name }}</h3>
          <div class="resource-meta">
            <span class="meta-item">{{ getCourseName(resource.courseId) }}</span>
            <span class="meta-divider">•</span>
            <span class="meta-item">{{ getTypeName(resource.type) }}</span>
          </div>
          <div class="resource-details">
            <span>{{ resource.size }}</span>
            <span>{{ resource.date }}</span>
            <span :class="['source-tag', resource.source === '生成' ? 'generated' : 'uploaded']">
              {{ resource.source }}
            </span>
          </div>
        </div>
        <div class="resource-actions">
          <button class="action-btn" title="预览">👁️</button>
          <button class="action-btn" title="下载">⬇️</button>
          <button class="action-btn" title="分享">🔗</button>
        </div>
      </div>
    </div>

    <div v-if="filteredResources.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无匹配的资源</p>
      <p class="empty-hint">尝试调整筛选条件或上传新资源</p>
    </div>
  </div>
</template>
