<template>
  <div class="settings-page">
    <HeaderComponent title="设置" class="setting-header">
      <template #actions>
        <a-button
          :type="isNeedRestart ? 'primary' : 'default'"
          @click="sendRestart"
          :icon="h(ReloadOutlined)"
          class="restart-btn"
        >
          {{ isNeedRestart ? '需要刷新' : '重新加载' }}
        </a-button>
      </template>
    </HeaderComponent>

    <div class="setting-container layout-container">
      <div class="sider" v-if="state.windowWidth > 520">
        <div class="menu-title">设置菜单</div>
        <a-button
          type="text"
          :class="{ activesec: state.section === 'base' }"
          @click="state.section = 'base'"
          :icon="h(SettingOutlined)"
        >
          基本设置
        </a-button>
        <a-button
          type="text"
          :class="{ activesec: state.section === 'model' }"
          @click="state.section = 'model'"
          :icon="h(CodeOutlined)"
        >
          模型配置
        </a-button>
        <a-button
          type="text"
          :class="{ activesec: state.section === 'path' }"
          @click="state.section = 'path'"
          :icon="h(FolderOutlined)"
        >
          路径配置
        </a-button>
        <a-button
          type="text"
          :class="{ activesec: state.section === 'user' }"
          @click="state.section = 'user'"
          :icon="h(UserOutlined)"
          v-if="userStore.isAdmin"
        >
          用户管理
        </a-button>

        <a-button
          type="text"
          :class="{ activesec: state.section === 'dashboard' }"
          @click="state.section = 'dashboard'"
          :icon="h(BarChartOutlined)"
          v-if="userStore.isAdmin"
        >
          仪表盘
        </a-button>
      </div>

      <div class="setting-content">
        <div class="setting" v-if="state.section === 'base'">
          <div class="section-header">
            <h2>检索配置</h2>
            <div class="section-divider"></div>
          </div>
          <div class="section">
            <div class="card1 card-select">
              <span class="label">对话模型</span>
              <ModelSelectorComponent
                @select-model="handleChatModelSelect"
                :model_name="configStore.config?.model_name"
                :model_provider="configStore.config?.model_provider"
              />
            </div>
            <div class="card1 card-select">
              <span class="label">{{ items?.embed_model.des }}</span>
              <a-select
                style="width: 300px"
                :value="configStore.config?.embed_model"
                @change="handleChange('embed_model', $event)"
                class="custom-select"
              >
                <a-select-option
                  v-for="(name, idx) in items?.embed_model.choices"
                  :key="idx"
                  :value="name"
                  >{{ name }}
                </a-select-option>
              </a-select>
            </div>
            <div class="card1 card-select">
              <span class="label">{{ items?.reranker.des }}</span>
              <a-select
                style="width: 300px"
                :value="configStore.config?.reranker"
                @change="handleChange('reranker', $event)"
                :disabled="!configStore.config.enable_reranker"
                class="custom-select"
              >
                <a-select-option
                  v-for="(name, idx) in items?.reranker.choices"
                  :key="idx"
                  :value="name"
                  >{{ name }}
                </a-select-option>
              </a-select>
            </div>
            <div class="card1">
              <span class="label">{{ items?.enable_reranker.des }}</span>
              <a-switch
                :checked="configStore.config.enable_reranker"
                @change="handleChange('enable_reranker', !configStore.config.enable_reranker)"
                class="custom-switch"
              />
            </div>
            <div class="card card-select">
              <span class="label">{{ items?.use_rewrite_query.des }}</span>
              <a-select
                style="width: 200px"
                :value="configStore.config?.use_rewrite_query"
                @change="handleChange('use_rewrite_query', $event)"
                class="custom-select"
              >
                <a-select-option
                  v-for="(name, idx) in items?.use_rewrite_query.choices"
                  :key="idx"
                  :value="name"
                  >{{ name }}
                </a-select-option>
              </a-select>
            </div>
          </div>
          <div class="section-header">
            <h2>功能配置</h2>
            <div class="section-divider"></div>
          </div>
          <div class="section">
            <div class="card1">
              <span class="label">{{ items?.enable_knowledge_base.des }}</span>
              <a-switch
                :checked="configStore.config.enable_knowledge_base"
                @change="
                  handleChange('enable_knowledge_base', !configStore.config.enable_knowledge_base)
                "
                class="custom-switch"
              />
            </div>
          </div>
        </div>
        <div class="setting" v-if="state.section === 'model'">
          <div class="section-header">
            <h2>模型配置</h2>
            <div class="section-divider"></div>
          </div>
          <p class="description-text">
            请在 <code>src/.env</code> 文件中配置对应的 APIKEY，并重新启动服务
          </p>
          <ModelProvidersComponent />
        </div>
        <div class="setting" v-if="state.section === 'path'">
          <div class="section-header">
            <h2>本地模型配置</h2>
            <div class="section-divider"></div>
          </div>
          <p class="description-text">
            如果是 Docker 启动，务必确保在 docker-compose.dev.yaml 中添加了 volumes 映射。
          </p>
          <TableConfigComponent
            :config="configStore.config?.model_local_paths"
            @update:config="handleModelLocalPathsUpdate"
          />
        </div>
        <div class="setting" v-if="state.section === 'user'">
          <div class="section-header">
            <h2>用户管理</h2>
            <div class="section-divider"></div>
          </div>
          <UserManagementComponent />
        </div>

        <div class="dashboard-container" v-if="state.section === 'dashboard'">
          <div class="py-4 container-fluid">
            <div class="row">
              <div class="col-lg-12">
                <div class="row">
                  <div class="col-lg-3 col-md-6 col-12">
                    <mini-statistics-card
                      title="Today's Money"
                      value="¥0"
                      description="<span
                        class='text-sm font-weight-bolder text-success'
                        >+0%</span> since yesterday"
                      :icon="{
                        component: 'ni ni-money-coins',
                        background: 'bg-gradient-primary',
                        shape: 'rounded-circle'
                      }"
                    />
                  </div>
                  <div class="col-lg-3 col-md-6 col-12">
                    <mini-statistics-card
                      title="Today's Users"
                      :value="dashboardStats.todayUsers"
                      :description="dashboardStats.todayUsersGrowthDescription"
                      :icon="{
                        component: 'ni ni-world',
                        background: 'bg-gradient-danger',
                        shape: 'rounded-circle'
                      }"
                    />
                  </div>
                  <div class="col-lg-3 col-md-6 col-12">
                    <mini-statistics-card
                      title="New Clients"
                      :value="dashboardStats.newClients"
                      :description="dashboardStats.newClientsGrowthDescription"
                      :icon="{
                        component: 'ni ni-paper-diploma',
                        background: 'bg-gradient-success',
                        shape: 'rounded-circle'
                      }"
                    />
                  </div>
                  <div class="col-lg-3 col-md-6 col-12">
                    <mini-statistics-card
                      title="Sales"
                      value="¥0"
                      description="<span
                        class='text-sm font-weight-bolder text-success'
                        >+0%</span> than last month"
                      :icon="{
                        component: 'ni ni-cart',
                        background: 'bg-gradient-warning',
                        shape: 'rounded-circle'
                      }"
                    />
                  </div>
                </div>
                <div class="row">
                  <div class="col-lg-7 mb-lg">
           

