<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title">
      步骤 2: 基础知识测试结果分析与提示
    </a-typography-title>
  </div>

  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="提示: 第一部分的 quiz 与实验成绩无关，学生需要设计图像 caption提示词以及计划提示词，让模型最终能推理正确答案以及对应的解释，效果越好分数越高！"
  />

  <div v-if="isInitialLoading" class="loading-container">
    <a-spin tip="加载实验数据中..."></a-spin>
  </div>

  <div v-else-if="initialLoadError" class="error-container">
    <a-alert type="error" show-icon>
      <template #message>加载实验数据失败</template>
      <template #description>
        {{ initialLoadError.message }}
        <a-button type="primary" size="small" @click="getExperimentDetails" class="retry-btn">
          重试加载
        </a-button>
      </template>
    </a-alert>
  </div>

  <div v-else>
    <div class="nav-tabs">
      <div
        class="nav-item"
        :class="{ active: activeTabId === 'dataset-content' }"
        @click="setActiveTab('dataset-content')"
        role="tab"
        aria-controls="dataset-content"
        :aria-selected="activeTabId === 'dataset-content'"
      >
        <span class="nav-circle"></span>
        <span class="nav-text">数据集</span>
      </div>

      <div
        class="nav-item"
        :class="{ active: activeTabId === 'tutorial-content' }"
        @click="setActiveTab('tutorial-content')"
        role="tab"
        aria-controls="tutorial-content"
        :aria-selected="activeTabId === 'tutorial-content'"
      >
        <span class="nav-circle"></span>
        <span class="nav-text">实验教程</span>
      </div>
    </div>

    <div class="tab-content">
      <div
        v-if="activeTabId === 'dataset-content'"
        id="dataset-content"
        role="tabpanel"
        aria-labelledby="dataset-tab"
      >
        <div class="dataset-container">
          <DataTable
            v-if="localQuizQuestions?.length > 0"
            :tableData="localQuizQuestions"
            :runningItemId="runningItemId"
            class="data-table"
            @item-executed="handleItemExecuted"
          />
          <p v-else class="empty-message">没有 Quiz 数据可展示在表格中。</p>
        </div>
      </div>

      <div
        v-if="activeTabId === 'tutorial-content'"
        class="tab-panel"
        id="tutorial-content"
        role="tabpanel"
        aria-labelledby="tutorial-tab"
      >
        <h5 class="tutorial-title">实验教程与说明</h5>

        <p class="tutorial-intro">
          欢迎来到实验步骤 2！本步骤主要目标是熟悉数据集结构和实验流程，并为后续设计提示词做好准备。
        </p>

        <h5 class="section-title">步骤说明</h5>
        <ol class="step-list">
          <li class="step-item">
            首先，请查看本页顶部的基础知识测试得分。请注意，这个测试得分不计入最终实验成绩，仅用于帮助你了解自己的基础掌握情况。
          </li>
          <li class="step-item">
            点击 "<strong class="highlight-text">数据集</strong>"
            导航项，你将看到本次实验需要使用的数据集。
          </li>
          <li class="step-item">
            数据集中包含图像、对应的问题以及可能的选项（如果是选择题）。你需要理解这些数据的格式和内容。
          </li>
          <li class="step-item">
            请仔细查看数据集中的每一个数据项（行）。特别是图像和问题。尝试思考如何引导模型理解图像并回答问题。
          </li>
          <li class="step-item">
            当你理解了数据集和实验要求后，点击数据集表格中任意一行旁边的 "<strong
              class="highlight-text"
              >执行</strong
            >" 按钮，即可前往下一步实验流程。
          </li>
        </ol>

        <h5 class="section-title">重要提示</h5>
        <ul class="tip-list">
          <li class="tip-item">后续步骤将要求你为这些图像和问题设计有效的提示词 (Prompts)。</li>
          <li class="tip-item">一个好的图像 Caption 提示词能够准确描述图像的关键信息。</li>
          <li class="tip-item">一个好的计划提示词能够引导模型进行多步推理，最终得出正确答案。</li>
        </ul>

        <p class="tutorial-footer">
          请确保你已阅读并理解所有信息，然后点击数据集表格中任意一个 **待执行** 或 **失败**
          的实验项的"执行"按钮前往下一步。
        </p>
      </div>

      <div
        v-if="activeTabId === 'settings-content'"
        class="tab-panel"
        id="settings-content"
        role="tabpanel"
        aria-labelledby="settings-tab"
      >
        <p class="settings-message">
          这里是
          <em class="settings-highlight">自定义界面 2 (Kept hidden)</em>
          的内容。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '@/components/DataTable.vue'
