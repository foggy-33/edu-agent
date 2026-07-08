import type { SiliconFlowConfig } from '../types/profile'

const STORAGE_KEY = 'studyflow_siliconflow_config'

export const defaultSiliconFlowConfig: SiliconFlowConfig = {
  api_key: '',
  base_url: 'https://api.siliconflow.cn/v1',
  model: 'deepseek-ai/DeepSeek-V4-Pro'
}

export function loadSiliconFlowConfig(): SiliconFlowConfig {
  try {
    return { ...defaultSiliconFlowConfig, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }
  } catch {
    return { ...defaultSiliconFlowConfig }
  }
}

export function saveSiliconFlowConfig(config: SiliconFlowConfig) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
}
