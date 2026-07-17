<script setup lang="ts">
import { computed, ref } from 'vue'
import { testSiliconFlow } from '../api/client'
import { loadSiliconFlowConfig, saveSiliconFlowConfig } from '../api/settings'

type ModelKind = '全部' | '对话' | '推理' | '编程' | '视觉' | '生图'

interface SiliconFlowModel {
  id: string
  provider: string
  title: string
  description: string
  tags: string[]
  kind: Exclude<ModelKind, '全部'>[]
  hot?: boolean
}

const modelCatalog: SiliconFlowModel[] = [
  {
    id: 'deepseek-ai/DeepSeek-V4-Pro',
    provider: 'DeepSeek',
    title: 'DeepSeek-V4-Pro',
    description: '适合复杂推理、长上下文问答和多任务协作。',
    tags: ['对话', '工具', '长文本', '推理'],
    kind: ['对话', '推理'],
    hot: true,
  },
  {
    id: 'deepseek-ai/DeepSeek-V4-Flash',
    provider: 'DeepSeek',
    title: 'DeepSeek-V4-Flash',
    description: '轻量高速模型，适合低延迟问答和快速生成。',
    tags: ['对话', '工具', '长文本'],
    kind: ['对话'],
    hot: true,
  },
  {
    id: 'Pro/deepseek-ai/DeepSeek-V3.2',
    provider: 'DeepSeek',
    title: 'Pro DeepSeek-V3.2',
    description: '当前项目默认模型，兼顾推理质量和中文教育内容生成。',
    tags: ['对话', '工具', '推理'],
    kind: ['对话', '推理'],
  },
  {
    id: 'deepseek-ai/DeepSeek-V3.2',
    provider: 'DeepSeek',
    title: 'DeepSeek-V3.2',
    description: '通用中文问答、学习资源生成、总结。',
    tags: ['对话', '推理'],
    kind: ['对话', '推理'],
  },
  {
    id: 'zai-org/GLM-5.2',
    provider: '智谱',
    title: 'GLM-5.2',
    description: '面向长程任务和工具调用的旗舰模型。',
    tags: ['对话', '工具', '长文本'],
    kind: ['对话', '推理'],
    hot: true,
  },
  {
    id: 'Pro/zai-org/GLM-5.1',
    provider: '智谱',
    title: 'Pro GLM-5.1',
    description: '面向智能体工程任务，适合规划、代码和长文档理解。',
    tags: ['对话', '工具', '编程'],
    kind: ['对话', '编程'],
  },
  {
    id: 'moonshotai/Kimi-K2.7-Code',
    provider: 'Kimi',
    title: 'Kimi-K2.7-Code',
    description: '面向代码任务，适合程序解释和代码生成。',
    tags: ['对话', '工具', '编程'],
    kind: ['对话', '编程'],
    hot: true,
  },
  {
    id: 'Pro/moonshotai/Kimi-K2.6',
    provider: 'Kimi',
    title: 'Pro Kimi-K2.6',
    description: '多模态智能体模型，适合长上下文和复杂问答。',
    tags: ['对话', '视觉', '工具'],
    kind: ['对话', '视觉'],
  },
  {
    id: 'MiniMaxAI/MiniMax-M2.5',
    provider: 'MiniMax',
    title: 'MiniMax-M2.5',
    description: '适合智能体工具调用、对话和内容生成。',
    tags: ['对话', '工具'],
    kind: ['对话', '推理'],
  },
  {
    id: 'nex-agi/Nex-N2-Pro',
    provider: 'nex-agi',
    title: 'Nex-N2-Pro',
    description: '强调自适应思考的模型，适合深度推理任务。',
    tags: ['对话', '工具', '推理'],
    kind: ['对话', '推理'],
  },
  {
    id: 'Tongyi-MAI/Z-Image-Turbo',
    provider: 'Tongyi-MAI',
    title: 'Z-Image-Turbo',
    description: '文生图模型，适合快速生成教学插图。',
    tags: ['生图'],
    kind: ['生图'],
  },
  {
    id: 'Tongyi-MAI/Z-Image',
    provider: 'Tongyi-MAI',
    title: 'Z-Image',
    description: '图像生成基础模型，适合较高质量的图片生成。',
    tags: ['生图'],
    kind: ['生图'],
  },
]

