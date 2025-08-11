<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title"> 步骤 8: 实验完成与总结 </a-typography-title>
  </div>

  <a-card class="result-summary mb-6" :bordered="false">
    <template #title>
      <div class="card-title"><file-text-outlined /> 实验结果速览</div>
    </template>
    <a-result :status="resultStatus" :title="resultTitle">
      <template #extra>
        <div class="result-actions">
          <a-button
            type="primary"
            size="large"
            @click="handleSave"
            :loading="isSaving"
            :disabled="isSaving || isLoading"
            class="generate-btn"
          >
            <template #icon><save-outlined /></template>
            保存实验记录
          </a-button>
          <a-button
            size="large"
            @click="$emit('restart')"
            :disabled="isSaving || isLoading"
            class="ant-btn-default ml-2"
          >
            <template #icon><reload-outlined /></template>
            重新开始一个新实验
          </a-button>
        </div>
      </template>
    </a-result>
  </a-card>

  <a-card class="step-output" :bordered="false">
    <template #title>
      <div class="card-title"><ordered-list-outlined /> 实验详情回顾</div>
    </template>
    <a-descriptions bordered :column="1" class="experiment-details">
      <a-descriptions-item label="实验问题">
        <a-typography-paragraph
          copyable
          class="summary-text"
          :ellipsis="{ rows: 2, expandable: true }"
        >
          {{ questionForSummary || '未提供' }}
        </a-typography-paragraph>
      </a-descriptions-item>
      <a-descriptions-item label="待推理图片">
        <div class="summary-image-container">
          <span v-if="!imagePathForSummary">未提供</span>
          <img
            v-if="imagePathForSummary"
            :src="imagePathForSummary"
            alt="实验图片"
            class="summary-image"
          />
        </div>
      </a-descriptions-item>
      <a-descriptions-item label="生成的图片描述 (步骤3)">
        <a-typography-paragraph
          copyable
          class="summary-text markdown-content"
          :ellipsis="{ rows: 3, expandable: true }"
          v-html="renderedImageDescription"
        >
        </a-typography-paragraph>
      </a-descriptions-item>
      <a-descriptions-item label="分析计划提示 (步骤4)">
        <a-typography-paragraph
          copyable
          class="summary-text"
          :ellipsis="{ rows: 3, expandable: true }"
        >
          {{ currentPlanPrompt || '未提供' }}
        </a-typography-paragraph>
      </a-descriptions-item>
      <a-descriptions-item label="生成的计划列表 (步骤4)">
        <a-list
          v-if="currentPlanList && currentPlanList.length > 0"
          size="small"
          bordered
          :data-source="currentPlanList"
          class="plan-list"
        >
          <template #renderItem="{ item, index }">
            <a-list-item>{{ index + 1 }}. {{ item }}</a-list-item>
          </template>
        </a-list>
        <span v-else>未生成计划列表</span>
      </a-descriptions-item>
      <a-descriptions-item label="计划执行结果总结 (步骤5)">
        <a-spin :spinning="isLoading && !parsedExecutionSteps.length">
          <a-collapse v-model:activeKey="activeExecutionKey" accordion class="steps-collapse">
            <a-collapse-panel
              v-for="stepItem in parsedExecutionSteps"
              :key="stepItem.key"
              :header="stepItem.title"
              class="step-panel"
            >
              <div
                v-if="stepItem.htmlContent"
                v-html="stepItem.htmlContent"
                class="step-content-html"
              ></div>
              <div v-else class="step-content-raw">
                <pre>{{ stepItem.rawContent }}</pre>
              </div>
            </a-collapse-panel>
            <a-collapse-panel
              v-if="parsedExecutionSteps.length === 0 && formattedExecutionSummary !== '无执行总结'"
              key="raw-fallback-execution"
              header="原始执行总结 (未解析到步骤)"
              :disabled="false"
              class="step-panel"
            >
              <pre style="white-space: pre-wrap; word-wrap: break-word">{{
                formattedExecutionSummary
              }}</pre>
            </a-collapse-panel>
            <a-collapse-panel
              v-if="parsedExecutionSteps.length === 0 && formattedExecutionSummary === '无执行总结'"
              key="no-content-fallback-execution"
              header="无执行总结"
              :disabled="true"
              class="step-panel"
            >
              <p>{{ formattedExecutionSummary }}</p>
            </a-collapse-panel>
          </a-collapse>
        </a-spin>
      </a-descriptions-item>

      <a-descriptions-item label="模型最终答案 (步骤6)">
        <a-typography-text class="final-answer-text">
          {{ parsedAnswerContent?.answer || '未获取' }}
        </a-typography-text>
      </a-descriptions-item>

      <a-descriptions-item label="模型答案解释 (步骤6)">
        <div
          v-if="modelExplanationHtml"
          v-html="modelExplanationHtml"
          class="summary-text markdown-content"
        ></div>
        <span v-else>未提供解释</span>
      </a-descriptions-item>

      <a-descriptions-item label="标准参考答案">
        <a-typography-text>
          {{ correctAnswer || '未提供' }}
        </a-typography-text>
      </a-descriptions-item>

      <a-descriptions-item v-if="evaluationData" label="AI评估理由 (步骤7)">
        <a-typography-paragraph
          copyable
          class="summary-text"
          :ellipsis="{ rows: 4, expandable: true }"
        >
          {{ evaluationData.justification || '未提供评估理由' }}
        </a-typography-paragraph>
      </a-descriptions-item>

      <a-descriptions-item v-if="myNewScore !== null" label="实验分数">
        <a-typography-text>
          {{ myNewScore }}
        </a-typography-text>
      </a-descriptions-item>
    </a-descriptions>
  </a-card>

  <div v-if="isLoading" class="loading-overlay">
    <a-spin size="large" tip="处理中...">
      <template #indicator>
        <loading-outlined spin class="custom-spin-icon" />
      </template>
    </a-spin>
  </div>
