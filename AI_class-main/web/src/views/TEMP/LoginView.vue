<template>
  <div class="login-view" :style="{ backgroundImage: `url(${loginBg})` }">
    <div class="login-container">
      <div class="login-logo">
        <h1>知识问答管理系统</h1>
      </div>

      <div v-if="isFirstRun" class="login-form">
        <h2>系统初始化</h2>
        <p class="init-desc">系统首次运行，请创建超级管理员账户：</p>

        <a-form :model="adminForm" @finish="handleInitialize" layout="vertical">
          <a-form-item
            label="用户名"
            name="username"
            :rules="[{ required: true, message: '请输入用户名' }]"
          >
            <a-input v-model:value="adminForm.username" prefix-icon="user" />
          </a-form-item>

          <a-form-item
            label="密码"
            name="password"
            :rules="[{ required: true, message: '请输入密码' }]"
          >
            <a-input-password v-model:value="adminForm.password" prefix-icon="lock" />
          </a-form-item>

          <a-form-item
            label="确认密码"
            name="confirmPassword"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validateConfirmPassword }
            ]"
          >
            <a-input-password v-model:value="adminForm.confirmPassword" prefix-icon="lock" />
          </a-form-item>

          <a-form-item>
            <a-button type="primary" html-type="submit" :loading="loading" block
              >创建管理员账户</a-button
            >
          </a-form-item>
        </a-form>
      </div>

      <div v-else>
        <div v-if="!isRegistering" class="login-form">
          <h2>用户登录</h2>

          <a-form :model="loginForm" @finish="handleLogin" layout="vertical">
            <a-form-item
              label="用户名"
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input v-model:value="loginForm.username">
                <template #prefix>
                  <user-outlined />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item
              label="密码"
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
            >
              <a-input-password v-model:value="loginForm.password">
                <template #prefix>
                  <lock-outlined />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item>
              <div class="login-options">
                <a-checkbox v-model:checked="rememberMe" @click="showDevMessage">记住我</a-checkbox>
                <a class="forgot-password" @click="showDevMessage">忘记密码?</a>
              </div>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" block>登录</a-button>
            </a-form-item>

            <div class="third-party-login">
              <div class="divider">
                <span>其他登录方式</span>
              </div>
              <div class="login-icons">
                <a-tooltip title="微信登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><wechat-outlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="企业微信登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><qrcode-outlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="飞书登录">
                  <a-button shape="circle" class="login-icon" @click="showDevMessage">
                    <template #icon><thunderbolt-outlined /></template>
                  </a-button>
                </a-tooltip>
              </div>
            </div>

            <div class="switch-form-link">
              还没有账户？ <a @click="isRegistering = true">立即注册</a>
            </div>
          </a-form>
        </div>

        <div v-else class="register-form login-form">
          <h2>用户注册</h2>

          <a-form :model="registerForm" @finish="handleRegister" layout="vertical">
            <a-form-item
              label="用户名"
              name="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input v-model:value="registerForm.username">
                <template #prefix>
                  <user-outlined />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item
              label="密码"
              name="password"
              :rules="[{ required: true, message: '请输入密码' }]"
            >
              <a-input-password v-model:value="registerForm.password">
                <template #prefix>
                  <lock-outlined />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item
              label="确认密码"
              name="confirmPassword"
              :rules="[
                { required: true, message: '请再次输入密码' },
                { validator: validateRegisterConfirmPassword }
              ]"
            >
              <a-input-password v-model:value="registerForm.confirmPassword">
                <template #prefix>
                  <lock-outlined />
                </template>
              </a-input-password>
            </a-form-item>

            <a-form-item
              label="所在机构名称"
              name="organization"
              :rules="[{ required: true, message: '请输入您所在的机构名称' }]"
            >
              <a-input v-model:value="registerForm.organization">
                <template #prefix> <team-outlined /> </template
              ></a-input>
            </a-form-item>

            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" block>注册</a-button>
            </a-form-item>

            <div class="switch-form-link">
              <div>已有账户？ <a @click="isRegistering = false">立即登录</a></div>
            </div>
          </a-form>
        </div>
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <div class="login-footer">
        <a @click="showDevMessage">联系我们</a>
        <a @click="showDevMessage">使用帮助</a>
        <a @click="showDevMessage">隐私政策</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { message } from 'ant-design-vue'
import { authApi } from '@/apis/auth_api' // 移除 chatApi，因为不再需要
import {
  UserOutlined,
  LockOutlined,
  WechatOutlined,
  QrcodeOutlined,
  ThunderboltOutlined,
  TeamOutlined
} from '@ant-design/icons-vue'
import loginBg from '@/assets/pics/login_bg.jpg'

const router = useRouter()
const userStore = useUserStore()

// 状态
const isFirstRun = ref(false)
const isRegistering = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const rememberMe = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

// 管理员初始化表单
const adminForm = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

// 注册表单
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  organization: ''
})

// 开发中功能提示
const showDevMessage = () => {
  message.info('该功能正在开发中，敬请期待！')
}