import { ExperimentOutlined } from '@ant-design/icons-vue'
import { experimentApi } from '@/apis/experiment_api'

const props = defineProps({
  experimentId: {
    type: [Number, String],
    required: true
  },
  // 重新引入 quizQuestions prop，作为获取不到 recordDetails.steps_status 时的备用数据源
  quizQuestions: {
    type: Array,
    default: () => []
  }
})

const emits = defineEmits(['next', 'itemSelectedForStep3'])

const activeTabId = ref('dataset-content')
const runningItemId = ref(localStorage.getItem('runningItemId') || null)
const currentExperimentRecordId = ref(null)
const currentExperimentRecordStatus = ref(null)

const localQuizQuestions = ref([])
const isInitialLoading = ref(true)
const initialLoadError = ref(null)

const setActiveTab = (tabId) => {
  activeTabId.value = tabId
  console.log(`Switched to tab: ${tabId}`)
}

/**
 * 辅助函数：将 options 数据处理成数组
 * 可以处理 JSON 字符串或直接的对象
 * @param {string|object|null} optionsData 从后端获取的 options 数据
 * @returns {Array|null} 处理后的选项数组
 */
const processOptions = (optionsData) => {
  if (!optionsData) {
    return null
  }
  let processed = null
  if (typeof optionsData === 'string') {
    try {
      const parsed = JSON.parse(optionsData)
      if (typeof parsed === 'object' && parsed !== null) {
        processed = Object.values(parsed)
      }
    } catch (e) {
      console.error('Failed to parse options string:', optionsData, e)
    }
  } else if (typeof optionsData === 'object' && optionsData !== null) {
    processed = Object.values(optionsData)
  }
  return processed
}

// 获取实验记录详情并更新本地数据
const getExperimentDetails = async () => {
  if (!props.experimentId) {
    console.warn('No experimentId provided, cannot fetch experiment record details.')
    isInitialLoading.value = false
    return
  }

  isInitialLoading.value = true
  initialLoadError.value = null

  try {
    console.log(`Fetching experiment record details for experiment ID: ${props.experimentId}`)
    const recordDetails = await experimentApi.getExperimentRecordDetails(props.experimentId)
    console.log('Experiment Record Details received:', recordDetails)

    currentExperimentRecordId.value = recordDetails.id
    currentExperimentRecordStatus.value = recordDetails.status
    localStorage.setItem('currentExperimentRecordId', recordDetails.id)

    if (recordDetails.steps_status && recordDetails.steps_status.length > 0) {
      localQuizQuestions.value = recordDetails.steps_status.map((stepDetail) => {
        return {
          id: String(stepDetail.id),
          status: stepDetail.status || 'pending',
          result: stepDetail.score || 0,
          user_answer: stepDetail.user_answer || null,
          image_path: stepDetail.image_path || null,
          image_description:
            stepDetail.image_description !== undefined ? stepDetail.image_description : null,
          question: stepDetail.question || '',
          answer: stepDetail.answer || '',
          explanation: stepDetail.explanation || '',
          // 核心修改：使用 processOptions 函数处理 options 字段
          options: processOptions(stepDetail.options)
        }
      })
    } else {
      console.warn(
        'recordDetails.steps_status is missing or empty. Initializing localQuizQuestions from quizQuestions prop as a fallback.'
      )
      // 如果后端没有提供 steps_status，则使用 prop.quizQuestions 作为备用数据源
      localQuizQuestions.value = props.quizQuestions.map((item) => ({
        ...item,
        id: String(item.id),
        status: 'pending', // 默认状态
        result: 0,
        user_answer: null,
        // 同样使用 processOptions 处理 prop 中的 options
        options: processOptions(item.options)
      }))
    }

    isInitialLoading.value = false
    runningItemId.value = null
    localStorage.removeItem('runningItemId')
    console.log('Initial fetch complete. runningItemId cleared.')
  } catch (error) {
    console.error('Error fetching initial experiment details:', error)
    initialLoadError.value = error
    isInitialLoading.value = false
    runningItemId.value = null
    localStorage.removeItem('runningItemId')
  }
}

