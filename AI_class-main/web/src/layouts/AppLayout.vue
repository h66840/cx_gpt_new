<script setup>
import { ref, reactive, KeepAlive, onMounted, computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import {
  GithubOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
  ProjectOutlined,
  ProjectFilled,
  LayoutOutlined
} from '@ant-design/icons-vue'
import {
  Bot,
  Waypoints,
  LibraryBig,
  MessageSquareMore,
  Settings,
  BookMarked
} from 'lucide-vue-next'

import { useConfigStore } from '@/stores/config'
import { useDatabaseStore } from '@/stores/database'
import DebugComponent from '@/components/DebugComponent.vue'
import UserInfoComponent from '@/components/UserInfoComponent.vue'

const configStore = useConfigStore()
const databaseStore = useDatabaseStore()

const layoutSettings = reactive({
  showDebug: false,
  useTopBar: localStorage.getItem('useTopBar') === 'true' || false // 从本地存储读取导航模式设置
})

// 切换导航模式
const toggleNavMode = () => {
  layoutSettings.useTopBar = !layoutSettings.useTopBar
  localStorage.setItem('useTopBar', layoutSettings.useTopBar) // 保存设置到本地存储
}

// Add state for GitHub stars
const githubStars = ref(0)
const isLoadingStars = ref(false)

const getRemoteConfig = () => {
  configStore.refreshConfig()
}

const getRemoteDatabase = () => {
  if (!configStore.config.enable_knowledge_base) {
    return
  }
  databaseStore.refreshDatabase()
}

// Fetch GitHub stars count
const fetchGithubStars = async () => {
  try {
    isLoadingStars.value = true
    // 公共API，可以直接使用fetch
    const response = await fetch('https://api.github.com/repos/xerrors/Yuxi-Know')
    const data = await response.json()
    githubStars.value = data.stargazers_count
  } catch (error) {
    console.error('获取GitHub stars失败:', error)
  } finally {
    isLoadingStars.value = false
  }
}

onMounted(() => {
  getRemoteConfig()
  getRemoteDatabase()
  fetchGithubStars() // Fetch GitHub stars on mount
})

// 打印当前页面的路由信息，使用 vue3 的 setup composition API
const route = useRoute()
console.log(route)

// 下面是导航菜单部分，添加智能体项
const mainList = [
  {
    name: '实验课程',
    path: '/experiment',
    icon: BookMarked,
    activeIcon: BookMarked
    // hidden: !configStore.config.enable_knowledge_graph,
  },
  {
    name: '对话',
    path: '/chat',
    icon: MessageSquareMore,
    activeIcon: MessageSquareMore
  },
  {
    name: '知识库',
    path: '/database',
    icon: LibraryBig,
    activeIcon: LibraryBig
    // hidden: !configStore.config.enable_knowledge_base,
  }

  // {
  //   name: '智能体',
  //   path: '/agent',
  //   icon: Bot,
  //   activeIcon: Bot
  // },
  // {
  //   name: '图谱',
  //   path: '/graph',
  //   icon: Waypoints,
  //   activeIcon: Waypoints
  //   // hidden: !configStore.config.enable_knowledge_graph,
  // },
]
</script>

<template>
  <div class="app-layout" :class="{ 'use-top-bar': layoutSettings.useTopBar }">
    <!-- <div class="debug-panel">
      <a-float-button
        @click="layoutSettings.showDebug = !layoutSettings.showDebug"
        tooltip="调试面板"
        :style="{
          right: '12px'
        }"
      >
        <template #icon>
          <BugOutlined />
        </template>
</a-float-button>
<a-drawer v-model:open="layoutSettings.showDebug" title="调试面板" width="800" :contentWrapperStyle="{ maxWidth: '100%' }"
  placement="right">
  <DebugComponent />
