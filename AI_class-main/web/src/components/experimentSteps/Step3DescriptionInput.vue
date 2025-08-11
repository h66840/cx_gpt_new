<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title"> 步骤 3: 生成图片描述 </a-typography-title>
  </div>

  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="在这一步中，我们将使用AI模型对实验图片进行详细描述，这将帮助我们更好地理解图片内容。"
  />

  <a-row :gutter="[32, 32]" class="mt-6">
    <a-col :span="24" :md="12">
      <a-card class="image-preview-card" :bordered="true">
        <template #title>
          <div class="card-title"><picture-outlined /> 实验图片</div>
        </template>
        <template v-if="selectedImage?.path">
          <div class="image-container">
            <a-image
              :src="selectedImage?.path"
              :alt="selectedImage?.description || '实验图片'"
              class="experiment-image"
              :preview="{ src: selectedImage?.path }"
            />
          </div>
        </template>
        <template v-else>
          <a-empty description="未找到实验图片" />
        </template>
      </a-card>
    </a-col>

    <a-col :span="24" :md="12">
      <a-form layout="vertical" class="prompt-form">
        <a-form-item label="输入初始提示词:" required class="form-label">
          <a-textarea
            v-model:value="localInitialPrompt"
            :rows="4"
            placeholder="请输入你对图片的观察或希望模型关注的点..."
            :disabled="internalIsLoading"
            allow-clear
            class="prompt-textarea"
          />
        </a-form-item>

        <a-card title="提示词示例" size="small" class="prompt-suggestions">
          <template #title>
            <div class="card-title"><bulb-filled /> 提示词示例</div>
          </template>
          <a-space direction="vertical" style="width: 100%" size="middle">
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="useSuggestion('请详细描述这张图片中的所有视觉元素，包括物体、文字和关系。')"
            >
              <bulb-outlined /> 详细描述所有视觉元素
            </a-tag>
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="useSuggestion('请识别图片中的关键信息，特别关注任何文字、符号或标记。')"
            >
              <bulb-outlined /> 识别关键信息和标记
            </a-tag>
            <a-tag
              color="blue"
              class="suggestion-tag"
              @click="
                useSuggestion('请分析图片中的主要对象及其特征，重点关注可能与问题相关的细节。')
              "
            >
              <bulb-outlined /> 分析主要对象及特征
            </a-tag>
          </a-space>
        </a-card>

        <a-space class="mt-6 action-buttons" size="large">
          <a-button
            type="primary"
            size="large"
            :loading="internalIsLoading"
            @click="generateDescription"
            :disabled="!localInitialPrompt.trim() || !selectedImage?.path"
            class="generate-btn"
          >
            <template #icon><robot-outlined /></template>
            {{ internalIsLoading ? '生成中...' : '生成图片描述' }}
          </a-button>

          <a-button
            type="primary"
            size="large"
            @click="goToNextStep"
            :disabled="!localImageDescription || internalIsLoading"
            class="next-btn"
          >
            <template #icon><arrow-right-outlined /></template>
            前往下一步实验流程
          </a-button>
        </a-space>
      </a-form>
    </a-col>
  </a-row>

  <a-collapse
    v-if="props.imageDescription || internalIsLoading || apiError"
    class="mt-6 result-collapse"
    :bordered="false"
    expand-icon-position="start"
    :default-active-key="['1']"
  >
    <a-collapse-panel key="1" header="图片描述结果">
      <template #header>
        <div class="collapse-header"><file-text-outlined /> 图片描述结果</div>
      </template>
      <a-spin
        :spinning="internalIsLoading"
        :delay="100"
        tip="AI正在分析图片并生成描述，这可能需要几秒钟..."
      >
        <!-- 修改这里：使用v-html渲染markdown内容 -->
        <div
          v-if="!internalIsLoading"
          class="description-result markdown-content"
          v-html="renderedMarkdown"
        ></div>
      </a-spin>
    </a-collapse-panel>
  </a-collapse>
</template>

<script setup>
import { defineProps, defineEmits, computed, ref, watch, nextTick } from 'vue'
import axios from 'axios'
import {
  ExperimentOutlined,
  EyeOutlined,
  BulbOutlined,
  RobotOutlined,
  ArrowRightOutlined
} from '@ant-design/icons-vue'
// 导入markdown-it
import MarkdownIt from 'markdown-it'

// 创建markdown-it实例
const md = new MarkdownIt({
  html: true, // 启用HTML标签
  breaks: true, // 将\n转换为<br>
  linkify: true // 自动将URL转换为链接
})

