<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title">
      步骤 5: 执行计划并获取结果
    </a-typography-title>
  </div>
  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="基于实验计划，这一步我们将按照计划逐步执行并获取结果。"
  />
  <div v-if="!planList || planList.length === 0" class="mb-4">
    <a-alert message="请先在步骤 4 生成计划列表后再执行。" type="warning" show-icon />
  </div>

  <a-button
    type="primary"
    @click="handleExecutePlan"
    :disabled="!planList || planList.length === 0 || internalIsLoading"
    :loading="internalIsLoading"
    class="execute-btn mt-6"
    aria-label="执行计划"
  >
    <template #icon><play-circle-outlined /></template>
    {{ internalIsLoading ? '执行中...' : '执行计划' }}
  </a-button>

  <div v-if="apiError" class="error-message mt-4">
    <a-alert type="error" :message="apiError" show-icon />
  </div>

  <div v-if="executionSteps.length > 0 || internalIsLoading" class="step-output mt-6">
    <div class="section-title"><file-text-outlined /> 计划执行结果</div>

    <a-spin
      :spinning="internalIsLoading && executionSteps.length === 0"
      tip="正在初始化计划执行，请稍候..."
    >
      <VaCard
        v-for="(stepItem, index) in executionSteps"
        :key="index"
        stripe
        stripe-color="info"
        class="mb-4 result-card"
      >
        <VaCardTitle>
          <h3 class="step-result-title">{{ stepItem.title }}</h3>
        </VaCardTitle>
        <VaCardContent>
          <div v-html="stepItem.htmlContent"></div>
        </VaCardContent>
      </VaCard>
    </a-spin>
  </div>

  <div v-else-if="hasAttemptedExecution && !internalIsLoading" class="step-output mt-6">
    <a-empty description="未能获取计划执行结果或结果为空" />
  </div>

  <div class="next-step-action mt-6">
    <a-button
      type="primary"
      @click="$emit('next')"
      :disabled="executionSteps.length === 0 || internalIsLoading || !isExecutionComplete"
      class="next-btn"
      aria-label="前往下一步实验流程"
    >
      <template #icon><arrow-right-outlined /></template>
      前往下一步实验流程
    </a-button>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import {
  Button as AButton,
  Spin as ASpin,
  Alert as AAlert,
  Empty as AEmpty,
  message,
  Typography
} from 'ant-design-vue'
import {
  ExperimentOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import { marked } from 'marked'

// 假设 Vuestic UI 组件已正确导入
// import { VaCard, VaCardTitle, VaCardContent } from 'vuestic-ui';

const props = defineProps({
  planList: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  detailedInfo: {
    type: [Object, String, null],
    default: null
  },
  imageDescription: {
    type: String,
    default: ''
  }
})

const emits = defineEmits(['update:detailedInfo', 'next', 'update:isLoading'])

const internalIsLoading = ref(props.isLoading)
const apiError = ref(null)
const hasAttemptedExecution = ref(false)
const executionSteps = ref([]) // 存储流式步骤
const totalSteps = ref(0) // 总步骤数
const isExecutionComplete = ref(false) // 执行完成标记

// 同步 props.isLoading
watch(
  () => props.isLoading,
  (newVal) => {
    internalIsLoading.value = newVal
  }
)

// 兼容非流式结果
watch(
  () => props.detailedInfo,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      parseExecutionResult(newVal)
    }
  },
  { immediate: true }
)

// 渲染 Markdown
function getMarkdownHtml(content) {
  try {
    return marked(content)
  } catch (e) {
    console.error('Markdown 解析错误:', e)
    return `<pre>${content}</pre>`
  }
}

// 处理流式 chunk
function processStreamChunk(stepIndex, content) {
  if (!executionSteps.value[stepIndex]) {
    executionSteps.value[stepIndex] = {
      title: `步骤 ${stepIndex + 1}: ${props.planList[stepIndex] || ''}`,
      content: content,
      htmlContent: getMarkdownHtml(content)
    }
  } else {
    executionSteps.value[stepIndex].content += content
    executionSteps.value[stepIndex].htmlContent = getMarkdownHtml(
      executionSteps.value[stepIndex].content
    )
  }
  executionSteps.value = [...executionSteps.value] // 触发响应式更新
  nextTick()
}