</a-drawer>
</div> -->

    <!-- 导航模式切换按钮 -->
    <div class="nav-mode-toggle">
      <a-tooltip :title="layoutSettings.useTopBar ? '切换到侧边栏模式' : '切换到顶部导航模式'">
        <a-button type="primary" shape="circle" @click="toggleNavMode" class="toggle-btn">
          <template #icon>
            <LayoutOutlined />
          </template>
        </a-button>
      </a-tooltip>
    </div>

    <div class="header" :class="{ 'top-bar': layoutSettings.useTopBar }">
      <div class="logo circle">
        <router-link to="/">
          <!-- 侧边栏模式下的 logo -->
          <div v-if="!layoutSettings.useTopBar" class="logo-icon">
            <span class="logo-letter">AI</span>
          </div>
          <!-- 顶部模式下显示完整 logo 和文字 -->
          <div v-else class="school-logo">
            <img src="/school-logo.png" alt="学校 Logo" />
          </div>
          <span class="logo-text">AI实验课</span>
        </router-link>
      </div>
      <div class="nav">
        <!-- 使用mainList渲染导航项 -->
        <RouterLink
          v-for="(item, index) in mainList"
          :key="index"
          :to="item.path"
          v-show="!item.hidden"
          class="nav-item"
          active-class="active"
        >
          <component
            class="icon"
            :is="route.path.startsWith(item.path) ? item.activeIcon : item.icon"
          />
          <span class="text">{{ item.name }}</span>
        </RouterLink>

        <a-tooltip placement="right">
          <template #title
            >后端疑似没有正常启动或者正在繁忙中，请刷新一下或者检查 docker logs api-dev</template
          >
          <div class="nav-item warning" v-if="!configStore.config._config_items">
            <component class="icon" :is="ExclamationCircleOutlined" />
            <span class="text">警告</span>
          </div>
        </a-tooltip>
      </div>
      <div class="fill" style="flex-grow: 1"></div>

      <!-- <div class="github nav-item">
        <a-tooltip placement="right">
          <template #title>欢迎 Star</template>
          <a href="https://github.com/xerrors/Yuxi-Know" target="_blank" class="github-link">
            <GithubOutlined class="icon" style="color: #222" />
            <span v-if="githubStars > 0" class="github-stars">
              <span class="star-count">{{ (githubStars / 1000).toFixed(1) }}k</span>
            </span>
          </a>
        </a-tooltip>
      </div> -->

      <!-- <div class="nav-item api-docs">
        <a-tooltip placement="right">
          <template #title>接口文档 {{ apiDocsUrl }}</template>
          <a :href="apiDocsUrl" target="_blank" class="github-link">
            <ApiOutlined class="icon" style="color: #222;"/>
          </a>
        </a-tooltip>
      </div> -->

      <!-- 用户信息组件 -->
      <div class="nav-item user-info">
        <a-tooltip placement="right">
          <template #title>用户信息</template>
          <UserInfoComponent />
        </a-tooltip>
      </div>

      <RouterLink class="nav-item setting" to="/setting" active-class="active">
        <a-tooltip placement="right">
          <template #title>设置</template>
          <Settings />
        </a-tooltip>
      </RouterLink>
    </div>
    <div class="header-mobile">
      <a-space :size="16">
        <RouterLink to="/experiment" class="nav-item" active-class="active">实验</RouterLink>
        <RouterLink to="/chat" class="nav-item" active-class="active">对话</RouterLink>
        <RouterLink to="/database" class="nav-item" active-class="active">知识</RouterLink>
        <RouterLink to="/setting" class="nav-item" active-class="active">设置</RouterLink>
      </a-space>
    </div>
    <div class="main-content">
      <router-view v-slot="{ Component, route }" id="app-router-view">
        <keep-alive v-if="route.meta.keepAlive !== false">
          <component :is="Component" />
        </keep-alive>
        <component :is="Component" v-else />
      </router-view>
    </div>
  </div>
</template>

<style lang="less" scoped>
@import '@/assets/main.css';

:root {
  --header-width: 70px;
}

.app-layout {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  min-width: var(--min-width);
  background-color: #f5f7fa;

  .header-mobile {
    display: none;
  }

  .debug-panel {
    position: fixed;
    z-index: 100;
    right: 0;
    bottom: 50px;
    border-radius: 20px 0 0 20px;
    cursor: pointer;
  }

  .nav-mode-toggle {
    position: fixed;
    z-index: 100;
    right: 20px;
    bottom: 20px;

    .toggle-btn {
      background: linear-gradient(135deg, #1677ff, #4096ff);
      border: none;
      box-shadow: 0 4px 12px rgba(22, 119, 255, 0.2);
      transition: all 0.3s ease;
      font-size: 18px;
      width: 44px;
      height: 44px;

      &:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(22, 119, 255, 0.3);
      }
    }
  }

  .main-content {
    flex: 1;
    height: 100%;
    overflow-y: auto;
    position: relative;
  }
}

div.header,
#app-router-view {
  height: 100%;
  max-width: 100%;
  user-select: none;
}

#app-router-view {
  flex: 1 1 auto;
  overflow-y: auto;
}

