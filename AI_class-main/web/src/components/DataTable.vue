<template>
  <div class="p-6 bg-gray-100 min-h-screen dark:bg-gray-900 integrated-data-table-container">
    <h6 class="text-lg font-bold mb-4 text-gray-800 dark:text-white">实验数据集</h6>

    <div class="relative overflow-x-auto shadow-md sm:rounded-lg">
      <table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 custom-table">
        <thead
          class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400"
        >
          <tr>
            <th scope="col" class="px-6 py-3 w-[240px]">图片</th>
            <th scope="col" class="px-6 py-3 w-auto">问题</th>
            <th scope="col" class="px-6 py-3 w-[200px]">选项</th>
            <th scope="col" class="px-6 py-3 w-[140px]">分数</th>
            <th scope="col" class="px-6 py-3 w-[100px]">状态</th>
            <th scope="col" class="px-6 py-3 w-[120px]">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in tableData"
            :key="item.id"
            class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          >
            <th scope="row" class="px-6 py-4 font-medium text-gray-900 dark:text-white image-cell">
              <div class="cell-content-wrapper">
                <img
                  v-if="item.image_path"
                  :src="item.image_path"
                  alt="Image for question"
                  class="table-image w-[160px] h-auto object-cover rounded"
                />
                <span v-else class="no-image-placeholder">无图片</span>
              </div>
            </th>

            <td class="px-6 py-4 question-cell">
              <div class="cell-content-wrapper">
                <p
                  class="mb-3 text-gray-500 dark:text-gray-400 whitespace-normal overflow-hidden text-ellipsis question-text"
                >
                  {{ item.question }}
                </p>
              </div>
            </td>

            <td class="px-6 py-4 options-list-cell">
              <div class="cell-content-wrapper">
                <ul
                  v-if="item.options && item.options.length > 0"
                  class="list-disc pl-5 options-list"
                >
                  <li v-for="(option, index) in item.options" :key="index" class="mb-1 option-item">
                    <span class="option-text">{{ option }}</span>
                  </li>
                </ul>
                <span
                  v-else
                  class="text-gray-400 dark:text-gray-500 text-xs no-options-placeholder"
                >
                  无选项
                </span>
              </div>
            </td>

            <td class="px-6 py-4 evaluation-cell">
              <div class="cell-content-wrapper">
                <p class="text-gray-700 dark:text-neutral-300">
                  {{ item.result || '请先完成该项实验' }}
                </p>
              </div>
            </td>

            <td class="px-6 py-4 status-cell">
              <div class="cell-content-wrapper">
                <span
                  :class="{
                    'status-completed': item.status === 'completed',
                    'status-in-progress': item.status === 'in_progress',
                    'status-failed': item.status === 'failed',
                    'status-pending': item.status === 'pending' || !item.status
                  }"
                >
                  {{
                    item.status === 'completed'
                      ? '已完成'
                      : item.status === 'in_progress'
                        ? '执行中'
                        : item.status === 'failed'
                          ? '失败'
                          : '待执行'
                  }}
                </span>
              </div>
            </td>

            <td class="px-6 py-4 actions-cell">
              <div class="cell-content-wrapper">
                <button
                  @click="emitItemExecuted(item)"
                  type="button"
                  class="action-button"
                  :disabled="item.status === 'completed'"
                  aria-label="执行实验"
                >
                  {{ item.status === 'in_progress' ? '继续' : '执行' }}
                </button>
                <span
                  v-if="item.status === 'completed' && item.result !== null"
                  class="ml-2 font-bold text-gray-800 dark:text-neutral-200"
                >
                </span>
              </div>
            </td>
          </tr>
          <tr v-if="!tableData || tableData.length === 0">
            <td
              colspan="6"
              class="px-6 py-4 text-center text-gray-500 dark:text-gray-400 no-data-row"
            >
              没有数据可展示。
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, onMounted } from 'vue'

const props = defineProps({
  tableData: {
    type: Array,
    default: () => []
  },
  runningItemId: {
    type: [String, Number, null],
    default: null
  }
})

const emits = defineEmits(['itemExecuted'])