const handleExecutePlan = async () => {
  if (!props.planList || props.planList.length === 0) {
    message.warn('计划列表为空，无法执行。')
    return
  }

  emits('update:isLoading', true)
  internalIsLoading.value = true
  apiError.value = null
  hasAttemptedExecution.value = true
  executionSteps.value = [] // 清空步骤
  totalSteps.value = 0
  isExecutionComplete.value = false

  // 预先创建第一个步骤卡片，避免显示"未能获取计划执行结果或结果为空"
  if (props.planList && props.planList.length > 0) {
    executionSteps.value = [
      {
        title: `步骤 1: ${props.planList[0] || ''}`,
        content: '正在执行...',
        htmlContent: '<p>正在执行...</p>'
      }
    ]
  }

  try {
    const response = await fetch('/api/execute-plan-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream'
      },
      body: JSON.stringify({
        plan_list: props.planList,
        image_caption: props.imageDescription
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: '执行计划流失败'
      }))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
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
          try {
            const event = JSON.parse(jsonData)
            console.log('收到 SSE 事件:', event)

            switch (event.event) {
              case 'init':
                totalSteps.value = event.data.total_steps || 0
                // 不再预先创建所有步骤卡片
                internalIsLoading.value = false // 初始化后停止加载
                break

              case 'step_start':
                const { step_index, step } = event.data
                // 创建新步骤，使用编号格式
                executionSteps.value[step_index] = {
                  title: `步骤 ${step_index + 1}: ${step}`,
                  content: '',
                  htmlContent: ''
                }
                executionSteps.value = [...executionSteps.value]
                break

              case 'chunk':
                const { step_index: chunkStepIndex, content } = event.data
                processStreamChunk(chunkStepIndex, content)
                break

              case 'step_complete':
                const { step_index: completeStepIndex, final_output } = event.data
                if (executionSteps.value[completeStepIndex]) {
                  executionSteps.value[completeStepIndex].content = final_output
                  executionSteps.value[completeStepIndex].htmlContent =
                    getMarkdownHtml(final_output)
                  executionSteps.value = [...executionSteps.value]
                }
                break

              case 'error':
                throw new Error(event.data)

              case 'complete':
                isExecutionComplete.value = true
                internalIsLoading.value = false
                emits('update:isLoading', false)
                // 保存最终结果，使用编号格式
                const finalResult = executionSteps.value
                  .map(
                    (step, idx) => `步骤 ${idx + 1}: ${props.planList[idx]}\n输出: ${step.content}`
                  )
                  .join('\n\n')
                emits('update:detailedInfo', finalResult)
                message.success('计划执行完成！')
                return

              default:
                console.warn('未知事件类型:', event.event)
            }
          } catch (e) {
            console.error('解析 SSE 数据错误:', e, jsonData)
            apiError.value = `解析流数据失败: ${e.message}`
          }
        }
      }
    }
  } catch (error) {
    console.error('执行计划流错误:', error)
    apiError.value = error.message || '执行计划时发生未知错误。'
    message.error(apiError.value)
    executionSteps.value = []
  } finally {
    if (internalIsLoading.value) {
      internalIsLoading.value = false
      emits('update:isLoading', false)
    }
  }
}

// 解析非流式结果
function parseExecutionResult(resultText) {
  if (!resultText || typeof resultText !== 'string') {
    executionSteps.value = []
    return
  }
  const stepRegex = /步骤 (\d+): (.*?)\n输出: (.*?)(?=\n\n步骤|$)/gs
  const steps = []
  let match
  while ((match = stepRegex.exec(resultText))) {
    const stepNum = match[1]?.trim()
    const step = match[2]?.trim()
    const output = match[3]?.trim()
    if (step && output) {
      steps.push({
        title: `步骤 ${stepNum}: ${step}`,
        content: output,
        htmlContent: getMarkdownHtml(output)
      })
    }
  }
  executionSteps.value = steps
  isExecutionComplete.value = true
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

.section-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

.mb-4 {
  margin-bottom: 16px !important;
}

.mt-4 {
  margin-top: 16px !important;
}

.mt-6 {
  margin-top: 24px !important;
}

.ml-4 {
  margin-left: 16px !important;
}

.error-message {
  margin-top: 16px;
}

.step-output {
  margin-top: 32px;
  background-color: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
  user-select: text;
}

.result-card {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.step-result-title {
  font-size: 1.5em;
  font-weight: 600;
  color: #262626;
  margin: 0;
}

.execute-btn,
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

.execute-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.next-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.execute-btn:hover,
.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.execute-btn:disabled,
.next-btn:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  border-color: #d9d9d9;
  box-shadow: none;
  transform: none;
}

.next-step-action {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.step-output :deep(h1),
.step-output :deep(h2),
.step-output :deep(h3),
.step-output :deep(h4),
.step-output :deep(h5),
.step-output :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: bold;
}

.step-output :deep(p) {
  margin-bottom: 1em;
  line-height: 1.6;
}

.step-output :deep(ul),
.step-output :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.step-output :deep(li) {
  margin-bottom: 0.5em;
}

.step-output :deep(pre) {
  background-color: #f0f8ff;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  border: 1px solid #d9eaff;
}

.step-output :deep(code) {
  font-family: monospace;
  background-color: #dcf0ff;
  padding: 0.2em 0.4em;
  border-radius: 3px;
}

.step-output :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.step-output :deep(blockquote) {
  border-left: 4px solid #add8e6;
  padding-left: 1em;
  margin-left: 0;
  color: #555;
  background-color: #f0f8ff;
}

.step-output :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
}

.step-output :deep(th),
.step-output :deep(td) {
  border: 1px solid #cce7ff;
  padding: 8px;
  text-align: left;
}

.step-output :deep(th) {
  background-color: #e6f7ff;
}

.ant-spin-container {
  width: 100%;
}

:deep(.ant-alert-message) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

:deep(.ant-spin-text) {
  font-size: 14px;
  margin-top: 8px;
}
</style>