</template>

<script setup>
import { computed, ref, watch, createVNode } from 'vue'
import {
  Card as ACard,
  Result as AResult,
  Button as AButton,
  Descriptions as ADescriptions,
  DescriptionsItem as ADescriptionsItem,
  TypographyParagraph as ATypographyParagraph,
  TypographyText as ATypographyText,
  List as AList,
  ListItem as AListItem,
  Spin as ASpin,
  message,
  Typography,
  Collapse as ACollapse,
  CollapsePanel as ACollapsePanel
} from 'ant-design-vue'
import { marked } from 'marked'
import { experimentApi } from '@/apis/experiment_api'

const ATypographyTitle = Typography.Title

const props = defineProps({
  finalAnswer: {
    // This prop will contain the raw string, potentially with ```json
    type: String,
    default: null
  },
  modelExplanations: {
    type: String,
    default: null
  },
  correctAnswer: {
    type: String,
    default: null
  },
  imagePathForSummary: {
    type: String,
    default: ''
  },
  questionForSummary: {
    type: String,
    default: ''
  },
  currentImageDescription: {
    type: String,
    default: ''
  },
  currentPlanPrompt: {
    type: String,
    default: ''
  },
  currentPlanList: {
    type: Array,
    default: () => []
  },
  executionSummary: {
    type: [Object, String, null],
    default: null
  },
  evaluationData: {
    type: Object,
    default: null
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  myNewScore: {
    type: [Number, String, null],
    default: null
  },
  itemData: {
    type: Object,
    default: () => null // 默认值为 null 或空对象
  }
})
console.log('实验分数是:', props.myNewScore)
const emits = defineEmits(['restart'])

const isSaving = ref(false)

// Computed property to parse the finalAnswer string and extract answer/explanation
const parsedAnswerContent = computed(() => {
  const rawAnswer = props.finalAnswer

  if (!rawAnswer || typeof rawAnswer !== 'string') {
    return { answer: rawAnswer || '未获取', explanation: null } // Handle null/non-string input cleanly
  }

  // Regex to find ```json{...}``` and extract the content inside
  // Use a non-greedy match for the content `([\s\S]*?)`
  const jsonMatch = rawAnswer.match(/```json\s*([\s\S]*?)\s*```/)

  if (jsonMatch && jsonMatch[1]) {
    try {
      // Parse the extracted JSON string
      const parsed = JSON.parse(jsonMatch[1])
      // Check if it's an object and has an 'answer' key (and optional 'explanation')
      if (typeof parsed === 'object' && parsed !== null && typeof parsed.answer === 'string') {
        // Return an object containing answer and explanation
        return {
          answer: parsed.answer,
          explanation: typeof parsed.explanation === 'string' ? parsed.explanation : null
        }
      }
    } catch (e) {
      console.error('Failed to parse finalAnswer JSON:', e)
      // If parsing fails, fall through and treat as a simple string
    }
  }

  // If format doesn't match, parsing/extraction failed, or structure is wrong,
  // treat the whole original string as the answer with no explanation.
  // Also handle cases where the string wasn't null initially but didn't parse.
  return { answer: rawAnswer, explanation: null }
})

// Computed property to render the explanation as HTML
const modelExplanationHtml = computed(() => {
  const explanation = props.modelExplanations
  console.log('解释是：', explanation)

  if (!explanation) return null
  try {
    return marked(explanation)
  } catch (e) {
    console.error('Error parsing model explanation as Markdown:', e)
    // Return raw text in pre tag if markdown parsing fails
    return `<pre>${explanation}</pre>`
  }
})

// Computed property to render the image description as HTML
// 计算属性：渲染图片描述的Markdown
const renderedImageDescription = computed(() => {
  if (!props.currentImageDescription) return '未提供'
  try {
    return marked(props.currentImageDescription)
  } catch (e) {
    console.error('Error parsing image description as Markdown:', e)
    return props.currentImageDescription || '未提供'
  }
})

// Computed property to check for exact match (now uses parsed answer)
const isResultCorrect = computed(() => {
  // Compare the parsed answer with the correct answer
  const answer = parsedAnswerContent.value?.answer
  if (!answer || props.correctAnswer === null) return false // Need both to compare

  // Ensure both are strings before trimming/comparing case-insensitively
  if (typeof answer === 'string' && typeof props.correctAnswer === 'string') {
    return answer.trim().toLowerCase() === props.correctAnswer.trim().toLowerCase()
  }
  return false // Not comparable
})

// Computed property to check if the experiment is successful based on exact match or score
const isExperimentSuccessful = computed(() => {
  // Check for exact match first (uses updated isResultCorrect)
  if (isResultCorrect.value) {
    return true
  }
  // Then check if score exists and is greater than 60
  if (typeof props.myNewScore === 'number' && props.myNewScore > 60) {
    return true
  }
  // Otherwise, not successful
  return false
})

// Computed property for the result status ('success' or 'error')
const resultStatus = computed(() => {
  return isExperimentSuccessful.value ? 'success' : 'error'
})

// Computed property for the result title text
const resultTitle = computed(() => {
  if (isResultCorrect.value) {
    return '实验成功完成！答案与参考完全一致！' // Optional: Change text for exact match
  } else if (isExperimentSuccessful.value) {
    // This means score > 60 but not exact match
    return '实验成功完成！答案与参考基本一致！'
  } else {
    return '实验完成，但模型答案与参考不符'
  }
})

// --- Logic for Parsing and Displaying Execution Summary Steps (Copied from previous iteration) ---

const formattedExecutionSummary = computed(() => {
  if (!props.executionSummary) return '无执行总结'
  if (typeof props.executionSummary === 'string') return props.executionSummary
  return JSON.stringify(props.executionSummary, null, 2)
})

function extractIndividualSteps(resultText) {
  if (!resultText || typeof resultText !== 'string' || resultText === '无执行总结') {
    return []
  }
  const stepRegex = /步骤(?: \d*)?:\s*([\s\S]*?)(?=步骤(?: \d*)?:|$)/gs
  const matches = Array.from(resultText.matchAll(stepRegex))

  if (!matches || matches.length === 0) {
    return []
  }
  return matches.map((match) => match[1].trim())
}

const parsedExecutionSteps = computed(() => {
  const rawSteps = extractIndividualSteps(formattedExecutionSummary.value)
  if (rawSteps.length === 0) return []

  return rawSteps.map((stepContent, index) => {
    let htmlContent = ''
    let isMarkdown = true
    try {
      if (
        (stepContent.startsWith('{') && stepContent.endsWith('}')) ||
        (stepContent.startsWith('[') && stepContent.endsWith(']'))
      ) {
        JSON.parse(stepContent)
        isMarkdown = false
      }

      if (isMarkdown) {
        htmlContent = marked(stepContent)
      }
    } catch (e) {
      console.error(`Error parsing step ${index + 1}:`, e)
      htmlContent = ''
      isMarkdown = false
    }
    return {
      key: String(index + 1),
      title: `步骤 ${index + 1}`,
      htmlContent: isMarkdown ? htmlContent : null,
      rawContent: stepContent
    }
  })
})

const activeExecutionKey = ref([])

watch(
  parsedExecutionSteps,
  (newSteps) => {
    if (newSteps && newSteps.length > 0) {
      if (
        activeExecutionKey.value.length === 0 ||
        !newSteps.find((step) => activeExecutionKey.value.includes(step.key))
      ) {
        activeExecutionKey.value = [newSteps[0].key]
      }
    } else {
      activeExecutionKey.value = []
    }
  },
  { immediate: true, deep: true }
)

// --- End of Logic for Parsing and Displaying Execution Summary Steps ---
const handleSave = async () => {
  // 基础校验：检查必要的 prop 是否存在
  if (!props.itemData || typeof props.myNewScore === 'undefined' || props.myNewScore === null) {
    message.warning('缺少必要的实验数据或分数，无法保存。')
    return
  }

  const { userId, experimentId, selectedStepId } = props.itemData
  console.log('第8步获取的itemData是:', props.itemData)
  const score = props.myNewScore

  if (
    typeof userId === 'undefined' ||
    userId === null ||
    typeof experimentId === 'undefined' ||
    experimentId === null
  ) {
    message.warning('缺少用户ID或实验ID，无法保存实验记录。')
    return
  }

  isSaving.value = true

  try {
    // 调用 experimentApi 中新添加的方法
    const result = await experimentApi.completeExperimentRecord(
      userId,
      experimentId,
      score,
      selectedStepId
    )
    message.success(result.message || '实验记录已保存并标记完成！')
  } catch (error) {
    // experimentApi 已经处理了 console.error，这里只弹窗
    message.error(error.message || '保存失败: 未知错误')
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
/* Base styles for the component */
.experiment-step {
  margin-bottom: 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  padding: 24px;
  position: relative;
  font-family: 'Arial', sans-serif;
  /* Example: Set a consistent base font */
  color: #262626;
  /* Default text color */
  line-height: 1.6;
  /* Default line height */
}

.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  user-select: text;
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

/* Styling for the result summary card */
.result-summary {
  margin-bottom: 24px;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  user-select: text;
}

/* Styling for the result actions (buttons) */
.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

/* Styling for the experiment details card */
.step-output {
  background-color: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  user-select: text;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  padding: 12px 0;
  /* Match ant-card-head-title padding */
}

.card-title :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}

/* Consistent margin classes */
.mt-6 {
  margin-top: 32px;
}

.mb-6 {
  margin-bottom: 32px;
}

.ml-2 {
  margin-left: 8px;
}

/* Button styles */
.generate-btn,
.ant-btn-default {
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
  color: white;
  border: none;
  /* Remove default border */
}

.generate-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.ant-btn-default {
  border-color: #d9d9d9;
  color: #595959;
  /* Default button text color */
}

.ant-btn-default:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #40a9ff;
  /* Example hover border color */
  color: #40a9ff;
  /* Example hover text color */
}

.generate-btn:disabled,
.ant-btn-default:disabled {
  background: #f5f5f5;
  color: rgba(0, 0, 0, 0.25);
  border-color: #d9d9d9;
  box-shadow: none;
  transform: none;
}

/* Descriptions List Styles */
.experiment-details :deep(.ant-descriptions-item-label) {
  font-weight: 600;
  color: #595959;
  background-color: #f5f7fa;
  /* Consistent label background */
}

.experiment-details :deep(.ant-descriptions-item-content) {
  font-size: 15px;
  line-height: 1.7;
  /* Adjusted line height for consistency */
  color: #262626;
  padding-top: 10px;
  /* Ensure padding consistent with label */
  padding-bottom: 10px;
}

.experiment-details :deep(.ant-descriptions-bordered .ant-descriptions-item-label) {
  /* This rule exists in Ant Design, reinforce background */
  background-color: #f5f7fa;
}

/* Styles for the plan list within descriptions */
.plan-list {
  margin: 0;
  /* Remove default margin */
}

.plan-list :deep(.ant-list-item) {
  line-height: 1.7;
  /* Consistent line height */
  padding: 8px 0;
}

.plan-list.ant-list-bordered {
  border-radius: 4px;
  border: 1px solid #d9d9d9;
}

/* Styling for standard summary texts (used for question, description, prompt, evaluation) */
.summary-text {
  word-break: break-word;
  /* white-space: pre-wrap; /* Ellipsis might interfere */
  margin-bottom: 0 !important;
  /* Remove paragraph default margin */
  line-height: 1.7;
  /* Consistent line height */
}

/* Container for the image to help control layout */
.summary-image-container {
  display: flex;
  align-items: center;
  min-height: 50px;
  /* Give it a minimum height even if no image */
}

.summary-image {
  max-width: 200px;
  max-height: 200px;
  width: auto;
  height: auto;
  object-fit: contain;

  margin-top: 0;
  /* Remove top margin as container provides space */
  margin-bottom: 0;
  /* Remove bottom margin */
  display: block;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* --- Styles for the Collapse/Steps (Copied from first component) --- */
.steps-collapse {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
  margin-top: 8px;
  /* Add some space above collapse */
  margin-bottom: 8px;
  /* Add some space below collapse */
}

.step-panel :deep(.ant-collapse-header) {
  font-weight: 500;
  background-color: #f0f5ff;
  color: #262626;
  /* Consistent header text color */
}

.step-panel :deep(.ant-collapse-content-box) {
  padding: 16px;
  background-color: #fff;
}

.step-content-raw pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f7f7f7;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
  font-family: inherit;
  font-size: inherit;
  line-height: 1.6;
  /* Consistent line height */
  color: #333;
}

/* Markdown content styling inside steps and explanation */
.step-content-html :deep(h1),
.step-content-html :deep(h2),
.step-content-html :deep(h3),
.step-content-html :deep(h4),
.step-content-html :deep(h5),
.step-content-html :deep(h6),
.markdown-content :deep(h1),
/* Applied to explanation markdown */
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
  color: #262626;
}

