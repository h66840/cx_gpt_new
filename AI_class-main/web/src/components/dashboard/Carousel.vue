<script setup>
import carousel1 from '@/assets/carousel-1.jpg'
import carousel2 from '@/assets/carousel-2.jpg'
import carousel3 from '@/assets/carousel-3.jpg'
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Carousel as BsCarousel } from 'bootstrap'

const carouselElement = ref(null) // 用于引用 Carousel DOM 元素
let bsCarouselInstance = null // 用于存储 Bootstrap Carousel 实例

onMounted(() => {
  // 确保 DOM 元素已经挂载
  if (carouselElement.value) {
    // 禁用 data-bs-ride="carousel" 属性，我们将手动控制
    // 或者直接从 template 中移除 data-bs-ride="carousel"
    // 然后在这里手动初始化
    bsCarouselInstance = new BsCarousel(carouselElement.value, {
      interval: 5000, // 设置轮播间隔时间，单位毫秒，例如 5 秒
      wrap: true // 循环轮播
    })
  }
})

onBeforeUnmount(() => {
  // 组件销毁前，销毁 Bootstrap Carousel 实例，防止内存泄漏
  if (bsCarouselInstance) {
    bsCarouselInstance.dispose()
    bsCarouselInstance = null
  }
})
</script>

<template>
  <div class="card card-carousel overflow-hidden h-100 p-0">
    <div
      id="carouselExampleCaptions"
      class="carousel slide h-100"
      data-bs-ride="carousel"
      ref="carouselElement"
    >
      <div class="carousel-inner border-radius-lg h-100">
        <div
          class="carousel-item h-100 active"
          :style="{
            backgroundImage: 'url(' + carousel1 + ')',
            backgroundSize: 'cover'
          }"
        >
          <div class="carousel-caption d-none d-md-block bottom-0 text-start start-0 ms-5">
            <div class="icon icon-shape icon-sm bg-white text-center border-radius-md mb-3">
              <i class="ni ni-camera-compact text-dark opacity-10"></i>
            </div>
            <h5 class="text-white mb-1">人工智能实验课</h5>
            <p>Agent 驱动的视觉推理实验.</p>
          </div>
        </div>
        <div
          class="carousel-item h-100"
          :style="{
            backgroundImage: 'url(' + carousel2 + ')',
            backgroundSize: 'cover'
          }"
        >
         <div
            class="carousel-caption d-none d-md-block bottom-0 text-start start-0 ms-5"
          >
            <div
              class="icon icon-shape icon-sm bg-white text-center border-radius-md mb-3"
            >
              <i class="ni ni-bulb-61 text-dark opacity-10"></i>
            </div>
            <h5 class="text-white mb-1">创新的视觉推理方式</h5>
            <p>
              先感知，后规划，再执行，从而推理出标准答案
            </p>
          </div>
        </div>
        <div
          class="carousel-item h-100"
          :style="{
            backgroundImage: 'url(' + carousel3 + ')',
            backgroundSize: 'cover'
          }"
        >
         <div
            class="carousel-caption d-none d-md-block bottom-0 text-start start-0 ms-5"
          >
            <div
              class="icon icon-shape icon-sm bg-white text-center border-radius-md mb-3"
            >
              <i class="ni ni-trophy text-dark opacity-10"></i>
            </div>
            <h5 class="text-white mb-1">教师端控制平台</h5>
            <p>
              
            </p>
          </div>
        </div>
      </div>
      <button
        class="carousel-control-prev w-5 me-3"
        type="button"
        data-bs-target="#carouselExampleCaptions"
        data-bs-slide="prev"
      >
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
      </button>
      <button
        class="carousel-control-next w-5 me-3"
        type="button"
        data-bs-target="#carouselExampleCaptions"
        data-bs-slide="next"
      >
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
      </button>
    </div>
  </div>
</template>