<div>
		<a-row :gutter="24" type="flex" align="stretch">
			<a-col :span="24" :lg="30" class="mb-24">
			<CardBarChart :barChartData="processedBarChartData"></CardBarChart>
			</a-col>
		</a-row>
	</div>
                  </div>
                  <div class="col-lg-5">
                    <carousel />
                  </div>
                </div>
                <div class="row mt-4"></div>
              </div>
            </div>
          </div>
        </div>
        <div class="row mt-4">
          <div class="col-lg-7 mb-lg-0 mb-4">
            <div class="card">
              <div class="p-3 pb-0 card-header">
                <div class="d-flex justify-content-between">
                  <h6 class="mb-2">订阅信息</h6>
                </div>
              </div>
              <div class="table-responsive">
                <table class="table align-items-center">
                  <tbody>
                    <tr v-for="(sale, index) in sales" :key="index">
                      <td class="w-30">
                        <div class="px-2 py-1 d-flex align-items-center">
                          <div>
                            <svg
                              width="24"
                              height="24"
                              viewBox="0 0 48 48"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                            >
                              <path
                                d="M24 20C27.866 20 31 16.866 31 13C31 9.13401 27.866 6 24 6C20.134 6 17 9.13401 17 13C17 16.866 20.134 20 24 20Z"
                                fill="none"
                                stroke="#333"
                                stroke-width="4"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                              />
                              <path
                                d="M6 40.8V42H42V40.8C42 36.3196 42 34.0794 41.1281 32.3681C40.3611 30.8628 39.1372 29.6389 37.6319 28.8719C35.9206 28 33.6804 28 29.2 28H18.8C14.3196 28 12.0794 28 10.3681 28.8719C8.86278 29.6389 7.63893 30.8628 6.87195 32.3681C6 34.0794 6 36.3196 6 40.8Z"
                                fill="none"
                                stroke="#333"
                                stroke-width="4"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                              />
                            </svg>
                          </div>
                          <div class="ms-4">
                            <p class="mb-0 text-xs font-weight-bold">账号:</p>
                            <h6 class="mb-0 text-sm">{{ sale.country }}</h6>
                          </div>
                        </div>
                      </td>
                      <td>
                        <div class="text-center">
                          <p class="mb-0 text-xs font-weight-bold">套餐:</p>
                          <h6 class="mb-0 text-sm">{{ sale.sales }}</h6>
                        </div>
                      </td>
                      <td>
                        <div class="text-center">
                          <p class="mb-0 text-xs font-weight-bold">消费额:</p>
                          <h6 class="mb-0 text-sm">{{ sale.value }}</h6>
                        </div>
                      </td>
                      <td class="text-sm align-middle">
                        <div class="text-center col">
                          <p class="mb-0 text-xs font-weight-bold">Bounce:</p>
                          <h6 class="mb-0 text-sm">{{ sale.bounce }}</h6>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="col-lg-5">
            <categories-list :categories="categoriesListData" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// ... (保持原有的 script setup 内容不变，它与样式和布局无关)
