<template>
  <div
    class="chat-sidebar"
    :class="{ 'sidebar-open': isSidebarOpen, 'no-transition': isInitialRender }"
  >
    <div class="sidebar-header">
      <div class="header-title">{{ currentAgentId }}</div>
      <div class="header-actions">
        <div class="toggle-sidebar nav-btn" v-if="isSidebarOpen" @click="toggleCollapse">
          <PanelLeftClose size="20" color="var(--gray-800)" />
        </div>
      </div>
    </div>
    <div class="conversation-list-top">
      <button type="text" @click="createNewChat" class="new-chat-btn">新对话</button>
    </div>
    <div class="conversation-list">
      <a-spin v-if="loading" />
      <template v-else>
        <div
          v-for="chat in chatsList"
          :key="chat.id"
          class="conversation-item"
          :class="{ active: currentChatId === chat.id }"
          @click="selectChat(chat.id)"
        >
          <div class="conversation-info">
            <div class="conversation-title">{{ chat.title || '新对话' }}</div>
          </div>
          <div class="conversation-actions">
            <a-dropdown :trigger="['click']" @click.stop>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="rename" @click.stop="renameChat(chat.id)">
                    <EditOutlined /> 重命名
                  </a-menu-item>
                  <a-menu-item
                    key="delete"
                    @click.stop="deleteChat(chat.id)"
                    v-if="chat.id !== currentChatId"
                  >
                    <DeleteOutlined /> 删除
                  </a-menu-item>
                </a-menu>
              </template>
              <a-button type="text" class="more-btn" @click.stop>
                <MoreOutlined />
              </a-button>
            </a-dropdown>
          </div>
        </div>
        <div v-if="chatsList.length === 0" class="empty-list">暂无对话历史</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, h } from 'vue'
import { DeleteOutlined, EditOutlined, MoreOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { PanelLeftClose, MessageSquarePlus } from 'lucide-vue-next'

const props = defineProps({
  currentAgentId: {
    type: String,
    default: null
  },
  currentChatId: {
    type: String,
    default: null
  },
  chatsList: {
    type: Array,
    default: () => []
  },
  isSidebarOpen: {
    type: Boolean,
    default: false
  },
  isInitialRender: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'create-chat',
  'select-chat',
  'delete-chat',
  'rename-chat',
  'toggle-sidebar'
])

// 状态变量
const loading = ref(false)

// 创建新对话
const createNewChat = () => {
  emit('create-chat')
}

// 选择对话
const selectChat = (chatId) => {
  emit('select-chat', chatId)
}

// 删除对话
const deleteChat = (chatId) => {
  emit('delete-chat', chatId)
}

// 重命名对话
const renameChat = async (chatId) => {
  try {
    // 找到当前对话
    const chat = props.chatsList.find((c) => c.id === chatId)
    if (!chat) return

    // 获取新标题
    let newTitle = ''
    let modalInstance = null

    await new Promise((resolve, reject) => {
      modalInstance = Modal.confirm({
        title: '重命名对话',
        content: h('div', {}, [
          h('input', {
            value: chat.title,
            style: { width: '100%', marginTop: '10px' },
            onInput: (e) => {
              newTitle = e.target.value
            }
          })
        ]),
        okText: '确认',
        cancelText: '取消',
        onOk: () => {
          resolve()
        },
        onCancel: () => {
          reject()
        }
      })
    })

    // 确保有标题
    if (!newTitle.trim()) {
      message.warning('标题不能为空')
      return
    }

    // 通知父组件
    emit('rename-chat', { chatId, title: newTitle })
  } catch (error) {
    console.error('重命名对话失败:', error)
  }
}

// 折叠侧边栏
const toggleCollapse = () => {
  emit('toggle-sidebar')
}
</script>

<style lang="less" scoped>
.chat-sidebar {
  width: 0;
  height: 100%;
  background-color: #f9fafb;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  border: none;
  overflow: hidden;
  box-shadow: none;

  &.no-transition {
    transition: none !important;
  }

  &.sidebar-open {
    width: 280px;
    max-width: 300px;
    border-right: 1px solid rgba(0, 0, 0, 0.06);
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.03);
  }

  .sidebar-header {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    background: linear-gradient(to right, rgba(255, 255, 255, 0.9), rgba(249, 250, 251, 0.9));
    backdrop-filter: blur(8px);

    .header-title {
      font-weight: 600;
      font-size: 16px;
      color: var(--gray-900);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
      letter-spacing: -0.01em;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .conversation-list-top {
    padding: 16px;

    .new-chat-btn {
      width: 100%;
      padding: 10px 16px;
      height: fit-content;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--main-color), var(--main-600));
      color: white;
      border: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      font-weight: 500;
      font-size: 14px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;

      &::before {
        content: '+';
        font-size: 18px;
        font-weight: 400;
        line-height: 1;
      }

      &:hover {
        background: linear-gradient(135deg, var(--main-600), var(--main-700));
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
      }

      &:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
    }
  }

  .conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 10px;

    .conversation-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 16px;
      border-radius: 10px;
      margin-bottom: 8px;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid transparent;

      &:hover {
        background-color: rgba(0, 0, 0, 0.02);
        border-color: rgba(0, 0, 0, 0.04);

        .conversation-actions {
          opacity: 1;
        }
      }

      &.active {
        background: linear-gradient(
          to right,
          rgba(var(--main-rgb), 0.08),
          rgba(var(--main-rgb), 0.03)
        );
        border: 1px solid rgba(var(--main-rgb), 0.1);

        .conversation-title {
          color: var(--main-700);
          font-weight: 600;
        }
      }

      .conversation-info {
        flex: 1;
        min-width: 0;

        .conversation-title {
          font-size: 14px;
          color: var(--gray-800);
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          transition: color 0.2s ease;
        }

        .conversation-time {
          font-size: 12px;
          color: var(--gray-500);
        }
      }

      .conversation-actions {
        opacity: 0;
        transition: opacity 0.3s ease;

        .more-btn {
          color: var(--gray-500);
          transition: all 0.2s ease;

          &:hover {
            color: var(--main-500);
            background-color: rgba(var(--main-rgb), 0.1);
            transform: rotate(90deg);
          }
        }
      }
    }

    .empty-list {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100px;
      color: var(--gray-500);
      font-size: 14px;
      font-style: italic;
      background-color: rgba(0, 0, 0, 0.01);
      border-radius: 10px;
      margin-top: 20px;
    }
  }
}

// 滚动条美化
.conversation-list::-webkit-scrollbar {
  width: 5px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
</style>

<style lang="less">
.toggle-sidebar {
  cursor: pointer;

  &.nav-btn {
    height: 2.5rem;
    display: flex;
    justify-content: center;
    align-items: center;
    border-radius: 10px;
    color: var(--gray-700);
    cursor: pointer;
    font-size: 15px;
    width: auto;
    padding: 0.5rem 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;

    .text {
      margin-left: 10px;
      font-weight: 500;
    }

    &:hover {
      background-color: rgba(var(--main-rgb), 0.08);
      color: var(--main-600);
      transform: translateY(-1px);
    }

    &:active {
      transform: translateY(0);
    }

    .nav-btn-icon {
      width: 1.5rem;
      height: 1.5rem;
      transition: transform 0.3s ease;
    }

    &:hover .nav-btn-icon {
      transform: translateX(-2px);
    }
  }
}
</style>