onMounted(() => {
  console.log('DataTable mounted.')
  console.log('DataTable received tableData:', props.tableData)
  console.log('DataTable received runningItemId:', props.runningItemId)
})

const emitItemExecuted = (item) => {
  console.log('emitItemExecuted function called for item:', item.id)
  console.log('DataTable button clicked for item:', item.id)
  // 仅在非完成状态下触发事件
  if (item.status !== 'completed') {
    emits('itemExecuted', item)
    console.log('emits("itemExecuted", item) called.')
  } else {
    console.log('Item is already completed, ignoring click.')
  }
}
</script>

<style scoped>
/* --- CSS 样式保持不变 --- */
/* Your existing styles below */
.integrated-data-table-container {
  background-color: #f3f4f6;
  /* bg-gray-100 */
  min-height: 100vh;
  padding: 1.5rem;
  /* p-6 */
}

.dark:bg-gray-900 {
  /* dark mode styles */
}

.text-lg {
  font-size: 1.125rem;
  /* 18px */
}

.font-bold {
  font-weight: 700;
}

.mb-4 {
  margin-bottom: 1rem;
  /* 16px */
}

.text-gray-800 {
  color: #1f2937;
}

.dark:text-white {
  /* dark mode styles */
}

.relative {
  position: relative;
}

.overflow-x-auto {
  overflow-x: auto;
}

.shadow-md {
  box-shadow:
    0 4px 6px -1px rgb(0 0 0 / 0.1),
    0 2px 4px -2px rgb(0 0 0 / 0.1);
}

.sm:rounded-lg {
  border-radius: 0.5rem;
  /* 8px */
}

.custom-table {
  min-width: 100%;
  /* Ensure table doesn't shrink too much */
}

.text-sm {
  font-size: 0.875rem;
  /* 14px */
}

.text-left {
  text-align: left;
}

.text-gray-500 {
  color: #6b7280;
}

.dark:text-gray-400 {
  /* dark mode styles */
}

.text-xs {
  font-size: 0.75rem;
  /* 12px */
}

.text-gray-700 {
  color: #374151;
}

.uppercase {
  text-transform: uppercase;
}

.bg-gray-50 {
  background-color: #f9fafb;
}

.dark:bg-gray-700 {
  /* dark mode styles */
}

.dark:text-gray-400 {
  /* dark mode styles */
}

th,
td {
  padding: 0.75rem 1.5rem;
  /* px-6 py-3/4 */
}

.bg-white {
  background-color: #fff;
}

.border-b {
  border-bottom-width: 1px;
  border-color: #e5e7eb;
  /* border-gray-200 */
}

.dark:bg-gray-800 {
  /* dark mode styles */
}

.dark:border-gray-700 {
  /* dark mode styles */
}

.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

.dark\:hover\:bg-gray-600:hover {
  /* dark mode styles */
}

/* Original image size, changed to w-[160px] in template */
/* .w-24 { width: 6rem; } */
/* .h-24 { height: 6rem; } */
.object-cover {
  object-fit: cover;
}

.rounded-md {
  border-radius: 0.375rem;
  /* 6px */
}

.font-medium {
  font-weight: 500;
}

.text-gray-900 {
  color: #111827;
}

.whitespace-pre-wrap {
  white-space: pre-wrap;
}

.dark:text-white {
  /* dark mode styles */
}

.list-disc {
  list-style-type: disc;
}

.list-inside {
  list-style-position: inside;
}

.text-right {
  text-align: right;
}

.text-blue-600 {
  color: #2563eb;
}

.dark:text-blue-500 {
  /* dark mode styles */
}

.hover\:underline:hover {
  text-decoration-line: underline;
}

/* Status colors */
.text-blue-500 {
  color: #3b82f6;
}

.text-yellow-500 {
  color: #f59e0b;
}

.text-green-500 {
  color: #22c55e;
}

.text-red-500 {
  color: #ef4444;
}

