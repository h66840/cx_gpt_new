<template>
  <div class="message-box" :class="[message.role, customClasses]">
    <!-- 用户消息 -->
    <div v-if="message.role === 'user' || message.role === 'sent'" class="user-message-container">
      <p class="message-text">
        {{ message.content }}
      </p>
      <div class="user-avatar">
        <CircleUser size="34" strokeWidth="1.5" class="user-icon" />
      </div>
    </div>

    <!-- 助手消息 -->
    <div
      v-else-if="message.role === 'assistant' || message.role === 'received'"
      class="assistant-message"
    >
      <div class="ai-avatar">
        <Bot size="34" strokeWidth="1.5" class="bot-icon" />
      </div>

      <!-- 推理过程 (ChatComponent特有) -->
      <div class="message-content">
        <p v-if="debugMode">
          {{ message.status }}
        </p>
        <div v-if="message.reasoning_content" class="reasoning-box">
          <a-collapse
            v-model:activeKey="reasoningActiveKey"
            :bordered="false"
            class="custom-collapse"
          >
            <template #expandIcon="{ isActive }">
              <caret-right-outlined
                :rotate="isActive ? 90 : 0"
                style="color: var(--main-600); font-size: 12px"
              />
            </template>
            <a-collapse-panel
              key="show"
              :header="message.status == 'reasoning' ? '正在思考...' : '推理过程'"
              class="reasoning-header"
            >
              <p class="reasoning-content">{{ message.reasoning_content.trim() }}</p>
            </a-collapse-panel>
          </a-collapse>
        </div>

        <!-- 加载中状态 -->
        <div v-if="isEmptyAndLoading" class="loading-dots">
          <div></div>
          <div></div>
          <div></div>
        </div>

        <!-- 检索中状态 (ChatComponent特有) -->
        <div v-else-if="message.status === 'searching' && isProcessing" class="searching-msg">
          <i>正在检索……</i>
        </div>

        <!-- 生成中状态 (ChatComponent特有) -->
        <div v-else-if="message.status === 'generating' && isProcessing" class="searching-msg">
          <i>正在生成……</i>
        </div>

        <div v-else-if="message.status === 'error'" class="err-msg" @click="$emit('retry')">
          请求错误，请重试。{{ message.message }}
        </div>

        <!-- 消息内容 -->
        <!-- <div v-else-if="message.content" v-html="renderMarkdown(message)" class="message-md"></div> -->
        <MdPreview
          v-else-if="message.content"
          ref="editorRef"
          editorId="preview-only"
          previewTheme="github"
          :showCodeRowNumber="false"
          :modelValue="message.content"
          :key="message.id"
          class="message-md"
        />

        <div v-else-if="message.reasoning_content" class="empty-block"></div>

        <!-- 工具调用 (AgentView特有) -->
        <slot
          v-else-if="message.toolCalls && Object.keys(message.toolCalls).length > 0"
          name="tool-calls"
        ></slot>

        <div v-else-if="!isProcessing" class="err-msg" @click="$emit('retry')">
          请求错误，请重试。{{ message.message }}
        </div>

        <div v-if="message.isStoppedByUser" class="retry-hint">
          你停止生成了本次回答
          <span class="retry-link" @click="emit('retryStoppedMessage', message.id)"
            >重新编辑问题</span
          >
        </div>

        <div
          v-if="
            (message.role == 'received' || message.role == 'assistant') &&
            message.status == 'finished' &&
            showRefs
          "
        >
          <RefsComponent
            :message="message"
            :show-refs="showRefs"
            :is-latest-message="isLatestMessage"
            @retry="emit('retry')"
            @openRefs="emit('openRefs', $event)"
          />
        </div>
      </div>
      <!-- 错误消息 -->
    </div>

    <!-- 自定义内容 -->
    <slot></slot>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CaretRightOutlined } from '@ant-design/icons-vue'
import RefsComponent from '@/components/RefsComponent.vue'
import { Bot, CircleUser } from 'lucide-vue-next'

import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'

const props = defineProps({
  // 消息角色：'user'|'assistant'|'sent'|'received'
  message: {
    type: Object,
    required: true
  },
  // 是否正在处理中
  isProcessing: {
    type: Boolean,
    default: false
  },
  // 自定义类
  customClasses: {
    type: Object,
    default: () => ({})
  },
  // 是否显示推理过程
  showRefs: {
    type: [Array, Boolean],
    default: () => false
  },
  debugMode: {
    type: Boolean,
    default: false
  },
  // 是否为最新消息
  isLatestMessage: {
    type: Boolean,
    default: false
  }
})