const config = ref(loadSiliconFlowConfig())
const showKey = ref(false)
const testing = ref(false)
const message = ref('')
const isError = ref(false)
const query = ref('')
const activeKind = ref<ModelKind>('全部')
const customModel = ref(config.value.model)
const modelKinds: ModelKind[] = ['全部', '对话', '推理', '编程', '视觉', '生图']

const selectedModel = computed(() => modelCatalog.find(item => item.id === config.value.model))
const filteredModels = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return modelCatalog.filter(item => {
    const matchesKind = activeKind.value === '全部' || item.kind.includes(activeKind.value as Exclude<ModelKind, '全部'>)
    const haystack = `${item.id} ${item.title} ${item.provider} ${item.description} ${item.tags.join(' ')}`.toLowerCase()
    return matchesKind && (!keyword || haystack.includes(keyword))
  })
})

function selectModel(model: SiliconFlowModel) {
  config.value.model = model.id
  customModel.value = model.id
  isError.value = false
  message.value = `已选择 ${model.id}`
}

function applyCustomModel() {
  const value = customModel.value.trim()
  if (!value) {
    isError.value = true
    message.value = '请输入模型标识'
    return
  }
  config.value.model = value
  isError.value = false
  message.value = `已使用自定义模型 ${value}`
}

function save() {
  applyCustomModel()
  if (isError.value) return
  saveSiliconFlowConfig(config.value)
  isError.value = false
  message.value = '配置已保存'
}