.header {
  display: flex;
  flex-direction: column;
  flex: 0 0 var(--header-width);
  justify-content: flex-start;
  align-items: center;
  background-color: white;
  height: 100%;
  width: var(--header-width);
  border-right: 1px solid var(--gray-300);
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.05);
  z-index: 10;
  transition: all 0.3s ease;

  .logo {
    width: 44px;
    height: 44px;
    margin: 20px 0 30px 0;
    transition: all 0.3s ease;

    .logo-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #1677ff, #4096ff);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(22, 119, 255, 0.2);

      .logo-letter {
        color: white;
        font-size: 20px;
        font-weight: bold;
      }
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
    }

    .logo-text {
      display: none;
    }

    & > a {
      text-decoration: none;
      font-size: 24px;
      font-weight: bold;
      color: #333;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
  }

  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 62px;
    padding: 4px 6px;
    border: 1px solid transparent;
    border-radius: 12px;
    background-color: transparent;
    color: var(--main-color);
    font-size: 20px;
    transition: all 0.3s ease;
    margin: 8px 0;
    text-decoration: none;
    cursor: pointer;

    &.github {
      padding: 10px 12px;

      &:hover {
        background-color: transparent;
        border: 1px solid transparent;
      }

      .github-link {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: inherit;
      }

      .github-stars {
        display: flex;
        align-items: center;
        font-size: 12px;
        margin-top: 4px;

        .star-icon {
          color: #f0a742;
          font-size: 12px;
          margin-right: 2px;
        }

        .star-count {
          font-weight: 600;
        }
      }
    }

    &.api-docs {
      padding: 10px 12px;
    }

    &.active {
      font-weight: bold;
      color: var(--main-600);
      background-color: var(--main-50);
      border: 1px solid var(--main-100);
      box-shadow: 0 2px 8px rgba(22, 119, 255, 0.1);
    }

    &.warning {
      color: var(--error-color);
    }

    &:hover {
      background-color: var(--main-25);
      transform: translateY(-2px);
    }

    .text {
      font-size: 12px;
      margin-top: 6px;
      text-align: center;
      font-weight: 500;
      width: 100%;
    }

    .icon {
      font-size: 18px;
      background: rgba(22, 119, 255, 0.05);
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
      transition: all 0.3s ease;
    }

    &:hover .icon {
      background: rgba(22, 119, 255, 0.1);
      transform: scale(1.05);
    }

    &.active .icon {
      background: rgba(22, 119, 255, 0.15);
    }
  }

  .setting {
    width: auto;
    font-size: 20px;
    color: var(--gray-700);
    margin-bottom: 20px;
    margin-top: 10px;
    padding: 16px 12px;
    border-radius: 12px;
    transition: all 0.3s ease;

    &:hover {
      cursor: pointer;
      background-color: var(--main-25);
      color: var(--main-600);
    }

    &.active {
      color: var(--main-600);
      background-color: var(--main-50);
    }
  }
}

.header .nav {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  position: relative;
  gap: 8px;
  width: 100%;
  padding: 0 8px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;

    div.header {
      display: none;
    }

    .debug-panel {
      bottom: 80px;
    }

    .nav-mode-toggle {
      display: none;
    }

    .main-content {
      height: calc(100vh - 60px);
    }
  }

  .app-layout div.header-mobile {
    display: flex;
    flex-direction: row;
    width: 100%;
    padding: 0 16px;
    justify-content: center;
    align-items: center;
    flex: 0 0 60px;
    border-top: 1px solid var(--gray-300);
    background-color: white;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    z-index: 10;

    .nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-decoration: none;
      color: var(--gray-700);
      font-size: 12px;
      font-weight: 500;
      padding: 8px 12px;
      border-radius: 8px;
      transition: all 0.3s ease;

      .icon {
        font-size: 20px;
        margin-bottom: 4px;
      }

      &.active {
        color: var(--main-600);
        background-color: var(--main-50);
      }

      &:hover {
        background-color: var(--main-25);
      }
    }
  }

  .app-layout .chat-box::webkit-scrollbar {
    width: 0;
  }
}

.app-layout.use-top-bar {
  flex-direction: column;
}

.header.top-bar {
  flex-direction: row;
  flex: 0 0 60px;
  width: 100%;
  height: 60px;
  border-right: none;
  border-bottom: 1px solid var(--gray-300);
  background-color: white;
  padding: 0 24px;
  gap: 24px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);

  .logo {
    width: fit-content;
    height: 36px;
    margin: 0 16px 0 0;
    display: flex;
    align-items: center;

    a {
      display: flex;
      flex-direction: row;
      align-items: center;
      text-decoration: none;
      color: inherit;
    }

    .school-logo {
      display: flex;
      align-items: center;
      height: 36px;
      margin-right: 12px;

      img {
        height: 36px;
        width: auto;
        object-fit: contain;
      }
    }

    img {
      width: 36px;
      height: 36px;
      margin-right: 12px;
      border-radius: 8px;
    }

    .logo-text {
      display: block;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: 0.5px;
      color: var(--main-600);
      white-space: nowrap;
      margin-left: 8px;
    }
  }

  .nav {
    flex-direction: row;
    height: auto;
    gap: 8px;
    width: auto;
    padding: 0;
  }

  .nav-item {
    flex-direction: row;
    width: auto;
    padding: 8px 16px;
    margin: 0;
    border-radius: 8px;

    .icon {
      margin-right: 8px;
      font-size: 16px;
      width: 28px;
      height: 28px;
      background: rgba(22, 119, 255, 0.05);
      border-radius: 6px;
    }

    .text {
      margin-top: 0;
      font-size: 14px;
      font-weight: 500;
    }

    &.github,
    &.setting {
      padding: 8px 16px;
      margin: 0;

      .icon {
        margin-right: 0;
        font-size: 18px;
      }

      &.active {
        color: var(--main-600);
      }
    }

    &.github {
      a {
        display: flex;
        align-items: center;
      }

      .github-stars {
        display: flex;
        align-items: center;
        margin-left: 6px;

        .star-icon {
          color: #f0a742;
          font-size: 14px;
          margin-right: 2px;
        }
      }
    }
  }
}

// 添加滚动条美化
.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb {
  background: #c1d3f0;
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: #a0bce4;
}
</style>