/* --- 表格单元格内容对齐修复 (主要依赖 Flexbox Wrapper) --- */
.custom-table th,
.custom-table td {
  word-break: break-word;
  border: 1px solid #e5e7eb;
  /* border-gray-200 */
  padding: 16px 24px !important;
  /* px-6 py-4 */
  display: table-cell;
  /* 确保行为像表格单元格 */
  vertical-align: middle !important;
  /* 默认垂直居中 */
  text-align: left;
  /* Default text align for cells */
}

.dark .custom-table th,
.dark .custom-table td {
  border-color: #4b5563 !important;
  /* dark:border-gray-600 */
}

/* 表格整体样式增强 */
.custom-table {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  border: 1px solid #eaeaea !important;
  transition: all 0.3s ease !important;
}

/* 表头样式优化 */
.custom-table thead {
  background: linear-gradient(to right, #f0f5ff, #e6f7ff) !important;
  color: #1a1a1a !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}

.custom-table thead th {
  padding: 14px 16px !important;
  font-size: 15px !important;
  border-bottom: 2px solid #d9e6ff !important;
}

/* 表格行样式优化 */
.custom-table tbody tr {
  transition: all 0.2s ease-in-out !important;
  border-bottom: 1px solid #f0f0f0 !important;
}

.custom-table tbody tr:hover {
  background-color: #f5f9ff !important;
  transform: translateY(-1px) !important;
}

/* 表格单元格样式优化 */
.custom-table td {
  padding: 16px !important;
  vertical-align: middle !important;
  font-size: 14px !important;
  color: #333 !important;
  line-height: 1.6 !important;
}

/* 调整问题列宽度 */
.custom-table th.question-header,
.custom-table td.question-cell {
  width: 25% !important;
  /* 减小问题栏目宽度，原来是 30% */
  max-width: 25% !important;
}

/* 调整选项列宽度 */
.custom-table th.options-header,
.custom-table td.options-list-cell {
  width: 25% !important;
  /* 增加选项栏目宽度，给更多空间 */
}

/* 问题单元格内容样式优化 */
.question-cell .cell-content-wrapper p {
  font-weight: 500 !important;
  color: #262626 !important;
  margin-bottom: 0 !important;
  line-height: 1.5 !important;
}

/* 选项列表样式优化 */
.custom-table td.options-list-cell ul.options-list li.option-item {
  margin-bottom: 8px !important;
  padding: 4px 0 !important;
  color: #444 !important;
}

/*
.custom-table td.options-list-cell ul.options-list li.option-item::before {
  content: '•' !important;
  color: #1890ff !important;
  font-size: 18px !important;
  line-height: 1 !important;
  margin-right: 10px !important;
}
*/

/* 图片单元格样式优化 */
.image-cell .cell-content-wrapper {
  padding: 4px !important;
}

.table-image {
  border-radius: 6px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  transition: transform 0.3s ease !important;
}

.table-image:hover {
  transform: scale(1.02) !important;
}

/* 分数单元格样式优化 */
.evaluation-cell p {
  font-weight: 600 !important;
  font-size: 16px !important;
  color: #1890ff !important;
}

/* 状态单元格样式优化 */
.status-cell span {
  padding: 4px 12px !important;
  border-radius: 12px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  display: inline-block !important;
}

.status-cell span.status-pending {
  background-color: #f5f5f5 !important;
  color: #8c8c8c !important;
}

.status-cell span.status-in-progress {
  background-color: #e6f7ff !important;
  color: #1890ff !important;
}

.status-cell span.status-completed {
  background-color: #f6ffed !important;
  color: #52c41a !important;
}

.status-cell span.status-failed {
  background-color: #fff2f0 !important;
  color: #ff4d4f !important;
}

/* 按钮样式优化 */
.custom-table button.action-button {
  background: linear-gradient(to right, #1890ff, #40a9ff) !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 8px 16px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2) !important;
}

.custom-table button.action-button:hover:not(:disabled) {
  background: linear-gradient(to right, #096dd9, #1890ff) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3) !important;
}

.custom-table button.action-button:active:not(:disabled) {
  transform: translateY(1px) !important;
}

/* 暗黑模式优化 */
.dark .custom-table {
  border-color: #303030 !important;
}

.dark .custom-table thead {
  background: linear-gradient(to right, #1f1f1f, #2d3748) !important;
  color: #e2e8f0 !important;
  border-bottom-color: #4a5568 !important;
}

.dark .custom-table tbody tr {
  border-bottom-color: #383838 !important;
}

.dark .custom-table tbody tr:hover {
  background-color: #2d3748 !important;
}

.dark .custom-table td {
  color: #e2e8f0 !important;
}

.dark .question-cell .cell-content-wrapper p {
  color: #e2e8f0 !important;
}

.dark .custom-table td.options-list-cell ul.options-list li.option-item {
  color: #cbd5e0 !important;
}

.dark .custom-table td.options-list-cell ul.options-list li.option-item::before {
  color: #63b3ed !important;
}

.dark .evaluation-cell p {
  color: #63b3ed !important;
}

.dark .status-cell span.status-pending {
  background-color: #2d3748 !important;
  color: #a0aec0 !important;
}

.dark .status-cell span.status-in-progress {
  background-color: #2a4365 !important;
  color: #63b3ed !important;
}

.dark .status-cell span.status-completed {
  background-color: #22543d !important;
  color: #68d391 !important;
}

.dark .status-cell span.status-failed {
  background-color: #742a2a !important;
  color: #fc8181 !important;
}

.dark .custom-table button.action-button {
  background: linear-gradient(to right, #3182ce, #4299e1) !important;
  box-shadow: 0 2px 6px rgba(49, 130, 206, 0.3) !important;
}

.dark .custom-table button.action-button:hover:not(:disabled) {
  background: linear-gradient(to right, #2b6cb0, #3182ce) !important;
  box-shadow: 0 4px 8px rgba(49, 130, 206, 0.4) !important;
}

.whitespace-normal {
  white-space: normal;
}

/* Dark mode basic table structure styles */
.dark .custom-table thead {
  background-color: #4a5568 !important;
  color: #a0aec0 !important;
}

.dark .custom-table tbody tr {
  background-color: #2d3748 !important;
  border-color: #4b5563 !important;
}

.dark .custom-table th[scope='row'] {
  color: #ffffff !important;
}

.custom-table td.no-data-row {
  color: #6b7280 !important;
}

.dark .custom-table td.no-data-row {
  color: #9ca3af !important;
}

/* --- 图片大小 (与之前相同) --- */
.table-image {
  max-width: 160px !important;
  height: auto !important;
  object-fit: cover !important;
  margin: 0 !important;
  padding: 0 !important;
}

.custom-table img {
  max-width: 160px !important;
  width: auto !important;
  height: auto !important;
  object-fit: cover !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* --- 按钮样式 (与之前相同) --- */
.custom-table button.action-button {
  outline: none !important;
  box-shadow: none !important;
  display: inline-flex !important;
  align-items: center !important;
  color: #ffffff !important;
  background-color: #2563eb !important;
  padding: 8px 16px !important;
  font-size: 0.875rem !important;
  line-height: 1.25rem !important;
  border-radius: 0.5rem !important;
  text-align: center !important;
  transition:
    background-color 0.2s ease,
    opacity 0.2s ease;

  position: static !important;
  float: none !important;
  margin: 0 !important;
}

.custom-table button.action-button:hover:not(:disabled) {
  background-color: #1d4ed8 !important;
}

.custom-table button.action-button:focus {
  outline: none !important;
  box-shadow: none !important;
}

.dark .custom-table button.action-button {
  background-color: #3b82f6 !important;
}

.dark .custom-table button.action-button:hover:not(:disabled) {
  background-color: #2563eb !important;
}

.dark .custom-table button.action-button:focus {
  outline: none !important;
  box-shadow: none !important;
}

.custom-table button.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  /* 增加禁用时的视觉反馈 */
}

/* Score span color */
.evaluation-cell p {
  color: #1f2937 !important;
}

.dark .evaluation-cell p {
  color: #ffffff !important;
}

/* Status cell text color is handled by binding in template */
.status-cell span {
  font-weight: bold;
}
</style>