const props = defineProps({
  initialPrompt: {
    type: String,
    default: ''
  },
  // experimentData 保留 prop 定义，但不再用于获取图片
  experimentData: {
    type: Object,
    default: () => null
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  imageDescription: {
    type: String,
    default: null
  },
  // experimentId: {
  //   type: String,
  //   required: true,
  // },
  // ### itemData 是现在获取图片的唯一来源 ###
  itemData: {
    type: Object,
    default: () => null // 默认值为 null 或空对象
  }
})

// 定义组件发出的事件
const emits = defineEmits([
  'update:initialPrompt',
  'update:imageDescription',
  'update:isLoading',
  'saveState',
  'next'
])

// 本地状态
const apiError = ref(null)
const localInitialPrompt = ref(props.initialPrompt)
const localImageDescription = ref(props.imageDescription)
const internalIsLoading = ref(props.isLoading)

// 计算属性：渲染Markdown
const renderedMarkdown = computed(() => {
  if (!localImageDescription.value) return ''
  try {
    const rendered = md.render(localImageDescription.value || '')
    // console.log('Rendered Markdown:', rendered) // 调试 Markdown 输出
    return rendered
  } catch (e) {
    console.error('Markdown 渲染出错:', e)
    return localImageDescription.value // 出错时返回原始文本
  }
})

// 监听props变化，更新本地状态
watch(
  () => props.initialPrompt,
  (newVal) => {
    localInitialPrompt.value = newVal
  }
)

watch(
  () => props.imageDescription,
  (newVal) => {
    localImageDescription.value = newVal
  }
)

watch(
  () => props.isLoading,
  (newVal) => {
    internalIsLoading.value = newVal
  }
)

// 监听本地状态变化，更新父组件
watch(localInitialPrompt, (newVal) => {
  emits('update:initialPrompt', newVal)
})

watch(localImageDescription, (newVal) => {
  emits('update:imageDescription', newVal)
})

// ### 修改计算属性：只从 itemData 获取当前选中的图片 ###
const selectedImage = computed(() => {
  if (props.itemData && props.itemData.image_path) {
    return {
      path: props.itemData.image_path,
      description: props.itemData.image_description || '实验图片' // 使用 itemData 里的描述或默认值
    }
  }

  // 不再检查 experimentData
  return null
})

// 使用提示词建议 (逻辑保持不变)
const useSuggestion = (suggestion) => {
  localInitialPrompt.value = suggestion
  emits('update:initialPrompt', suggestion)
}

// 生成图片描述
const generateDescription = async () => {
  if (!localInitialPrompt.value.trim() || !selectedImage.value?.path) {
    console.warn('提示词或图片路径缺失，无法生成描述。')
    return
  }

  apiError.value = null
  internalIsLoading.value = true // 开始加载
  emits('update:isLoading', true)
  localImageDescription.value = ''
  emits('update:imageDescription', '')

  try {
    const response = await fetch('/api/describe-image', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream'
      },
      body: JSON.stringify({
        image_path: selectedImage.value.path,
        prompt: localInitialPrompt.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }))
      throw new Error(
        errorData.detail || errorData.message || `HTTP error! status: ${response.status}`
      )
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let eolIndex
      while ((eolIndex = buffer.indexOf('\n\n')) >= 0) {
        const line = buffer.substring(0, eolIndex).trim()
        buffer = buffer.substring(eolIndex + 2)

        if (line.startsWith('data:')) {
          const jsonData = line.substring('data:'.length).trim()
          // console.log('Received SSE data:', jsonData)
          try {
            const data = JSON.parse(jsonData)
            if (data.error) {
              console.error('Streaming error from server:', data.error)
              apiError.value = `生成图片描述失败: ${data.error}`
              localImageDescription.value = ''
              emits('update:imageDescription', null)
              internalIsLoading.value = false // 错误时停止加载
              emits('update:isLoading', false)
              return
            } else if (data.status === 'done') {
              console.log('Streaming finished.')
              internalIsLoading.value = false // 流结束时停止加载
              emits('update:isLoading', false)
              emits('saveState')
              return
            } else if (data.description_chunk) {
              // console.log('Description chunk:', data.description_chunk)
              localImageDescription.value += data.description_chunk
              emits('update:imageDescription', localImageDescription.value)
              // 接收到第一个 chunk 时停止加载状态
              if (internalIsLoading.value) {
                internalIsLoading.value = false
                emits('update:isLoading', false)
              }
              // 强制触发响应式更新
              await nextTick()
            }
          } catch (e) {
            console.error('Error parsing stream data:', e, jsonData)
          }
        }
      }
    }

    if (buffer.startsWith('data:')) {
      const jsonData = buffer.substring('data:'.length).trim()
      try {
        const data = JSON.parse(jsonData)
        if (data.description_chunk) {
          localImageDescription.value += data.description_chunk
          emits('update:imageDescription', localImageDescription.value)
          if (internalIsLoading.value) {
            internalIsLoading.value = false
            emits('update:isLoading', false)
          }
          await nextTick()
        }
      } catch (e) {
        console.error('Error parsing final stream data:', e, jsonData)
      }
    }
  } catch (error) {
    console.error('生成图片描述时出错:', error)
    apiError.value = `生成图片描述失败: ${error.message || '未知错误'}`
    localImageDescription.value = null
    emits('update:imageDescription', null)
  } finally {
    if (internalIsLoading.value) {
      internalIsLoading.value = false
      emits('update:isLoading', false)
    }
    nextTick(() => {
      emits('saveState')
    })
  }
}
// 前往下一步 (逻辑保持不变)
const goToNextStep = () => {
  emits('next')
}
</script>

