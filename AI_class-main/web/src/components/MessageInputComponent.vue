<template>
  <div class="input-box" :class="customClasses" @click="focusInput">
    <div class="input-area">
      <a-textarea
        ref="inputRef"
        class="user-input"
        v-model:value="inputValue"
        @keydown="handleKeyPress"
        :placeholder="placeholder"
        :disabled="disabled"
        :auto-size="autoSize"
      />
    </div>
    <div class="input-options">
      <div class="options__left">
        <slot name="options-left"></slot>
      </div>
      <div class="options__right">
        <a-tooltip :title="isLoading ? '停止回答' : ''">
          <a-button @click="handleSendOrStop" :disabled="sendButtonDisabled" type="link">
            <template #icon>
              <component :is="getIcon" class="send-btn" />
            </template>
          </a-button>
        </a-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, toRefs, onMounted } from 'vue'
import {
  SendOutlined,
  ArrowUpOutlined,
  LoadingOutlined,
  PauseOutlined
} from '@ant-design/icons-vue'

const inputRef = ref(null)
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '输入问题...'
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  sendButtonDisabled: {
    type: Boolean,
    default: false
  },
  autoSize: {
    type: Object,
    default: () => ({ minRows: 2, maxRows: 6 })
  },
  sendIcon: {
    type: String,
    default: 'ArrowUpOutlined'
  },
  customClasses: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'keydown'])

// 图标映射
const iconComponents = {
  SendOutlined: SendOutlined,
  ArrowUpOutlined: ArrowUpOutlined,
  PauseOutlined: PauseOutlined
}

// 根据传入的图标名动态获取组件
const getIcon = computed(() => {
  if (props.isLoading) {
    return PauseOutlined
  }
  return iconComponents[props.sendIcon] || ArrowUpOutlined
})

// 创建本地引用以进行双向绑定
const inputValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 处理键盘事件
const handleKeyPress = (e) => {
  emit('keydown', e)
}

// 处理发送按钮点击
const handleSendOrStop = () => {
  emit('send')
}

// 聚焦输入框
const focusInput = () => {
  if (inputRef.value && !props.disabled) {
    inputRef.value.focus()
  }
}

// Wait for component to mount before setting up onStartTyping
onMounted(() => {
  // Use the template ref element for onStartTyping
  setTimeout(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  }, 100)
})
</script>

<style lang="less" scoped>
.input-box {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: auto;
  margin: 0 auto;
  padding: 0.5rem 0.85rem;
  border: 2px solid var(--gray-200);
  border-radius: 1rem;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);

  &:focus-within {
    border-color: var(--main-500);
    background: white;
    box-shadow: 0 6px 16px rgba(22, 119, 255, 0.12);
    transform: translateY(-1px);
  }

  .input-area {
    display: flex;
    align-items: flex-end;
    gap: 8px;
  }

  .user-input {
    flex: 1;
    min-height: 44px;
    padding: 0.5rem 0;
    background-color: transparent;
    border: none;
    margin: 0;
    color: #222222;
    font-size: 15px;
    outline: none;
    resize: none;
    line-height: 1.6;

    &:focus {
      outline: none;
      box-shadow: none;
    }

    &:active {
      outline: none;
    }

    &::placeholder {
      color: #888888;
      opacity: 0.8;
      transition: opacity 0.3s ease;
    }

    &:focus::placeholder {
      opacity: 0.5;
    }
  }

  .input-options {
    display: flex;
    padding: 10px 0 0;
    border-top: 1px solid var(--gray-100);

    .options__left,
    .options__right {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .options__right {
      width: fit-content;
    }

    .options__left {
      flex: 1;

      :deep(.opt-item) {
        border-radius: 12px;
        border: 1px solid var(--gray-300);
        padding: 5px 12px;
        cursor: pointer;
        font-size: 12px;
        color: var(--gray-700);
        transition: all 0.25s ease;
        background-color: rgba(255, 255, 255, 0.8);

        &:hover {
          background-color: var(--main-10);
          color: var(--main-600);
          border-color: var(--main-300);
          transform: translateY(-1px);
          box-shadow: 0 2px 6px rgba(22, 119, 255, 0.1);
        }

        &.active {
          color: var(--main-600);
          border: 1px solid var(--main-500);
          background-color: var(--main-10);
          box-shadow: 0 2px 6px rgba(22, 119, 255, 0.1);
        }
      }
    }
  }
}

button.ant-btn-icon-only {
  height: 36px;
  width: 36px;
  cursor: pointer;
  background: linear-gradient(135deg, #1677ff, #06b6d4);
  border-radius: 50%;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 3px 8px rgba(22, 119, 255, 0.25);
  color: white;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;

  &:hover {
    background: linear-gradient(135deg, #0958d9, #08a5c0);
    box-shadow: 0 5px 12px rgba(22, 119, 255, 0.35);
    transform: translateY(-2px);
    color: white;
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(22, 119, 255, 0.2);
  }

  &:disabled {
    background: linear-gradient(135deg, #bfbfbf, #d9d9d9);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
}

@media (max-width: 520px) {
  .input-box {
    border-radius: 15px;
    padding: 0.625rem 0.875rem;
  }
}
</style>