import { message } from 'ant-design-vue'
import { computed, reactive, ref, h, watch, onMounted, onUnmounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { useUserStore } from '@/stores/user'
import {
  ReloadOutlined,
  SettingOutlined,
  CodeOutlined,
  FolderOutlined,
  UserOutlined,
  BarChartOutlined // 确保这里导入了 BarChartOutlined
} from '@ant-design/icons-vue'
import HeaderComponent from '@/components/HeaderComponent.vue'
import TableConfigComponent from '@/components/TableConfigComponent.vue'
import ModelProvidersComponent from '@/components/ModelProvidersComponent.vue'
import UserManagementComponent from '@/components/UserManagementComponent.vue'
import { notification, Button } from 'ant-design-vue'
import { systemConfigApi } from '@/apis/admin_api'
import ModelSelectorComponent from '@/components/ModelSelectorComponent.vue'

// 导入仪表盘所需的组件
import MiniStatisticsCard from '@/components/dashboard/MiniStatisticsCard.vue'
import GradientLineChart from '@/components/dashboard/GradientLineChart.vue'
import CardBarChart from '@/components/Cards/CardBarChart.vue' ;
import Carousel from '@/components/dashboard/Carousel.vue'
import CategoriesList from '@/components/dashboard/CategoriesList.vue'

// 1. 导入刚才创建的 dashboardApi
import { dashboardApi } from '@/apis/dashboard_api'

// ======================= 代码顺序调整 =======================
// 推荐将核心的、被多处依赖的变量和状态定义在前面

// 1. 初始化 Pinia Stores
const configStore = useConfigStore()
const userStore = useUserStore()

// 2. 定义组件核心的、控制UI的响应式状态 (被 watch 和 template 使用)
const state = reactive({
  loading: false,
  section: 'base', // 默认显示基本设置
  windowWidth: window?.innerWidth || 0
})

// 3. 定义其他状态变量
const isNeedRestart = ref(false)
const items = computed(() => configStore.config._config_items)

// 4. 定义仪表盘相关的状态
const dashboardStats = reactive({
  todayUsers: '0',
  newClients: '0',
  todayUsersGrowthDescription: '',
  newClientsGrowthDescription: ''
})
// const visitorChartData = ref({
//   labels: [],
//   datasets: [
//     {
//       label: '访客人数',
//       data: []
//     }
//   ]
// })
const processedBarChartData = ref({
  labels: [],
  datasets: [{
    label: "访客人数",
    backgroundColor: '#fff', // 保持原 CardBarChart 的样式
    borderWidth: 0,
    borderSkipped: false,
    borderRadius: 6,
    data: [],
    maxBarThickness: 20,
  }]
});

let dashboardDataLoaded = false
// 5. 定义一个函数，用于获取并处理仪表盘数据
const fetchAndProcessDashboardData = async () => {
  try {
    const stats = await dashboardApi.getActivityStats()
    console.log('从后端获取的统计数据:', stats)

    if (stats && stats.length > 0) {
      // **处理卡片数据**
      // 后端返回的数据是按日期升序的，最后一个元素就是当天的数据
      const todayData = stats[stats.length - 1]
      dashboardStats.todayUsers = todayData.total_operations.toLocaleString() // 今日操作数
      dashboardStats.newClients = `+${todayData.registration_count.toLocaleString()}` // 今日注册数，保持"+"号前缀

      // ---
      // **计算 Today's Users 比率 (与上周同天对比)**
      let todayUsersRatio = 0
      let showTodayUsersDescription = true // 标志，控制是否显示描述

      if (stats.length >= 8) {
        // 确保有足够的数据来获取上周同天的数据
        const lastWeekTodayData = stats[stats.length - 8] // 倒数第8个元素即为上周同天数据

        // 新规则：如果上周同天操作数为0 (即分母为0)，则不显示描述
        if (lastWeekTodayData.total_operations === 0) {
          showTodayUsersDescription = false
        } else {
          // 分母不为0时，正常计算比率
          todayUsersRatio =
            ((todayData.total_operations - lastWeekTodayData.total_operations) /
              lastWeekTodayData.total_operations) *
            100
        }
      } else {
        // 如果数据不足以计算上周同天，也不显示描述
        showTodayUsersDescription = false
      }

      // 格式化 Today's Users 比率描述
      if (showTodayUsersDescription) {
        const todayUsersColorClass = todayUsersRatio >= 0 ? 'text-success' : 'text-danger'
        const todayUsersSign = todayUsersRatio >= 0 ? '+' : ''
        dashboardStats.todayUsersGrowthDescription = `<span
            class='text-sm font-weight-bolder ${todayUsersColorClass}'
          >${todayUsersSign}${todayUsersRatio.toFixed(2)}%</span> since last week`
      } else {
        dashboardStats.todayUsersGrowthDescription = '' // 不显示时清空描述
      }

      // ---
      // **计算 New Clients 比率 (与上周同天对比)**
      let newClientsRatio = 0
      let showNewClientsDescription = true // 标志，控制是否显示描述

      // 检查是否有上周同天的数据 (今天日期 - 7天)
      if (stats.length >= 8) {
        const lastWeekTodayData = stats[stats.length - 8]

        // 新规则：如果上周同天注册数为0 (即分母为0)，则不显示描述
        if (lastWeekTodayData.registration_count === 0) {
          showNewClientsDescription = false
        } else {
          // 分母不为0时，正常计算比率
          newClientsRatio =
            ((todayData.registration_count - lastWeekTodayData.registration_count) /
              lastWeekTodayData.registration_count) *
            100
        }
      } else {
        // 如果数据不足以计算上周同天，也不显示描述
        showNewClientsDescription = false
      }

      // 格式化 New Clients 比率描述
      if (showNewClientsDescription) {
        const newClientsColorClass = newClientsRatio >= 0 ? 'text-success' : 'text-danger'
        const newClientsSign = newClientsRatio >= 0 ? '+' : ''
        dashboardStats.newClientsGrowthDescription = `<span
            class='text-sm font-weight-bolder ${newClientsColorClass}'
          >${newClientsSign}${newClientsRatio.toFixed(2)}%</span> since last week`
      } else {
        dashboardStats.newClientsGrowthDescription = '' // 不显示时清空描述
      }

      // **处理图表数据**
      // 根据你的要求，截取最近8天的数据用于图表
      const chartSourceData = stats.slice(-8)

     // 更新 processedBarChartData，使其包含 CardBarChart 所需的所有属性
      processedBarChartData.value = {
        labels: chartSourceData.map((item) => item.date.substring(5)),
        datasets: [
          {
            label: '访客人数',
            backgroundColor: '#fff', // 为 CardBarChart 设置背景色
            borderWidth: 0,
            borderSkipped: false,
            borderRadius: 6,
            data: chartSourceData.map((item) => item.total_operations),
            maxBarThickness: 20,
          }
        ]
      };

      // 标记数据已成功加载
      dashboardDataLoaded = true
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    message.error('获取仪表盘数据失败，请检查网络或联系管理员。')
  }
}
// 6. 监听 `state.section` 的变化，当切换到 'dashboard' 时加载数据
watch(
  () => state.section,
  (newSection) => {
    // 只有当用户切换到仪表盘，并且数据尚未加载时，才执行获取操作
    if (newSection === 'dashboard' && !dashboardDataLoaded) {
      fetchAndProcessDashboardData()
    }
  }
)

// START: 修改部分 - 移除 sales 对象中的 flag 属性
const sales = {
  us: {
    country: '24181214557',
    sales: 2500,
    value: '¥230,900',
    bounce: '29.9%'
  },
  germany: {
    country: '小华',
    sales: '3.900',
    value: '¥440,000',
    bounce: '40.22%'
  },
  britain: {
    country: '24181214558',
    sales: '1.400',
    value: '¥190,700',
    bounce: '23.44%'
  },
  brasil: {
    country: 'Brasil',
    sales: '562',
    value: '¥143,960',
    bounce: '32.14%'
  }
}
// END: 修改部分

const categoriesListData = [
  {
    icon: { component: 'ni ni-mobile-button', background: 'dark' },
    label: '学情分析'
  },
  {
    icon: { component: 'ni ni-tag', background: 'dark' },
    label: '成绩查询',
    description: '123 participate <strong>15 open</strong>'
  }
]

const handleModelLocalPathsUpdate = (config) => {
  handleChange('model_local_paths', config)
}

const preHandleChange = (key, e) => {
  if (key == 'enable_knowledge_graph' && e && !configStore.config.enable_knowledge_base) {
    message.error('启动知识图谱必须请先启用知识库功能')
    return
  }

  if (key == 'enable_knowledge_base' && !e && configStore.config.enable_knowledge_graph) {
    message.error('关闭知识库功能必须请先关闭知识图谱功能')
    return
  }

  if (
    key == 'enable_reranker' ||
    key == 'enable_knowledge_graph' ||
    key == 'enable_knowledge_base' ||
    key == 'embed_model' ||
    key == 'reranker' ||
    key == 'model_local_paths'
  ) {
    isNeedRestart.value = true
    notification.info({
      message: '需要重新加载模型',
      description: '请点击右下角按钮重新加载模型',
      placement: 'topLeft',
      duration: 0,
      btn: h(Button, { type: 'primary', onClick: sendRestart }, '立即重新加载')
    })
  }
  return true
}

const handleChange = (key, e) => {
  if (!preHandleChange(key, e)) {
    return
  }
  configStore.setConfigValue(key, e)
}

const handleChanges = (items) => {
  for (const key in items) {
    if (!preHandleChange(key, items[key])) {
      return
    }
  }
  configStore.setConfigValues(items)
}

const updateWindowWidth = () => {
  state.windowWidth = window?.innerWidth || 0
}

const handleChatModelSelect = ({ provider, name }) => {
  configStore.setConfigValues({
    model_provider: provider,
    model_name: name
  })
}

onMounted(() => {
  updateWindowWidth()
  window.addEventListener('resize', updateWindowWidth)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateWindowWidth)
})

const sendRestart = () => {
  console.log('Restarting...')
  message.loading({ content: '重新加载模型中', key: 'restart', duration: 0 })

  systemConfigApi
    .restartServer()
    .then(() => {
      console.log('Restarted')
      message.success({ content: '重新加载完成!', key: 'restart', duration: 2 })
      setTimeout(() => {
        window.location.reload()
      }, 200)
    })
    .catch((error) => {
      console.error('重启服务失败:', error)
      message.error({ content: `重启失败: ${error.message}`, key: 'restart', duration: 2 })
    })
}
</script>

<style lang="less" scoped>
.settings-page {
  background-color: #f5f7fa;
  min-height: 100vh;
}

.setting-container {
  --setting-header-height: 65px;
  user-select: text;
}

.setting-header {
  height: var(--setting-header-height);
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 10;

  p {
    margin: 8px 0 0;
    color: #6b7280;
  }

  .restart-btn {
    transition: all 0.3s;
    border-radius: 6px;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
  }
}

.setting-container {
  padding: 24px;
  box-sizing: border-box;
  display: flex;
  position: relative;
  min-height: calc(100vh - var(--setting-header-height));
  gap: 24px;

  // 移除了 .full-width 类，确保侧边栏和内容区域始终有间隙
  // &.full-width {
  //   padding-left: 0;
  //   padding-right: 0;
  //   gap: 0;
  // }
}

.sider {
  width: 220px;
  height: fit-content;
  padding: 24px 0;
  position: sticky;
  top: calc(var(--setting-header-height) + 24px);
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: 12px;
  gap: 8px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1);

  .menu-title {
    font-size: 16px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 16px;
    padding: 0 24px;
    width: 100%;
  }

  & > button {
    width: 100%;
    height: auto;
    padding: 12px 24px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-size: 15px;
    border-radius: 0;
    color: #4b5563;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;

    &:hover {
      background: #f3f4f6;
      color: #1890ff;
    }

    &.activesec {
      background: #e6f7ff;
      color: #1890ff;
      border-right: 3px solid #1890ff;
      font-weight: 500;
    }

    .anticon {
      font-size: 18px;
    }
  }
}