async function testConnection() {
  applyCustomModel()
  if (isError.value) return
  testing.value = true
  message.value = ''
  try {
    const result = await testSiliconFlow(config.value)
    saveSiliconFlowConfig(config.value)
    isError.value = false
    message.value = `${result.model}：${result.message}`
  } catch (error) {
    isError.value = true
    message.value = error instanceof Error ? error.message : '连接测试失败'
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>模型设置</h1>
      <p>配置大模型接口，用于对话、资源生成和学习分析</p>
    </div>

    <section class="panel">
      <div class="panel-header">
        <h2>接口配置</h2>
        <span class="current-model">当前：{{ config.model }}</span>
      </div>

      <div class="form-grid">
        <div class="form-item">
          <label>API Key</label>
          <div class="input-with-btn">
            <input v-model="config.api_key" :type="showKey ? 'text' : 'password'" placeholder="sk-..." />
            <button type="button" @click="showKey = !showKey">{{ showKey ? '隐藏' : '显示' }}</button>
          </div>
        </div>
        <div class="form-item">
          <label>Base URL</label>
          <input v-model="config.base_url" type="url" placeholder="https://api.siliconflow.cn/v1" />
        </div>
        <div class="form-item">
          <label>自定义模型</label>
          <div class="input-with-btn">
            <input v-model="customModel" type="text" placeholder="deepseek-ai/DeepSeek-V4-Pro" @change="applyCustomModel" />
            <button type="button" @click="applyCustomModel">应用</button>
          </div>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>选择模型</h2>
      </div>

      <div class="model-toolbar">
        <div class="kind-tabs">
          <button
            v-for="kind in modelKinds"
            :key="kind"
            type="button"
            :class="{ active: activeKind === kind }"
            @click="activeKind = kind"
          >
            {{ kind }}
          </button>
        </div>
        <div class="model-search">
          <span>⌕</span>
          <input v-model="query" placeholder="搜索模型" />
        </div>
      </div>

      <div class="model-list">
        <button
          v-for="model in filteredModels"
          :key="model.id"
          type="button"
          :class="['model-item', config.model === model.id ? 'selected' : '']"
          @click="selectModel(model)"
        >
          <div class="model-main">
            <div class="model-name">
              {{ model.title }}
              <span v-if="model.hot" class="hot-tag">热门</span>
            </div>
            <div class="model-provider">{{ model.provider }}</div>
          </div>
          <p class="model-desc">{{ model.description }}</p>
          <div class="model-tags">
            <span v-for="tag in model.tags" :key="tag">{{ tag }}</span>
          </div>
        </button>
      </div>
    </section>

    <section class="panel panel-actions-row">
      <div class="selected-info">
        <strong>{{ selectedModel?.title || '自定义模型' }}</strong>
        <span>{{ selectedModel?.description || '将直接使用你输入的模型标识。' }}</span>
      </div>
      <div class="action-buttons">
        <button class="btn-ghost" @click="save">保存设置</button>
        <button class="btn-primary" :disabled="testing" @click="testConnection">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
      </div>
    </section>

    <div v-if="message" :class="['tip', isError ? 'tip-error' : 'tip-success']">{{ message }}</div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #1f2937;
}

.page-header h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.current-model {
  padding: 4px 10px;
  border-radius: 6px;
  background: #f3f4f6;
  color: #4b5563;
  font-size: 12px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-grid .form-item:last-child {
  grid-column: 1 / -1;
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

.form-item input {
  padding: 9px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #1f2937;
  background: #fff;
  outline: none;
  transition: border-color 0.15s;
}

.form-item input:focus {
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(107, 114, 128, 0.1);
}

.input-with-btn {
  display: flex;
  gap: 8px;
}

.input-with-btn input {
  flex: 1;
  min-width: 0;
}

.input-with-btn button {
  flex: none;
  padding: 0 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  color: #374151;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.input-with-btn button:hover {
  background: #f3f4f6;
}

.model-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.kind-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kind-tabs button {
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

.kind-tabs button:hover {
  border-color: #d1d5db;
  color: #374151;
}

.kind-tabs button.active {
  color: #fff;
  border-color: #111827;
  background: #111827;
}

.model-search {
  width: min(240px, 100%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
}

.model-search span {
  color: #9ca3af;
  font-size: 14px;
}

.model-search input {
  width: 100%;
  padding: 8px 0;
  border: 0;
  outline: 0;
  background: transparent;
  font-size: 13px;
}

.model-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.model-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  color: #374151;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}

.model-item:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.model-item.selected {
  border-color: #111827;
  background: #f9fafb;
}

.model-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.model-name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 6px;
}

.hot-tag {
  padding: 2px 6px;
  border-radius: 4px;
  background: #fef3c7;
  color: #92400e;
  font-size: 10px;
  font-weight: 600;
}

.model-provider {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
}

.model-desc {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
  min-height: 36px;
}

.model-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.model-tags span {
  padding: 2px 8px;
  border-radius: 4px;
  color: #6b7280;
  background: #f3f4f6;
  font-size: 11px;
  font-weight: 500;
}

.panel-actions-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.selected-info {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-info strong {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.selected-info span {
  font-size: 12px;
  color: #6b7280;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.btn-primary,
.btn-ghost {
  padding: 9px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn-primary {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.btn-primary:hover:not(:disabled) {
  background: #1f2937;
  border-color: #1f2937;
}

.btn-ghost {
  background: #fff;
  color: #374151;
  border-color: #d1d5db;
}

.btn-ghost:hover {
  background: #f9fafb;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tip {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.tip-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.tip-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

@media (max-width: 760px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-grid .form-item:last-child {
    grid-column: auto;
  }

  .model-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .model-search {
    width: auto;
  }

  .model-list {
    grid-template-columns: 1fr;
  }

  .panel-actions-row {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    justify-content: flex-end;
  }
}
</style>
