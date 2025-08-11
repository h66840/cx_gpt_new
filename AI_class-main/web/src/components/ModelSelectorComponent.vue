<template>
  <a-dropdown>
    <a class="model-select" @click.prevent>
      <!-- <BulbOutlined /> -->
      <a-tooltip :title="model_name" placement="right">
        <span class="model-text text"> {{ model_name }} </span>
      </a-tooltip>
      <span class="text" style="color: #aaa">{{ model_provider }} </span>
    </a>
    <template #overlay>
      <a-menu class="scrollable-menu">
        <a-menu-item-group
          v-for="(item, key) in modelKeys"
          :key="key"
          :title="modelNames[item]?.name"
        >
          <a-menu-item
            v-for="(model, idx) in modelNames[item]?.models"
            :key="`${item}-${idx}`"
            @click="handleSelectModel(item, model)"
          >
            {{ model }}
          </a-menu-item>
        </a-menu-item-group>
        <a-menu-item-group v-if="customModels.length > 0" title="自定义模型">
          <a-menu-item
            v-for="(model, idx) in customModels"
            :key="`custom-${idx}`"
            @click="handleSelectModel('custom', model.custom_id)"
          >
            custom/{{ model.custom_id }}
          </a-menu-item>
        </a-menu-item-group>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { BulbOutlined } from '@ant-design/icons-vue'
import { useConfigStore } from '@/stores/config'

const props = defineProps({
  model_name: {
    type: String,
    default: ''
  },
  model_provider: {
    type: String,
    default: ''
  }
})

const configStore = useConfigStore()
const emit = defineEmits(['select-model'])

// 从configStore中获取所需数据
const modelNames = computed(() => configStore.config?.model_names)
const modelStatus = computed(() => configStore.config?.model_provider_status)
const customModels = computed(() => configStore.config?.custom_models || [])

// 筛选 modelStatus 中为真的key
const modelKeys = computed(() => {
  return Object.keys(modelStatus.value || {}).filter((key) => modelStatus.value?.[key])
})

// 选择模型的方法
const handleSelectModel = (provider, name) => {
  emit('select-model', { provider, name })
}
</script>

<style lang="less" scoped>
.model-select {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  border: 1px solid var(--gray-300);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: white;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  &:hover {
    border-color: var(--main-400);
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
  }

  &.borderless {
    border: none;
  }

  &.max-width {
    max-width: 380px;
  }

  .model-text {
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
    color: var(--gray-800);
  }
}

.nav-btn {
  height: 2.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 10px;
  color: var(--gray-900);
  cursor: pointer;
  width: auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0.5rem 0.85rem;

  .text {
    margin-left: 10px;
    font-weight: 500;
  }

  &:hover {
    background-color: var(--main-light-3);
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  }
}

.scrollable-menu {
  max-height: 320px;
  overflow-y: auto;
  border-radius: 10px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--gray-400);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: var(--gray-500);
  }
}
</style>

<style lang="less">
// 添加全局样式以确保滚动功能在dropdown内正常工作
.ant-dropdown-menu {
  &.scrollable-menu {
    max-height: 320px;
    overflow-y: auto;
    padding: 6px;
    border-radius: 10px;

    .ant-dropdown-menu-item {
      border-radius: 8px;
      margin-bottom: 2px;
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--main-10);
      }

      &-active {
        background-color: var(--main-10);
        color: var(--main-600);
      }
    }

    .ant-dropdown-menu-item-group-title {
      padding: 8px 12px;
      color: var(--gray-700);
      font-weight: 500;
      font-size: 13px;
    }
  }
}
</style>