.setting-content {
  flex: 1;
}

.dashboard-container {
  width: 100%;
  padding: 0;
  box-sizing: border-box;
}

.setting {
  width: 100%;
  margin: 0 auto;
  height: 100%;
  margin-bottom: 40px;

  .section-header {
    margin-bottom: 16px;

    h2 {
      font-size: 20px;
      font-weight: 600;
      color: #111827;
      margin-bottom: 8px;
    }

    .section-divider {
      height: 3px;
      width: 40px;
      background: linear-gradient(90deg, #1890ff, #36cfc9);
      border-radius: 3px;
    }
  }

  .description-text {
    color: #6b7280;
    margin-bottom: 24px;
    font-size: 14px;
    line-height: 1.6;

    code {
      background-color: #f3f4f6;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      color: #ef4444;
    }
  }

  .section {
    margin-bottom: 32px;
    background-color: #fff;
    padding: 24px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .card1 {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-radius: 8px;
    background-color: #f9fafb;
    transition: all 0.3s;

    &:hover {
      background-color: #f3f4f6;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .label {
      font-weight: 500;
      color: #374151;
      margin-right: 20px;
      font-size: 15px;

      button {
        margin-left: 10px;
        height: 24px;
        padding: 0 8px;
        font-size: smaller;
      }
    }

    .custom-select {
      border-radius: 6px;

      &:hover {
        border-color: #1890ff;
      }
    }

    .custom-switch {
      &:hover {
        transform: scale(1.05);
      }
    }
  }
}

// 响应式设计优化
@media (max-width: 768px) {
  .setting-container {
    padding: 16px;
    gap: 16px;
  }

  .setting {
    .section {
      padding: 16px;
    }

    .card {
      padding: 12px;
    }
  }
}

@media (max-width: 520px) {
  .setting-container {
    flex-direction: column;
    // 移除了移动端 full-width 类的特殊处理，保持统一
    // &.full-width {
    //   padding: 16px;
    // }
  }

  .card.card-select {
    gap: 0.75rem;
    align-items: flex-start;
    flex-direction: column;

    .custom-select {
      width: 100% !important;
    }
  }

  .setting-header {
    position: static;
  }
}
</style>

<style lang="less">
// 添加全局样式以确保滚动功能在dropdown内正常工作
.ant-dropdown-menu {
  &.scrollable-menu {
    max-height: 300px;
    overflow-y: auto;
  }
}
</style>