const handleItemExecuted = async (item) => {
  console.log(`handleItemExecuted called for item: ${item.id}`)

  if (!props.experimentId) {
    console.error('Cannot execute item: experimentId prop is missing.')
    alert('无法开始实验，实验ID缺失。') // 异常情况保留 alert
    return
  }

  try {
    // 调用后端 API，该 API 负责创建或更新单个步骤的记录，并将其状态设为 IN_PROGRESS
    console.log(
      `Calling startOrContinueExperiment with experimentId: ${props.experimentId}, step ID: ${item.id}`
    )
    const response = await experimentApi.startOrContinueExperiment(props.experimentId, item.id)
    const record = response.record // 从响应中获取实际的 record 数据
    console.log('从后端获取的 record 是:', record)

    // 将当前步骤的记录ID和状态存储起来，通常是用来追踪当前用户正在操作的步骤
    currentExperimentRecordId.value = record.id
    currentExperimentRecordStatus.value = record.status
    localStorage.setItem('currentExperimentRecordId', record.id) // 存储当前步骤的记录ID

    console.log(
      `Received Step Record for experiment ID ${props.experimentId}, step ID ${item.id}: ID=${record.id}, Status=${record.status}`
    )

    // let alertMessage = '' // 移除 alertMessage 变量，因为不再需要非异常 alert
    // 这里只检查记录的状态，因为 '执行' 按钮只代表开始/继续
    if (record.status === 'completed') {
      // alertMessage = `步骤（记录ID：${record.id}）已完成，将跳转到下一步。` // 移除此处的 alert
      console.log(`步骤（记录ID：${record.id}）已完成，将跳转到下一步。`)
    } else if (record.status === 'in_progress' || record.status === 'not_started') {
      // alertMessage = `步骤（记录ID：${record.id}）已成功开始或继续，请前往下一步。` // 移除此处的 alert
      console.log(`步骤（记录ID：${record.id}）已成功开始或继续，请前往下一步。`)

      const itemIndex = localQuizQuestions.value.findIndex((q) => q.id === item.id)
      if (itemIndex !== -1) {
        // 乐观更新当前步骤的状态，表示用户已点击执行，以便 UI 反映
        localQuizQuestions.value[itemIndex].status = 'in_progress_clicked'
        runningItemId.value = item.id
        localStorage.setItem('runningItemId', item.id)
        console.log(
          `Item ${item.id} status updated to: ${localQuizQuestions.value[itemIndex].status}, runningItemId set to: ${runningItemId.value}`
        )
      } else {
        console.warn(`Item ${item.id} not found in localQuizQuestions for optimistic update.`)
      }
    } else {
      console.warn(`Unexpected step record status: ${record.status}`)
      // alertMessage = `获取步骤记录状态异常: ${record.status}` // 移除此处的 alert
      alert(`获取步骤记录状态异常: ${record.status}`) // 异常情况保留 alert
      return
    }
    // alert(alertMessage) // 移除所有非异常情况下的 alert

    let finalItemForEmit = { ...item } // 创建 item 的副本，包含原始的步骤信息
    //     // 替换 answer 字段
    if (record.answers !== undefined && record.answers !== null) {
      finalItemForEmit.answer = record.answers
      console.log(
        `Updated item ${item.id}'s answer from backend record: ${finalItemForEmit.answer}`
      )
    } else {
      console.warn(`Backend record.answers is missing or null for item ${item.id}.`)
    }

    // 替换 explanation 字段
    if (record.explanation !== undefined && record.explanation !== null) {
      finalItemForEmit.explanation = record.explanation
      console.log(
        `Updated item ${item.id}'s explanation from backend record: ${finalItemForEmit.explanation}`
      )
    } else {
      console.warn(`Backend record.explanation is missing or null for item ${item.id}.`)
    }

    // *** 移除对 record.answers 和 record.explanation 的直接赋值 ***
    // 这些信息不应从这里的 "start" 路由获取。
    // 如果后续步骤需要正确答案或解释，应该从 getExperimentDetails 获得的 `steps_status` 中获取
    // 或者在用户提交答案后，由另一个 API（例如您未来可能会有的 "submit_answer" API）返回。

    console.log(`Calling getExperimentDetails to re-sync all step statuses.`)
    // 关键：重新调用 getExperimentDetails 来从后端获取所有步骤的最新状态和分数
    // 这将确保 DataTable 中显示的数据是最新的，并且每个步骤的状态是独立的
    await getExperimentDetails()

    console.log(
      `getExperimentDetails completed. Final localQuizQuestions for item ${item.id} status:`,
      localQuizQuestions.value.find((q) => q.id === item.id)?.status
    )

    // 触发事件，传递给父组件当前选中的步骤信息
    emits('itemSelectedForStep3', {
      ...finalItemForEmit, // 包含步骤的原始信息 (question, options, etc.)
      recordId: record.id, // 当前步骤的记录ID (由后端 start_or_continue_step 返回)
      recordStatus: record.status, // 当前步骤的记录状态
      selectedStepId: item.id,
      userId: record.user_id,
      experimentId: record.experiment_id
    })
    emits('next') // 导航到下一步
  } catch (error) {
    console.error(
      `Error starting/continuing step for ID ${props.experimentId}, step ID ${item.id}:`,
      error
    )
    alert(`开始/继续步骤失败: ${error.message}`) // 异常情况保留 alert
    runningItemId.value = null
    localStorage.removeItem('runningItemId')
  }
}
onMounted(() => {
  // 组件挂载时，获取实验记录详情
  getExperimentDetails()
})
</script>