<style scoped>
.experiment-step {
  margin-bottom: 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  padding: 24px;
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.step-icon {
  font-size: 28px;
  color: #1890ff;
  margin-right: 12px;
}

.step-title {
  margin-bottom: 0 !important;
  font-weight: 600 !important;
  color: #262626;
}

.step-info {
  margin-bottom: 24px;
  border-radius: 8px;
  font-size: 16px;
}

.mt-6 {
  margin-top: 32px;
}

.image-preview-card {
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.image-preview-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.card-title :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 240px;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  padding: 1px;
}

.experiment-image {
  max-width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.prompt-form {
  padding: 4px;
}

.form-label :deep(.ant-form-item-label > label) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.prompt-textarea {
  border-radius: 8px;
  font-size: 16px;
  resize: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.prompt-textarea:hover {
  border-color: #40a9ff;
}

.prompt-suggestions {
  margin-top: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.suggestion-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 14px;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

.suggestion-tag :deep(svg) {
  margin-right: 6px;
  font-size: 16px;
}

.action-buttons {
  margin-top: 28px;
  display: flex;
  justify-content: flex-start;
}

.generate-btn,
.next-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.generate-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.next-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.generate-btn:hover,
.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.generate-btn:disabled,
.next-btn:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  border-color: #d9d9d9;
  box-shadow: none;
  transform: none;
}

.result-collapse {
  margin-top: 36px;
  background-color: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.collapse-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.collapse-header :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.description-result {
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1.8;
  user-select: text;
}

/* 添加Markdown内容样式 */
.markdown-content {
  color: #262626;
}

/* Markdown内容样式优化 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 16px;
  margin-bottom: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: #262626;
}

.markdown-content :deep(h1) {
  font-size: 24px;
}

.markdown-content :deep(h2) {
  font-size: 22px;
}

.markdown-content :deep(h3) {
  font-size: 20px;
}

.markdown-content :deep(h4) {
  font-size: 18px;
}

.markdown-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-content :deep(li) {
  margin-bottom: 6px;
}

.markdown-content :deep(a) {
  color: #1890ff;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(blockquote) {
  padding: 8px 16px;
  margin: 16px 0;
  border-left: 4px solid #1890ff;
  background-color: #e6f7ff;
  color: #595959;
}

.markdown-content :deep(code) {
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 14px;
}

.markdown-content :deep(pre) {
  background-color: #f0f2f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #fafafa;
  font-weight: 600;
}

.markdown-content :deep(tr:nth-child(even)) {
  background-color: #fafafa;
}

/* 覆盖一些 Ant Design 默认样式 */
:deep(.ant-card-head) {
  min-height: 48px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-card-head-title) {
  padding: 12px 0;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
  padding: 16px 24px !important;
}

:deep(.ant-collapse-content-box) {
  padding: 24px !important;
}

:deep(.ant-alert-message) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

:deep(.ant-alert-description) {
  font-size: 14px;
  color: #595959;
  margin-top: 4px;
}

:deep(.ant-spin-text) {
  font-size: 14px;
  margin-top: 8px;
}

:deep(.ant-typography) {
  color: #262626;
}
</style>
