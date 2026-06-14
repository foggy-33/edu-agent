<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
  className?: string
}>()

const htmlContent = ref('')

async function renderMarkdown() {
  if (!props.content) {
    htmlContent.value = ''
    return
  }
  marked.setOptions({
    breaks: true,
    gfm: true
  })
  htmlContent.value = await marked.parse(props.content) as string
}

onMounted(() => {
  renderMarkdown()
})

watch(() => props.content, () => {
  renderMarkdown()
})

const containerClass = computed(() => {
  return props.className || ''
})
</script>

<template>
  <div
    class="markdown-body"
    :class="containerClass"
    v-html="htmlContent"
  ></div>
</template>

<style scoped>
.markdown-body {
  line-height: 1.7;
  color: #374151;
}

.markdown-body :deep(h1) {
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
  margin: 1.5rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.markdown-body :deep(h2) {
  font-size: 1.375rem;
  font-weight: 600;
  color: #1f2937;
  margin: 1.25rem 0 0.75rem;
  padding-left: 0.75rem;
  border-left: 4px solid #6366f1;
}

.markdown-body :deep(h3) {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin: 1rem 0 0.5rem;
}

.markdown-body :deep(p) {
  margin: 0.75rem 0;
}

.markdown-body :deep(strong) {
  color: #111827;
  font-weight: 600;
}

.markdown-body :deep(em) {
  color: #6b7280;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5rem;
  margin: 0.75rem 0;
}

.markdown-body :deep(li) {
  margin: 0.375rem 0;
  line-height: 1.7;
}

.markdown-body :deep(ul li) {
  list-style-type: disc;
}

.markdown-body :deep(ol li) {
  list-style-type: decimal;
}

.markdown-body :deep(code) {
  background: #f3f4f6;
  color: #dc2626;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.markdown-body :deep(pre) {
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
  color: #e5e7eb;
  padding: 1rem 1.25rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  margin: 1rem 0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.markdown-body :deep(pre code) {
  background: transparent;
  color: #e5e7eb;
  padding: 0;
  font-size: 0.875rem;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #6366f1;
  background: linear-gradient(90deg, #eef2ff 0%, transparent 100%);
  padding: 0.75rem 1rem;
  margin: 1rem 0;
  border-radius: 0 0.5rem 0.5rem 0;
  color: #4b5563;
}

.markdown-body :deep(blockquote p) {
  margin: 0;
}

.markdown-body :deep(a) {
  color: #6366f1;
  text-decoration: none;
  border-bottom: 1px dashed #6366f1;
  transition: all 0.2s;
}

.markdown-body :deep(a:hover) {
  color: #4f46e5;
  border-bottom-style: solid;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.markdown-body :deep(th) {
  background: #f9fafb;
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.markdown-body :deep(td) {
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
}

.markdown-body :deep(tr:hover td) {
  background: #f9fafb;
}

.markdown-body :deep(hr) {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, #e5e7eb 50%, transparent 100%);
  margin: 1.5rem 0;
}
</style>
