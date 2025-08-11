<template>
  <a-card :bordered="false" class="dashboard-bar-chart">
    <div>
      <canvas ref="chartCanvas" :style="{ height: height + 'px' }"></canvas>
    </div>
    <div class="card-title">
      <h6>访客人数</h6>
      <p>最近8天平台浏览量 <span class="text-success">+23%</span></p>
    </div>
    <div class="card-content">
      <p>此处展示了平台近期的活跃访客数据趋势，帮助您了解用户参与度。</p>
    </div>
    <a-row class="card-footer" type="flex" justify="center" align="top">
      <a-col :span="6">
        <h4>{{ latestVisitors }}</h4>
        <span>最新访客</span>
      </a-col>
      <a-col :span="6">
        <h4>{{ totalVisitorsLast8Days }}</h4>
        <span>8天总访客</span>
      </a-col>
      <a-col :span="6">
        <h4>--</h4>
        <span>活跃度</span>
      </a-col>
      <a-col :span="6">
        <h4>--</h4>
        <span>趋势</span>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { Chart, registerables } from 'chart.js'


Chart.register(...registerables)
// 定义接收的 props
// 这里的 props 对应了原来 CardBarChart 传递给 ChartBar 的 `data` 和 `height`
const props = defineProps({
  barChartData: {
    type: Object,
    required: true,
    default: () => ({
      labels: [],
      datasets: [
        {
          label: '访客人数',
          backgroundColor: '#fff',
          borderWidth: 0,
          borderSkipped: false,
          borderRadius: 6,
          data: [],
          maxBarThickness: 20
        }
      ]
    })
  },
  height: {
    type: Number,
    default: 220 // 默认高度，与原 CardBarChart 中 chart-bar 的 height 一致
  }
})


const chartCanvas = ref(null)

let chartInstance = null


const latestVisitors = computed(() => {
  const data = props.barChartData.datasets[0]?.data
  // 获取最新一个数据点的值，并进行本地化数字格式化
  return data && data.length > 0 ? data[data.length - 1].toLocaleString() : 'N/A'
})

const totalVisitorsLast8Days = computed(() => {
  const data = props.barChartData.datasets[0]?.data
  // 计算所有数据点的总和，并进行本地化数字格式化
  return data && data.length > 0 ? data.reduce((sum, val) => sum + val, 0).toLocaleString() : 'N/A'
})

// 渲染或更新图表的核心函数
const renderChart = () => {
  if (chartInstance) {
    // 如果图表实例已经存在，说明是数据更新，直接更新数据并重绘
    chartInstance.data = props.barChartData
    chartInstance.update()
  } else if (chartCanvas.value) {
    // 如果图表实例不存在且 canvas 元素已挂载，则创建新的 Chart 实例
    const ctx = chartCanvas.value.getContext('2d')
    chartInstance = new Chart(ctx, {
      type: 'bar', // 图表类型为柱状图
      data: props.barChartData, // 绑定传入的图表数据
      options: {
        // !!! 完整的 Chart.js options 配置，确保所有视觉效果一致 !!!
        layout: {
          padding: {
            top: 30,
            right: 15,
            left: 10,
            bottom: 5
          }
        },
        responsive: true, // 启用响应式，图表会根据容器大小自动调整
        maintainAspectRatio: false, // 禁用保持宽高比，允许图表自由拉伸
        plugins: {
          legend: {
            display: false // 不显示图例
          },
          tooltip: {
            // 工具提示配置 (Chart.js v3+ 为 'tooltip', 而非 'tooltips')
            enabled: true, // 启用工具提示
            mode: 'index', // 工具提示模式：显示所有数据点的提示
            intersect: false // 工具提示不要求精确交叉
          }
        },
        scales: {
          // 坐标轴配置
          y: {
            // Y 轴 (垂直轴)
            grid: {
              // 网格线
              display: true, // 显示网格线
              color: 'rgba(255, 255, 255, .2)', // 网格线颜色
              zeroLineColor: '#ffffff', // 零刻度线颜色
              borderDash: [6], // 网格线虚线样式
              borderDashOffset: [6]
            },
            ticks: {
              // 刻度标签
              suggestedMin: 0, // 建议最小值
              suggestedMax: 1000, // 建议最大值
              display: true, // 显示刻度标签
              color: '#fff', // 刻度标签颜色
              font: {
                size: 14,
                lineHeight: 1.5,
                weight: '600',
                family: 'Open Sans'
              }
            }
          },
          x: {
            // X 轴 (水平轴)
            grid: {
              display: false // 不显示网格线
            },
            ticks: {
              display: true, // 显示刻度标签
              color: '#fff', // 刻度标签颜色
              font: {
                size: 14,
                lineHeight: 1.5,
                weight: '600',
                family: 'Open Sans'
              }
            }
          }
        }
      }
    })
  }
}

// 组件挂载时执行一次图表渲染
onMounted(() => {
  renderChart()
})

// 监听 barChartData prop 的变化，当数据改变时重新渲染或更新图表
watch(
  () => props.barChartData,
  () => {
    renderChart()
  },
  { deep: true }
) // 深度监听对象内部的变化

// 组件即将销毁时，销毁 Chart 实例，防止内存泄漏
onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

---

<style lang="less" scoped>


/* Ant Design Vue 的 Card 样式基础 */
.dashboard-bar-chart {
  background-color: #ffffff; /* 示例背景色，请根据你的主题调整 */
  color: #fff; /* 文本颜色 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* 阴影 */
  padding: 20px; /* 内边距 */
  height: 100%; /* 确保卡片高度填充父容器 */
  display: flex; /* 使用 Flexbox 布局 */
  flex-direction: column; /* 垂直排列子元素 */

  /* 包裹 Canvas 的 div 容器样式 */
  > div:first-child {
    flex-grow: 1; /* 让图表区域占据可用空间 */
    min-height: 0; /* 允许 flex item 缩小 */
    margin-bottom: 20px; /* 在图表和标题之间增加间距 */
  }

  .card-title {
    margin-top: 0; /* 如果上一个 div 提供了 margin-bottom，这里可清零 */
    h6 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 5px;
      color: #fff;
    }
    p {
      font-size: 14px;
      color: #ccc;
      span.text-success {
        /* 确保 text-success 样式也存在 */
        font-weight: bold;
        color: #52c41a; /* 绿色，Ant Design Vue 默认的成功色 */
      }
    }
  }

  .card-content {
    margin-top: 15px;
    p {
      font-size: 13px;
      color: #bbb;
      line-height: 1.5;
    }
  }

  .card-footer {
    margin-top: 20px;
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1); /* 顶部边框 */
    padding-top: 15px;

    .ant-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      h4 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 2px;
        color: #fff;
      }
      span {
        font-size: 12px;
        color: #aaa;
      }
    }
  }
}

/* 图表 Canvas 自身的样式：包含原始的背景渐变 */
canvas {
  /* 使用 Less 语法，如果使用纯 CSS，移除 lang="less" */
  background-image: linear-gradient(to right, #00369e, #005cfd, #a18dff);
  width: 100% !important; /* 确保 canvas 宽度占满父容器 */
  /* height 会通过 props 传入的 :height 控制，这里无需设置 100% */
}
</style>