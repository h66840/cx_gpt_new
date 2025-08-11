<template>
  <div class="header-container">
    <div class="header-content">
      <div class="header-title">
        <h1>{{ title }}</h1>
        <slot name="description">
          <p v-if="description">{{ description }}</p>
        </slot>
      </div>
      <div class="header-actions" v-if="$slots.actions">
        <slot name="actions"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped lang="less">
.header-container {
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 18px 24px;
  border-bottom: 1px solid rgba(22, 119, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-md);
  }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);

  h1 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: var(--main-700);
    transition: color var(--transition-fast);

    &:hover {
      color: var(--main-600);
    }
  }

  p {
    margin: 8px 0 0;
    color: var(--gray-600);
  }
}

.header-actions {
  display: flex;
  gap: 12px;

  :deep(.ant-btn) {
    border-radius: 6px;
    transition: all var(--transition-fast);

    &.ant-btn-primary {
      background-color: var(--main-600);
      border-color: var(--main-600);

      &:hover {
        background-color: var(--main-500);
        border-color: var(--main-500);
        box-shadow: 0 2px 8px rgba(22, 119, 255, 0.35);
      }
    }
  }
}
</style>
