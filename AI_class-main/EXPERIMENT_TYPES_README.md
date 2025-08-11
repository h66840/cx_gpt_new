# 實驗類型功能說明

## 概述

本功能允許不同的實驗卡片點擊後顯示不同的詳情頁面界面。通過在實驗數據中添加 `type` 字段，系統會根據實驗類型動態加載對應的詳情組件。

## 功能特點

### 1. 動態組件切換
- 根據實驗的 `type` 字段自動選擇對應的詳情組件
- 支持多種不同的界面佈局和內容展示
- 無需修改路由，保持 URL 結構不變

### 2. 組件類型

#### 類型 A (ExperimentDetailTypeA.vue)
- **適用場景**: 視覺推理類實驗
- **特色**: 
  - 藍色主題配色
  - 傳統的左右分欄佈局
  - 專注於視覺分析相關內容
  - 包含實驗介紹、步驟、Q&A、評價等標籤頁

#### 類型 B (ExperimentDetailTypeB.vue)
- **適用場景**: 大模型應用類實驗
- **特色**:
  - 綠色主題配色
  - 現代化的 Hero 佈局
  - 網格式內容區域
  - 包含實驗概覽、步驟、學習資源、FAQ 等標籤頁

## 技術實現

### 1. 後端修改

#### 數據庫模型更新
```python
# server/models/experiment_model.py
class Experiment(Base):
    # ... 其他字段
    type = Column(String(20), default='A')  # 新增類型字段
```

#### API 響應更新
```python
# server/routers/experiment_router.py
def to_dict(self):
    return {
        # ... 其他字段
        "type": self.type,  # 添加類型字段到響應
    }
```

### 2. 前端實現

#### 主容器組件 (ExperimentDetail.vue)
```vue
<template>
  <component
    :is="detailComponent"
    v-if="experiment"
    :experiment="experiment"
    :reviews="reviews"
    @start-experiment="startExperiment"
    @go-back="goBack"
  />
</template>

<script setup>
const detailComponent = computed(() => {
  const experimentType = experiment.value.type || 'A'
  switch (experimentType) {
    case 'A': return ExperimentDetailTypeA
    case 'B': return ExperimentDetailTypeB
    default: return ExperimentDetailTypeA
  }
})
</script>
```

#### 子組件結構
每個類型組件都接收相同的 props 並發出相同的事件：
```vue
<script setup>
const props = defineProps({
  experiment: Object,
  reviews: Array,
  isLoading: Boolean,
  error: String
})

const emit = defineEmits([
  'start-experiment',
  'go-back',
  'open-rating-modal',
  'close-rating-modal',
  'review-submitted'
])
</script>
```

## 使用方法

### 1. 數據庫遷移
運行遷移腳本為現有實驗添加類型字段：
```bash
python server/utils/add_experiment_type.py
```

### 2. 設置實驗類型
在數據庫中為實驗設置 `type` 字段：
- `'A'`: 使用類型 A 的詳情組件
- `'B'`: 使用類型 B 的詳情組件

### 3. 添加新類型
如需添加新的實驗類型：

1. 創建新的詳情組件 (如 `ExperimentDetailTypeC.vue`)
2. 在 `ExperimentDetail.vue` 中添加對應的 case
3. 在數據庫中為實驗設置新的類型值

## 擴展指南

### 添加新的實驗類型

1. **創建新組件**:
```vue
<!-- ExperimentDetailTypeC.vue -->
<template>
  <div class="experiment-detail-type-c">
    <!-- 自定義佈局和內容 -->
  </div>
</template>

<script setup>
// 接收相同的 props 並發出相同的事件
const props = defineProps({
  experiment: Object,
  reviews: Array,
  isLoading: Boolean,
  error: String
})

const emit = defineEmits([
  'start-experiment',
  'go-back',
  'open-rating-modal',
  'close-rating-modal',
  'review-submitted'
])
</script>
```

2. **更新主容器**:
```javascript
// ExperimentDetail.vue
const detailComponent = computed(() => {
  const experimentType = experiment.value.type || 'A'
  switch (experimentType) {
    case 'A': return ExperimentDetailTypeA
    case 'B': return ExperimentDetailTypeB
    case 'C': return ExperimentDetailTypeC  // 新增
    default: return ExperimentDetailTypeA
  }
})
```

3. **設置實驗類型**:
在數據庫中將實驗的 `type` 字段設置為 `'C'`

## 注意事項

1. **向後兼容**: 如果實驗沒有 `type` 字段，默認使用類型 A
2. **組件一致性**: 所有類型組件都必須接收相同的 props 並發出相同的事件
3. **樣式隔離**: 每個組件使用獨立的 CSS 類名避免樣式衝突
4. **響應式設計**: 所有組件都支持移動端適配

## 測試

1. 確保不同類型的實驗能正確顯示對應的詳情頁面
2. 驗證所有交互功能（開始實驗、返回、評分等）正常工作
3. 檢查移動端適配效果
4. 確認樣式在不同組件間不衝突 