.step-content-html :deep(h1),
.markdown-content :deep(h1) {
  font-size: 1.8em;
}

.step-content-html :deep(h2),
.markdown-content :deep(h2) {
  font-size: 1.6em;
}

.step-content-html :deep(h3),
.markdown-content :deep(h3) {
  font-size: 1.4em;
}

.step-content-html :deep(p),
.markdown-content :deep(p)

/* Applied to explanation markdown */ {
  margin-bottom: 1em;
  line-height: 1.7;
  color: #595959;
}

.step-content-html :deep(ul),
.step-content-html :deep(ol),
.markdown-content :deep(ul),
/* Applied to explanation markdown */
.markdown-content :deep(ol) {
  margin-bottom: 1em;
  padding-left: 2em;
}

.step-content-html :deep(li),
.markdown-content :deep(li)

/* Applied to explanation markdown */ {
  margin-bottom: 0.5em;
  line-height: 1.7;
  color: #595959;
}

.step-content-html :deep(pre),
.markdown-content :deep(pre)

/* Applied to explanation markdown */ {
  background-color: #f0f8ff;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  border: 1px solid #d9eaff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #333;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  /* Monospace font */
  font-size: 0.95em;
  /* Slightly smaller font size */
  line-height: 1.6;
  /* Consistent line height */
}