// 密码确认验证 (用于管理员初始化)
const validateConfirmPassword = (rule, value) => {
  if (value === '') {
    return Promise.reject('请确认密码')
  }
  if (value !== adminForm.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

// 密码确认验证 (用于用户注册)
const validateRegisterConfirmPassword = (rule, value) => {
  if (value === '') {
    return Promise.reject('请再次输入密码')
  }
  if (value !== registerForm.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

// --- 处理登录 ---
const handleLogin = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    await userStore.login({
      username: loginForm.username,
      password: loginForm.password
    })

    message.success('登录成功')

    // 获取之前尝试访问的路径
    const redirectPath = sessionStorage.getItem('redirect')
    sessionStorage.removeItem('redirect')

    // 定义最终的跳转目标
    let targetPath = '/' // 默认跳转到首页

    // 如果有有效的重定向路径，优先跳转到该路径
    if (redirectPath && redirectPath !== '/login') {
      targetPath = redirectPath
    } else {
      // 如果没有重定向路径，根据用户角色决定默认跳转
      if (userStore.isAdmin) {
        // 管理员默认跳转到 /chat
        targetPath = '/chat'
      } else {
        // 普通用户默认跳转到实验平台
        targetPath = '/experiment' // 您指定的“实验平台”路由
      }
    }

    // 执行最终跳转
    router.push(targetPath)
  } catch (error) {
    console.error('登录失败:', error)
    errorMessage.value = error.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}

// 处理初始化管理员
const handleInitialize = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    if (adminForm.password !== adminForm.confirmPassword) {
      errorMessage.value = '两次输入的密码不一致'
      return
    }

    await userStore.initialize({
      username: adminForm.username,
      password: adminForm.password
    })

    message.success('管理员账户创建成功')
    isFirstRun.value = false // 初始化成功后，显示登录页
  } catch (error) {
    console.error('初始化失败:', error)
    errorMessage.value = error.message || '初始化失败，请重试'
  } finally {
    loading.value = false
  }
}

// 处理用户注册
const handleRegister = async () => {
  try {
    loading.value = true
    errorMessage.value = ''

    // 调用后端注册 API
    await authApi.register({
      username: registerForm.username,
      password: registerForm.password,
      organization: registerForm.organization
    })

    message.success('注册成功，请登录！')
    isRegistering.value = false // 注册成功后切换回登录表单

    // 清空注册表单和错误信息
    errorMessage.value = ''
    registerForm.username = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    registerForm.organization = ''
  } catch (error) {
    console.error('注册失败:', error)
    errorMessage.value = error.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}

// 检查是否是首次运行
const checkFirstRunStatus = async () => {
  try {
    loading.value = true
    const isFirst = await userStore.checkFirstRun()
    isFirstRun.value = isFirst
  } catch (error) {
    console.error('检查首次运行状态失败:', error)
    errorMessage.value = '系统出错，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 组件挂载时
onMounted(async () => {
  // 如果用户已经登录，直接跳转到首页（或者管理员到 /chat，普通用户到 /experiment）
  if (userStore.isLoggedIn) {
    let targetPath = '/'
    if (userStore.isAdmin) {
      targetPath = '/chat'
    } else {
      targetPath = '/experiment' // 普通用户默认跳转到实验平台
    }
    router.push(targetPath)
    return
  }
  await checkFirstRunStatus()
})
</script>

<style lang="less" scoped>
/* 新增：用于切换表单的链接样式 */
.switch-form-link {
  text-align: right;
  margin-top: -10px; /* 根据布局微调 */
  margin-bottom: 20px;
  font-size: 14px;
  color: #666;

  a {
    color: #1890ff;
    cursor: pointer;
    &:hover {
      color: #40a9ff;
    }
  }
}

.login-view {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-size: cover;
  background-position: center;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.1);
    z-index: 0;
  }
}

.login-container {
  width: 420px;
  padding: 40px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
  backdrop-filter: blur(8px);
  border: 2px solid white;
}

.login-logo {
  text-align: center;
  margin-bottom: 30px;

  img {
    height: 70px;
    margin-bottom: 16px;
  }

  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--main-color);
    margin: 0;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }
}

.login-form {
  h2 {
    text-align: center;
    margin-bottom: 30px;
    font-size: 22px;
    font-weight: 500;
    color: #333;
  }

  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }

  :deep(.ant-input-affix-wrapper) {
    padding: 10px 11px;
    height: auto;
  }

  :deep(.ant-btn) {
    font-size: 16px;
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .forgot-password {
    color: #1890ff;
    font-size: 14px;

    &:hover {
      color: #40a9ff;
    }
  }
}

.init-desc {
  margin-bottom: 24px;
  color: #666;
  text-align: center;
}

.error-message {
  margin-top: 16px;
  padding: 10px 12px;
  background-color: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  color: #ff4d4f;
  font-size: 14px;
}

.third-party-login {
  margin-top: 20px;

  .divider {
    position: relative;
    text-align: center;
    margin: 16px 0;

    &::before,
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      width: calc(50% - 60px);
      height: 1px;
      background-color: #e8e8e8;
    }

    &::before {
      left: 0;
    }

    &::after {
      right: 0;
    }

    span {
      display: inline-block;
      padding: 0 12px;
      background-color: rgba(255, 255, 255, 0.9); /* 与容器背景色一致 */
      position: relative;
      color: #999;
      font-size: 14px;
    }
  }

  .login-icons {
    display: flex;
    justify-content: center;
    margin-top: 16px;

    .login-icon {
      margin: 0 12px;
      width: 42px;
      height: 42px;
      color: #666;
      border: 1px solid var(--gray-300);
      transition: all 0.3s;

      &:hover {
        color: var(--main-color);
        border-color: var(--main-color);
      }
    }
  }
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;

  a {
    color: #666;
    margin: 0 8px;
    cursor: pointer;

    &:hover {
      color: var(--main-color);
    }
  }
}
</style>
