<script setup>
import { onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import Chart from "chart.js/auto"; // 确保你已经安装了 chart.js

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
  height: {
    type: String,
    default: "300",
  },
  title: {
    type: String,
    default: "",
  },
  description: {
    type: String,
    default: "",
  },
  chart: {
    type: Object,
    required: true,
    // 对于复杂的对象 prop，可以更细致地定义其结构
    // labels: Array,
    // datasets: {
    //   type: Array,
    //   label: String,
    //   data: Array,
    // },
  },
});

let chartInstance = null; // 用于存储 Chart.js 实例，以便在更新或销毁时引用

/**
 * 初始化或更新图表
 */
const initChart = () => {
  // 使用 nextTick 确保 DOM 已经更新并渲染了 Canvas 元素
  nextTick(() => {
    const canvas = document.getElementById(props.id);
    if (!canvas) {
      console.warn(`Canvas element with ID '${props.id}' not found.`);
      return; // 如果 Canvas 元素不存在，则提前退出
    }

    const gradientLineChart = canvas.getContext("2d");

    // 销毁现有的图表实例，防止重复创建
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null; // 清除引用
    }

    // 创建渐变色
    var gradientStroke1 = gradientLineChart.createLinearGradient(0, 230, 0, 50);
    gradientStroke1.addColorStop(1, "rgba(203,12,159,0.2)");
    gradientStroke1.addColorStop(0.2, "rgba(72,72,176,0.0)");
    gradientStroke1.addColorStop(0, "rgba(203,12,159,0)");

    var gradientStroke2 = gradientLineChart.createLinearGradient(0, 230, 0, 50);
    gradientStroke2.addColorStop(1, "rgba(20,23,39,0.2)");
    gradientStroke2.addColorStop(0.2, "rgba(72,72,176,0.0)");
    gradientStroke2.addColorStop(0, "rgba(20,23,39,0)");

    const datasets = props.chart.datasets.map((dataset, index) => ({
      ...dataset, // 复制原始 dataset 属性
      tension: 0.4,
      borderWidth: 3, // 保持 borderWidth 为 3
      pointRadius: 0,
      fill: true,
      // 根据索引应用不同的颜色或渐变，这里使用示例颜色
      borderColor: index === 0 ? "#4BB543" : "#3A416F",
      backgroundColor: index === 0 ? gradientStroke1 : gradientStroke2,
      maxBarThickness: 6,
    }));

    chartInstance = new Chart(gradientLineChart, {
      type: "line",
      data: {
        labels: props.chart.labels,
        datasets: datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          title: {
            // 如果需要显示图表标题，可以在这里配置
            display: false,
            text: props.title,
            color: '#333', // 标题颜色
            font: {
              size: 16,
              weight: 'bold'
            }
          },
        },
        interaction: {
          intersect: false,
          mode: "index",
        },
        scales: {
          y: {
            grid: {
              drawBorder: false,
              display: true,
              drawOnChartArea: true,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              padding: 10,
              color: "#fbfbfb", // 注意：Canvas内部的字体颜色可能需要调整以适配背景
              font: {
                size: 11,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
          x: {
            grid: {
              drawBorder: false,
              display: false,
              drawOnChartArea: false,
              drawTicks: false,
              borderDash: [5, 5],
            },
            ticks: {
              display: true,
              color: "#ccc",
              padding: 20,
              font: {
                size: 11,
                family: "Open Sans",
                style: "normal",
                lineHeight: 2,
              },
            },
          },
        },
      },
    });
  });
};

onMounted(() => {
  initChart(); // 在组件挂载后初始化图表
});

onBeforeUnmount(() => {
  // 在组件销毁前销毁 Chart.js 实例，防止内存泄漏
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});

// 监听 props.chart 的变化，以便在数据更新时重新绘制图表
watch(
  () => props.chart,
  () => {
    initChart();
  },
  { deep: true } // 深度监听对象内部的变化
);
</script>

<template>
  <div class="card z-index-2">
    <div class="pb-0 card-header mb-0">
      <h6>{{ props.title }}</h6>
      <p v-if="props.description" class="text-sm" v-html="props.description" />
    </div>
    <div class="p-3 card-body">
      <div class="chart">
        <canvas
          :id="props.id"
          class="chart-canvas"
          :height="props.height"
        ></canvas>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 可以根据你的UI框架和需求调整这里的样式 */
.chart-canvas {
  width: 100% !important; /* 确保 Canvas 宽度自适应其父容器 */
  height: auto; /* 让高度根据内容自动调整，或设置固定高度如 props.height */
  max-height: 300px; /* 或者根据 props.height 设置 */
}
</style>