<style scoped>
/* 样式代码保持不变 */
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

/* 加载和错误状态样式 */
.loading-container {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.error-container {
  margin: 20px 0;
}

.retry-btn {
  margin-left: 16px;
}

/* 导航标签样式 */
.nav-tabs {
  display: flex;
  align-items: center;
  margin-top: 24px;
  margin-bottom: 32px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
  user-select: text;
}

.nav-item {
  display: flex;
  align-items: center;
  position: relative;
  padding: 8px 0;
  margin-right: 64px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: text;
}

.nav-item.active {
  color: #1890ff;
  font-weight: 600;
}

.nav-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-item {
  margin-left: 8px;
}

.nav-circle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #d9d9d9;
  margin-right: 8px;
  display: inline-block;
}

.nav-item.active .nav-circle {
  background-color: #1890ff;
}

.nav-text {
  font-size: 16px;
  user-select: text;
}

.progress-container {
  display: flex;
  align-items: center;
  margin-left: auto;
  flex: 1;
}

/* 内容面板样式 */
.tab-content {
  user-select: text;
}

.tab-panel {
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  background-color: #fff;
  user-select: text;
}

/* 数据集面板样式 */
.dataset-container {
  margin-top: 0;
  user-select: text;
}

.data-table {
  width: 100%;
  user-select: text;
}

.data-table :deep(table) {
  user-select: text;
}

.data-table :deep(td),
.data-table :deep(th) {
  user-select: text;
}

.empty-message {
  color: #8c8c8c;
  text-align: center;
  padding: 24px;
  user-select: text;
}

/* 教程面板样式 */
.tutorial-title {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  user-select: text;
}

.tutorial-intro {
  margin-top: 8px;
  margin-bottom: 24px;
  color: #595959;
  line-height: 1.6;
  user-select: text;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin-top: 24px;
  margin-bottom: 8px;
  user-select: text;
}

.step-list {
  list-style-type: decimal;
  padding-left: 24px;
  margin-bottom: 24px;
  color: #595959;
  user-select: text;
}

.step-item {
  margin-bottom: 8px;
  line-height: 1.6;
  user-select: text;
}

.tip-list {
  list-style-type: disc;
  padding-left: 24px;
  margin-bottom: 24px;
  color: #595959;
  user-select: text;
}

.tip-item {
  margin-bottom: 8px;
  line-height: 1.6;
  user-select: text;
}

.highlight-text {
  font-weight: 600;
  color: #262626;
  user-select: text;
}

.tutorial-footer {
  margin-top: 24px;
  color: #595959;
  line-height: 1.6;
  user-select: text;
}

/* 设置面板样式 */
.settings-message {
  color: #8c8c8c;
  user-select: text;
}

.settings-highlight {
  font-weight: 600;
  color: #262626;
  user-select: text;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .nav-tabs {
    flex-wrap: wrap;
  }

  .nav-item {
    margin-right: 24px;
    margin-bottom: 8px;
  }

  .progress-container {
    width: 100%;
    margin-top: 16px;
    margin-left: 0;
  }
}
</style>
