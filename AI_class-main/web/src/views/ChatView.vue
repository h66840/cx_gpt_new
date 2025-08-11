<template>
  <div class="chat-container">
    <div class="conversations" :class="{ 'is-open': state.isSidebarOpen }">
      <div class="actions">
        <!-- <div class="action new" @click="addNewConv"><FormOutlined /></div> -->
        <span class="header-title">AI助教</span>
        <div class="action close" @click="state.isSidebarOpen = false">
          <PanelLeftClose size="20" color="#595959" />
        </div>
      </div>
      <div class="conversation-list">
        <div
          class="conversation"
          v-for="(state, index) in convs"
          :key="index"
          :class="{ active: curConvId === index }"
          @click="goToConversation(index)"
        >
          <div class="conversation__title">
            <MessageSquareMore size="16" color="#595959" class="title-icon" />
            {{ state.title }}
          </div>
          <div class="conversation__delete" @click.stop="delConv(index)">
            <DeleteOutlined />
          </div>
        </div>
      </div>
    </div>
    <ChatComponent
      :conv="convs[curConvId]"
      :state="state"
      @rename-title="renameTitle"
      @newconv="addNewConv"
    />
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { DeleteOutlined } from '@ant-design/icons-vue'
import ChatComponent from '@/components/ChatComponent.vue'
import { MessageSquareMore, PanelLeftClose } from 'lucide-vue-next'

const convs = reactive(
  JSON.parse(localStorage.getItem('chat-convs')) || [
    {
      id: 0,
      title: '新对话',
      history: [],
      messages: [],
      inputText: ''
    }
  ]
)

const state = reactive({
  isSidebarOpen: JSON.parse(localStorage.getItem('chat-sidebar-open') || 'true')
})

// Watch isSidebarOpen and save to localStorage
watch(
  () => state.isSidebarOpen,
  (newValue) => {
    localStorage.setItem('chat-sidebar-open', JSON.stringify(newValue))
  }
)
const curConvId = ref(0)

const generateRandomHash = (length) => {
  let chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let hash = ''
  for (let i = 0; i < length; i++) {
    hash += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return hash
}

const renameTitle = (newTitle) => {
  convs[curConvId.value].title = newTitle
}

const goToConversation = (index) => {
  curConvId.value = index
  console.log(convs[curConvId.value])
}

const addNewConv = () => {
  curConvId.value = 0
  if (convs.length > 0 && convs[0].messages.length === 0) {
    return
  }
  convs.unshift({
    id: generateRandomHash(8),
    title: `新对话`,
    history: [],
    messages: [],
    inputText: ''
  })
}

const delConv = (index) => {
  convs.splice(index, 1)

  if (index < curConvId.value) {
    curConvId.value -= 1
  } else if (index === curConvId.value) {
    curConvId.value = 0
  }

  if (convs.length === 0) {
    addNewConv()
  }
}

// Watch convs and save to localStorage
watch(
  () => convs,
  (newStates) => {
    localStorage.setItem('chat-convs', JSON.stringify(newStates))
  },
  { deep: true }
)

// Load convs from localStorage on mount
onMounted(() => {
  const savedSonvs = JSON.parse(localStorage.getItem('chat-convs'))
  if (savedSonvs) {
    for (let i = 0; i < savedSonvs.length; i++) {
      convs[i] = savedSonvs[i]
    }
  }
})
</script>

<style lang="less" scoped>
@import '@/assets/main.css';

.chat-container {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
  background-color: #f5f7fa;
}

.conversations {
  width: 250px;
  max-width: 250px;
  border-right: 1px solid var(--main-light-3);
  background-color: var(--bg-sider);
  transition: all 0.3s ease;
  white-space: nowrap;
  /* 防止文本换行 */
  overflow: hidden;
  /* 确保内容不溢出 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);

  &.is-open {
    width: 280px;
  }

  &:not(.is-open) {
    width: 0;
    padding: 0;
    overflow: hidden;
  }

  & .actions {
    height: var(--header-height);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    z-index: 9;
    border-bottom: 1px solid rgba(22, 119, 255, 0.1);
    background-color: white;

    .header-title {
      font-weight: 600;
      font-size: 18px;
      color: #1677ff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .action {
      width: 36px;
      height: 36px;
      display: flex;
      justify-content: center;
      align-items: center;
      border-radius: 8px;
      color: #595959;
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        background-color: rgba(22, 119, 255, 0.08);
        color: #1677ff;
        transform: translateY(-2px);
      }
    }
  }

  .conversation-list {
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    max-height: calc(100% - var(--header-height));
    padding: 8px;
  }

  .conversation-list .conversation {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    cursor: pointer;
    width: 100%;
    transition: all 0.2s ease;
    border-radius: 8px;
    margin-bottom: 4px;

    &__title {
      color: #595959;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 8px;

      .title-icon {
        transition: all 0.2s ease;
      }
    }

    &__delete {
      display: none;
      color: #8c8c8c;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;

      &:hover {
        color: #ff4d4f;
        background-color: rgba(255, 77, 79, 0.1);
      }
    }

    &.active {
      background-color: rgba(22, 119, 255, 0.08);
      border-left: 3px solid #1677ff;
      padding-left: 13px;

      & .conversation__title {
        color: #1677ff;
        font-weight: 500;

        .title-icon {
          color: #1677ff;
        }
      }
    }

    &:not(.active):hover {
      background-color: rgba(0, 0, 0, 0.04);

      & .conversation__delete {
        display: flex;
      }
    }
  }

  .conversation-list::-webkit-scrollbar {
    position: absolute;
    width: 4px;
  }

  .conversation-list::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 4px;
  }

  .conversation-list::-webkit-scrollbar-thumb {
    background: #d9d9d9;
    border-radius: 4px;
  }

  .conversation-list::-webkit-scrollbar-thumb:hover {
    background: #bfbfbf;
    border-radius: 4px;
  }

  .conversation-list::-webkit-scrollbar-thumb:active {
    background: #8c8c8c;
    border-radius: 4px;
  }

  @media (max-width: 520px) {
    .conversations {
      position: absolute;
      z-index: 101;
      width: 300px;
      height: 100%;
      border-radius: 0 16px 16px 0;
      box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);

      &:not(.is-open) {
        width: 0;
        padding: 0;
        overflow: hidden;
      }
    }
  }
}
</style>