.step-content-html :deep(code),
.markdown-content :deep(code)

/* Applied to explanation markdown */ {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  background-color: #e6f7ff;
  padding: 0.2em 0.5em;
  border-radius: 4px;
  font-size: 0.9em;
  color: #c24105;
}

.step-content-html :deep(pre code),
.markdown-content :deep(pre code)

/* Applied to explanation markdown */ {
  background-color: transparent;
  padding: 0;
  font-size: 1em;
  /* Inherit size from pre */
  border: none;
  box-shadow: none;
  color: inherit;
}

.step-content-html :deep(blockquote),
.markdown-content :deep(blockquote)

/* Applied to explanation markdown */ {
  border-left: 5px solid #add8e6;
  padding: 10px 15px;
  margin-left: 0;
  margin-bottom: 1em;
  color: #4a4a4a;
  background-color: #f0f8ff;
  border-radius: 0 4px 4px 0;
}

.step-content-html :deep(table),
.markdown-content :deep(table)

/* Applied to explanation markdown */ {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1em;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.step-content-html :deep(th),
.step-content-html :deep(td),
.markdown-content :deep(th),
/* Applied to explanation markdown */
.markdown-content :deep(td) {
  border: 1px solid #cce7ff;
  padding: 10px 12px;
  text-align: left;
}

.step-content-html :deep(th),
.markdown-content :deep(th)

/* Applied to explanation markdown */ {
  background-color: #e6f7ff;
  font-weight: 600;
  color: #262626;
}

.step-content-html :deep(tr:nth-child(even)),
.markdown-content :deep(tr:nth-child(even))

/* Applied to explanation markdown */ {
  background-color: #f9fcff;
}

.step-content-html :deep(hr),
.markdown-content :deep(hr)

/* Applied to explanation markdown */ {
  border: 0;
  height: 1px;
  background: #cce7ff;
  margin: 1.5em 0;
}

/* --- End of Styles for the Collapse/Steps --- */

/* Style for the final answer text */
.final-answer-text {
  color: #262626 !important;
  /* Ensure color is black, !important to override Ant Design type colors */
  line-height: 1.7;
  /* Consistent line height */
  display: inline-block;
  /* Needed if you want vertical alignment with label */
  vertical-align: middle;
  /* Align with label */
}

/* Loading Overlay Styling */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 12px;
}

.loading-overlay :deep(.ant-spin-text) {
  margin-top: 8px;
  font-size: 16px;
  color: #262626;
}

.loading-overlay .custom-spin-icon {
  font-size: 36px;
  color: #1890ff;
}

/* Ant Design Overrides */
:deep(.ant-card-head) {
  min-height: 48px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-result) {
  padding: 24px;
}

:deep(.ant-result-icon) {
  margin-bottom: 16px;
}

:deep(.ant-result-title) {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 8px;
}

:deep(.ant-result-subtitle) {
  font-size: 15px;
  color: #595959;
  line-height: 1.6;
}

:deep(.ant-result-extra) {
  margin-top: 24px;
}

:deep(.ant-list-bordered) {
  border: 1px solid #d9d9d9;
}

:deep(.ant-list-item) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-list-item:last-child) {
  border-bottom: none;
}

/* Specific style for typography paragraph with ellipsis and copyable */
:deep(.summary-text.ant-typography-ellipsis) {
  display: block;
  width: 100%;
}

@media (max-width: 768px) {
  .result-actions {
    flex-direction: column;
    gap: 12px;
  }

  .ant-btn-default.ml-2 {
    margin-left: 0;
  }
}
</style>