const editorRef = ref()
const statusDefination = {
  init: '初始化',
  loading: '加载中',
  reasoning: '推理中',
  generating: '生成中',
  error: '错误'
}

const emit = defineEmits(['retry', 'retryStoppedMessage', 'openRefs'])

// 推理面板展开状态
const reasoningActiveKey = ref(['show'])

// 计算属性：内容为空且正在加载
const isEmptyAndLoading = computed(() => {
  const isEmpty = !props.message.content || props.message.content.length === 0
  const isLoading = props.message.status === 'init' && props.isProcessing
  return isEmpty && isLoading
})
</script>

<style lang="less" scoped>
.message-box {
  // 在组件根元素上定义变量
  --message-primary: #1677ff;
  --message-primary-light: #e6f4ff;
  --message-gradient: linear-gradient(135deg, #1677ff, #06b6d4);
  --message-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --message-radius: 12px;
  --message-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --message-error: #f5222d;
  --message-error-light: #fff1f0;
  --avatar-bg-user: #1677ff;
  --avatar-bg-bot: #10b981;
  --avatar-size: 36px;

  display: inline-block;
  margin: 1rem 0;
  user-select: text;
  word-break: break-word;
  word-wrap: break-word;
  font-size: 15px;
  line-height: 1.6;
  box-sizing: border-box;
  color: var(--gray-900);
  max-width: 100%;
  position: relative;
  letter-spacing: 0.25px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInUp 0.3s ease-out;

  .user-message-container {
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
    gap: 12px;
    max-width: 95%;
    margin-left: auto;
  }

  .user-avatar,
  .ai-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: scale(1.05);
    }
  }

  .user-avatar {
    color: #1677ff;
  }

  .ai-avatar {
    color: #10b981;
  }

  &.user,
  &.sent {
    .message-text {
      color: white;
      background: var(--message-gradient, var(--main-color));
      border-radius: 18px 18px 4px 18px;
      padding: 0.75rem 1.25rem;
      box-shadow: var(--message-shadow);
      margin: 0;
    }
  }

  &.assistant,
  &.received {
    color: initial;
    width: 100%;
    text-align: left;
    margin: 0 0 20px 0;
    padding: 0px;
    background-color: transparent;
    border-radius: 0;

    .assistant-message {
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }

    .message-content {
      flex: 1;
      max-width: calc(100% - var(--avatar-size) - 12px);
    }
  }

  .message-text {
    max-width: 100%;
    margin-bottom: 0;
    white-space: pre-line;
    font-weight: 400;
  }

  .err-msg {
    color: var(--message-error);
    border: 1px solid rgba(245, 34, 45, 0.2);
    padding: 0.75rem 1.25rem;
    border-radius: var(--message-radius);
    text-align: left;
    background: var(--message-error-light);
    margin-bottom: 12px;
    cursor: pointer;
    transition: var(--message-transition);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);

    &:hover {
      border-color: rgba(245, 34, 45, 0.4);
      box-shadow: 0 2px 8px rgba(245, 34, 45, 0.1);
    }
  }

  .searching-msg {
    color: var(--gray-700);
    animation: colorPulse 1.2s infinite ease-in-out;
    padding: 0.5rem 0;
    font-style: italic;
    display: flex;
    align-items: center;
    gap: 8px;

    &::before {
      content: '';
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      border: 2px solid var(--gray-300);
      border-top-color: var(--gray-700);
      animation: spin 1s linear infinite;
    }
  }

  .reasoning-box {
    margin-top: 12px;
    margin-bottom: 16px;
    border-radius: var(--message-radius);
    border: 1px solid var(--main-light-3);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    overflow: hidden;
    transition: var(--message-transition);

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .reasoning-content {
      font-size: 13px;
      color: var(--gray-800);
      white-space: pre-wrap;
      margin: 0;
      padding: 12px 16px;
      line-height: 1.5;
      background-color: rgba(0, 0, 0, 0.01);
    }
  }

  .assistant-message {
    width: 100%;
  }

  .status-info {
    display: block;
    background-color: var(--gray-50);
    color: var(--gray-700);
    padding: 12px;
    border-radius: var(--message-radius);
    margin-bottom: 12px;
    font-size: 12px;
    font-family: monospace;
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid var(--gray-100);
  }

  :deep(.tool-calls-container) {
    width: 100%;
    margin-top: 12px;

    .tool-call-container {
      margin-bottom: 12px;
      transition: var(--message-transition);

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  :deep(.tool-call-display) {
    background-color: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: var(--message-radius);
    overflow: hidden;
    transition: var(--message-transition);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .tool-header {
      padding: 12px 16px;
      background-color: var(--gray-100);
      font-size: 14px;
      font-weight: 500;
      color: var(--gray-800);
      border-bottom: 1px solid var(--gray-200);
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      user-select: none;
      position: relative;
      transition: var(--message-transition);

      &:hover {
        background-color: var(--gray-50);
      }

      .anticon {
        color: var(--main-600);
        transition: transform 0.2s ease;
      }

      .step-badge {
        margin-left: auto;
        background-color: var(--gray-200);
        color: var(--gray-700);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        transition: var(--message-transition);
      }
    }

    .tool-content {
      transition: all 0.3s ease;

      .tool-params {
        padding: 12px 16px;
        background-color: var(--gray-50);

        .tool-params-header {
          background-color: var(--gray-100);
          font-size: 13px;
          color: var(--gray-800);
          padding: 8px 12px;
          border-radius: 6px 6px 0 0;
          font-weight: 500;
        }

        .tool-params-content {
          margin: 0;
          font-size: 13px;
          background-color: var(--gray-100);
          border-radius: 0 0 6px 6px;
          padding: 10px 12px;
          overflow-x: auto;
          line-height: 1.5;
        }
      }
    }

    &.is-collapsed {
      .tool-header {
        border-bottom: none;

        .anticon {
          transform: rotate(-90deg);
        }
      }
    }
  }
}

.retry-hint {
  margin-top: 10px;
  padding: 10px 16px;
  color: var(--gray-600);
  font-size: 14px;
  text-align: left;
  background-color: var(--gray-50);
  border-radius: var(--message-radius);
  border: 1px solid var(--gray-100);
}

.retry-link {
  color: var(--message-primary);
  cursor: pointer;
  margin-left: 4px;
  font-weight: 500;
  transition: var(--message-transition);

  &:hover {
    text-decoration: underline;
    color: var(--main-600);
  }
}

.ant-btn-icon-only {
  &:has(.anticon-stop) {
    background-color: var(--message-error) !important;
    transition: var(--message-transition);

    &:hover {
      background-color: #ff7875 !important;
      transform: translateY(-1px);
    }

    &:active {
      transform: translateY(0);
    }
  }
}

.loading-dots {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;

  div {
    width: 8px;
    height: 8px;
    margin: 0 4px;
    background-color: var(--message-primary, var(--gray-700));
    border-radius: 50%;
    opacity: 0.3;
    animation: pulse 0.6s infinite ease-in-out both;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }

    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes colorPulse {
  0% {
    color: var(--gray-700);
  }

  50% {
    color: var(--gray-400);
  }

  100% {
    color: var(--gray-700);
  }
}

@keyframes pulse {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.3;
  }

  40% {
    transform: scale(1);
    opacity: 0.8;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

<style lang="less">
.message-md .md-editor-preview-wrapper {
  color: var(--gray-900);
  max-width: 100%;
  padding: 0;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Noto Sans SC', 'PingFang SC', 'Noto Sans SC',
    'Microsoft YaHei', 'Hiragino Sans GB', 'Source Han Sans CN', 'Courier New', monospace;

  #preview-only-preview {
    font-size: 15px;
  }

  h1,
  h2 {
    font-size: 1.2rem;
  }

  h3,
  h4 {
    font-size: 1.1rem;
  }

  h5,
  h6 {
    font-size: 1rem;
  }

  a {
    color: var(--main-700);
  }

  code {
    font-size: 13px;
    font-family:
      'Menlo', 'Monaco', 'Consolas', 'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei',
      'Hiragino Sans GB', 'Source Han Sans CN', 'Courier New', monospace;
    line-height: 1.5;
    letter-spacing: 0.025em;
    tab-size: 4;
    -moz-tab-size: 4;
    background-color: var(--gray-100);
  }
}

.chat-box.font-smaller #preview-only-preview {
  font-size: 14px;

  h1,
  h2 {
    font-size: 1.1rem;
  }

  h3,
  h4 {
    font-size: 1rem;
  }
}

.chat-box.font-larger #preview-only-preview {
  font-size: 16px;

  h1,
  h2 {
    font-size: 1.3rem;
  }

  h3,
  h4 {
    font-size: 1.2rem;
  }

  h5,
  h6 {
    font-size: 1.1rem;
  }

  code {
    font-size: 14px;
  }
}
</style>
