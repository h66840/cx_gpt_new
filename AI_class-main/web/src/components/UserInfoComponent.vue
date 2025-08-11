<template>
  <div class="user-info-component">
    <a-dropdown :trigger="['click']" v-if="userStore.isLoggedIn">
      <div class="user-info-dropdown" :data-align="showRole ? 'left' : 'center'">
        <div class="user-avatar">
          <CircleUser />
          <div class="user-role-badge" :class="userRoleClass"></div>
        </div>
        <div v-if="showRole" class="username-display">{{ userStore.username }}</div>
      </div>
      <template #overlay>
        <a-menu class="user-menu">
          <a-menu-item key="username" disabled>
            <span class="user-menu-username">{{ userStore.username }}</span>
          </a-menu-item>
          <a-menu-item key="role" disabled>
            <span class="user-menu-role">{{ userRoleText }}</span>
          </a-menu-item>
          <a-menu-divider />
          <a-menu-item key="logout" @click="logout" class="logout-item">
            <LogoutOutlined /> &nbsp;退出登录
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
    <a-button v-else type="primary" @click="goToLogin" class="login-button">
      <UserRoundCheck /> <span class="login-text">登录</span>
    </a-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { CircleUser, UserRoundCheck } from 'lucide-vue-next'

const router = useRouter()
const userStore = useUserStore()

const props = defineProps({
  showRole: {
    type: Boolean,
    default: false
  }
})

// 用户名首字母（用于显示在头像中）
const userInitial = computed(() => {
  if (!userStore.username) return '?'
  return userStore.username.charAt(0).toUpperCase()
})

// 用户角色显示文本
const userRoleText = computed(() => {
  switch (userStore.userRole) {
    case 'superadmin':
      return '超级管理员'
    case 'admin':
      return '管理员'
    case 'user':
      return '普通用户'
    default:
      return '未知角色'
  }
})

// 用户角色徽章样式类
const userRoleClass = computed(() => {
  return {
    superadmin: userStore.userRole === 'superadmin',
    admin: userStore.userRole === 'admin',
    user: userStore.userRole === 'user'
  }
})

// 退出登录
const logout = () => {
  userStore.logout()
  message.success('已退出登录')
  // 跳转到首页
  router.push('/login')
}

// 前往登录页
const goToLogin = () => {
  router.push('/login')
}
</script>

<style lang="less" scoped>
.user-info-component {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-800);
  position: relative;
}

.user-info-dropdown {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    background-color: rgba(22, 119, 255, 0.05);
  }

  &[data-align='center'] {
    justify-content: center;
  }

  &[data-align='left'] {
    justify-content: flex-start;
  }
}

.username-display {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  cursor: pointer;
  position: relative;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
  }
}

.user-role-badge {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  right: -1px;
  bottom: -1px;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

  &.superadmin {
    background-color: #ff4d4f; // 红色，超管
  }

  &.admin {
    background-color: #1890ff; // 蓝色，管理员
  }

  &.user {
    background-color: #52c41a; // 绿色，普通用户
  }
}

.user-menu {
  min-width: 160px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);

  :deep(.ant-dropdown-menu-item) {
    padding: 10px 16px;
    transition: all 0.2s ease;

    &:hover:not([disabled]) {
      background-color: rgba(22, 119, 255, 0.05);
    }
  }
}

.user-menu-username {
  font-weight: bold;
  font-size: 14px;
  color: var(--gray-900);
  display: block;
}

.user-menu-role {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  display: block;
  margin-top: 2px;
}

.logout-item {
  color: #ff4d4f;

  &:hover {
    background-color: rgba(255, 77, 79, 0.05) !important;
  }
}

.login-button {
  display: flex;
  align-items: center;
  gap: 6px;
  border-radius: 20px;
  height: 32px;
  padding: 0 16px;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  border: none;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.2);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
  }

  .login-text {
    font-weight: 500;
    margin-left: 4px;
  }
}
</style>
