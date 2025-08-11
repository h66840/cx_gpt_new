<template>
  <div class="step-header">
    <experiment-outlined class="step-icon" />
    <a-typography-title :level="3" class="step-title"> 步骤 1: 图像表达 </a-typography-title>
  </div>

  <a-alert
    type="info"
    show-icon
    class="step-info"
    message="实验指引"
    description="提示: 根据图像类别特征，利用视觉语言大模型，对图像进行结构化表达，为后续实验做准备！"
  />

  <div class="step3-image-select-row">
    <!-- 類別導航欄 -->
    <div class="category-nav-scroll">
      <div
        v-for="cat in categories"
        :key="cat.key"
        class="category-nav-item"
        :class="{ active: activeCategory === cat.key }"
        @click="openImageSelector(cat.key)"
      >
        <img :src="cat.icon" :alt="cat.label" class="cat-icon" />
        <span class="cat-label">{{ cat.label }}</span>
      </div>
      <!-- 上傳圖片按鈕 -->
      <div class="upload-nav-item">
        <a-upload
          :show-upload-list="false"
          :before-upload="handleUpload"
          accept="image/*"
          :custom-request="() => {}"
        >
          <a-button type="primary" class="upload-nav-btn">
            <upload-outlined />
            上传图像
          </a-button>
        </a-upload>
      </div>
    </div>
    <div class="main-content-row">
      <!-- 左側：圖片選擇與預覽 -->
      <div class="image-select-col">
        <div class="image-selector-area">
          <div class="selector-placeholder">
            <a-button
              type="dashed"
              size="large"
              class="select-image-btn"
              @click="openImageSelector(activeCategory)"
            >
              <picture-outlined />
              点击选择实验图片
            </a-button>
            <div class="selected-category-info">
              <span class="category-label">当前类别：{{ getCategoryLabel(activeCategory) }}</span>
            </div>
          </div>
        </div>
        <div class="preview-area">
          <a-card :bordered="false" class="preview-card">
            <template #title>
              <div class="preview-card-title">
                <experiment-outlined />
                <span>实验图片</span>
              </div>
            </template>
            <div class="preview-content">
              <div v-if="selectedImage" class="image-container">
                <div class="image-frame">
                  <div class="frame-corner frame-corner-tl"></div>
                  <div class="frame-corner frame-corner-tr"></div>
                  <div class="frame-corner frame-corner-bl"></div>
                  <div class="frame-corner frame-corner-br"></div>
                  <a-image
                    :src="selectedImage.path"
                    :alt="selectedImage.description"
                    class="preview-img"
                  />
                </div>
                <div class="image-info">
                  <div class="image-name">{{ selectedImage.description }}</div>
                  <div class="image-category">
                    <tag-outlined />
                    <span>{{ getCategoryLabel(activeCategory) }}</span>
                  </div>
                </div>
              </div>
              <a-empty v-else description="请先选择实验图片" class="empty-placeholder">
                <template #image>
                  <picture-outlined class="empty-icon" />
                </template>
              </a-empty>
            </div>
          </a-card>
        </div>
      </div>
      <!-- 右側：輸入提示詞與操作 -->
      <div class="prompt-col">
        <a-form layout="vertical" class="prompt-form">
          <a-form-item label="输入初始提示词:" required class="form-label">
            <a-textarea
              v-model:value="localInitialPrompt"
              :rows="6"
              placeholder="请设计将左侧图片转换为场景图json的提示词..."
              :disabled="internalIsLoading"
              allow-clear
              class="prompt-textarea"
            />

            <!-- 示例提示詞選項 -->
            <div class="example-prompts">
              <div class="example-title">
                <file-text-outlined />
                <span>典型示例</span>
              </div>
              <div class="example-list">
                <div class="example-item" @click="showExampleLayout">
                  <bulb-outlined />
                  <span>示例一：基础对象识别</span>
                </div>
                <div class="example-item" @click="showSceneGraph">
                  <bulb-outlined />
                  <span>案例一：场景图</span>
                </div>
              </div>
            </div>
          </a-form-item>
          <a-space class="mt-6 action-buttons" size="large">
            <a-button
              type="primary"
              size="large"
              :loading="internalIsLoading"
              @click="generateDescription"
              :disabled="!localInitialPrompt.trim() || !selectedImage"
              class="generate-btn"
            >
              <robot-outlined />
              {{ internalIsLoading ? '生成中...' : '生成场景图json' }}
            </a-button>
            <a-button
              v-if="localImageDescription && !internalIsLoading"
              type="primary"
              size="large"
              @click="renderSceneGraph"
              class="render-btn"
            >
              <experiment-outlined />
              场景图可视化
            </a-button>
            <!-- <a-button
              type="primary"
              size="large"
              @click="goToNextStep"
              :disabled="!localImageDescription || internalIsLoading"
              class="next-btn"
            >
              <arrow-right-outlined />
              前往下一步实验流程
            </a-button> -->
          </a-space>
        </a-form>
        <a-collapse
          v-if="localImageDescription || internalIsLoading || apiError"
          class="mt-6 result-collapse"
          :bordered="false"
          expand-icon-position="start"
          :default-active-key="['1']"
        >
          <a-collapse-panel key="1" header="视觉表达结果">
            <template #header>
              <div class="collapse-header">
                <file-text-outlined />
                视觉表达结果
              </div>
            </template>
            <a-spin
              :spinning="internalIsLoading"
              :delay="100"
              tip="AI正在将图像转为结构化知识，这可能需要几秒钟..."
            >
              <div
                v-if="!internalIsLoading"
                class="description-result markdown-content scrollable-result"
                v-html="renderedMarkdown"
              ></div>
            </a-spin>
          </a-collapse-panel>
        </a-collapse>
        <div class="guidance-actions" v-if="localImageDescription && !internalIsLoading">
          <a-button type="primary" @click="handleGetSuggestion"> 下一步骤 </a-button>
        </div>
      </div>
    </div>

    <!-- 圖片選擇彈出框 -->
    <a-modal
      v-model:open="imageSelectorVisible"
      :title="`选择${getCategoryLabel(selectedCategory)}图片`"
      width="800px"
      :footer="null"
      class="image-selector-modal"
      :mask-closable="true"
    >
      <div class="image-selector-content">
        <div class="category-info">
          <div class="category-icon">
            <img
              :src="getCategoryIcon(selectedCategory)"
              :alt="getCategoryLabel(selectedCategory)"
            />
          </div>
          <div class="category-description">
            <h3>{{ getCategoryLabel(selectedCategory) }}</h3>
            <p>请从下方选择一张实验图片，或使用顶部导航栏切换其他类别</p>
          </div>
        </div>

        <a-carousel arrows :dots="true" class="image-carousel" autoplay>
          <template #prevArrow>
            <div class="carousel-arrow carousel-arrow-prev">
              <left-outlined />
            </div>
          </template>
          <template #nextArrow>
            <div class="carousel-arrow carousel-arrow-next">
              <right-outlined />
            </div>
          </template>

          <div class="carousel-slide">
            <div class="carousel-grid">
              <div
                v-for="img in categoryImages[selectedCategory]"
                :key="img.path"
                class="carousel-img-wrapper"
                :class="{
                  selected: selectedImage?.path === img.path,
                  hovering: hoveringImage === img.path
                }"
                @click="selectImageFromModal(img)"
                @mouseenter="startImageHover(img.path)"
                @mouseleave="endImageHover()"
              >
                <div class="img-card">
                  <div class="img-preview">
                    <img :src="img.path" :alt="img.description" />
                    <div class="select-overlay">
                      <check-circle-outlined />
                    </div>
                    <div class="hover-overlay">
                      <zoom-in-outlined />
                    </div>
                  </div>
                  <div class="img-desc">{{ img.description }}</div>
                </div>
              </div>
            </div>
          </div>
        </a-carousel>
      </div>
    </a-modal>

    <!-- 示例布局弹窗 -->
    <a-modal
      v-model:open="exampleLayoutVisible"
      title="示例布局"
      width="900px"
      :footer="null"
      class="example-layout-modal"
    >
      <div class="example-layout-content">
        <div class="example-case-selector">
          <div class="selector-label">选择案例：</div>
          <a-radio-group v-model:value="selectedCase" button-style="solid">
            <a-radio-button value="case1">案例一: 基础对象识别</a-radio-button>
            <a-radio-button value="case2">案例二: 人物类系描述</a-radio-button>
          </a-radio-group>
        </div>

        <div class="example-layout-grid">
          <!-- 源图片区域 -->
          <div class="layout-section">
            <div class="section-title">【源图片】</div>
            <div class="section-content image-section">
              <img :src="currentCaseData.imageSrc" alt="示例图片" class="example-image" />
            </div>
          </div>

          <!-- 提示词模板区域 -->
          <div class="layout-section">
            <div class="section-title">
              【提示词模板】
              <span class="section-subtitle">（附带一键复制）</span>
              <a-button type="link" size="small" @click="copyPromptTemplate" class="copy-btn">
                <copy-outlined />
              </a-button>
            </div>
            <div class="section-content prompt-section">
              <a-typography-paragraph>
                {{ currentCaseData.promptTemplate }}
              </a-typography-paragraph>
            </div>
          </div>

          <!-- 生成的场景图区域 -->
          <div class="layout-section">
            <div class="section-title">
              【生成的场景图】
              <span class="section-subtitle">（JSON结果）</span>
            </div>
            <div class="section-content result-section">
              <pre v-if="currentCaseData.resultType === 'json'" class="json-result">{{
                currentCaseData.result
              }}</pre>
              <div
                v-else-if="currentCaseData.resultType === 'markdown'"
                class="markdown-result"
                v-html="renderMarkdownText(currentCaseData.result)"
              ></div>
              <div v-else class="text-result">{{ currentCaseData.result }}</div>
            </div>
          </div>
        </div>

        <div class="example-actions">
          <a-button type="primary" @click="applyCurrentTemplate"> 应用此提示词模板 </a-button>
          <a-button @click="exampleLayoutVisible = false"> 关闭 </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 自定义组件弹窗 -->
    <a-modal
      v-model:open="customComponentVisible"
      title="自定义组件示例"
      width="900px"
      :footer="null"
      class="custom-component-modal"
    >
      <div class="custom-component-content">
        <!-- 这里可以放置自定义组件 -->
        <div class="placeholder-component">
          <div class="placeholder-header">
            <experiment-outlined />
            <span>自定义组件 (待实现)</span>
          </div>
          <div class="placeholder-body">
            <p>这里将渲染您的自定义组件，目前组件待定。</p>
            <p>您可以在这里实现任何需要的功能，例如：</p>
            <ul>
              <li>图像处理工具</li>
              <li>交互式表单</li>
              <li>数据可视化</li>
              <li>其他自定义功能</li>
            </ul>
          </div>
        </div>

        <div class="custom-actions">
          <a-button type="primary" @click="applyCustomTemplate"> 应用此模板 </a-button>
          <a-button @click="customComponentVisible = false"> 关闭 </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 場景圖可視化彈出框 -->
    <a-modal
      v-model:open="showGraphVisualization"
      title="场景图可视化"
      width="1200px"
      :footer="null"
      class="scene-graph-modal"
      :destroyOnClose="true"
    >
      <div class="scene-graph-content">
        <ThreeDPyramidGraph :graph-data="sceneGraphData" />
      </div>
    </a-modal>

    <!-- 实验指引弹窗 -->
    <a-modal v-model:open="guidanceModalVisible" title="实验指引" width="700px" class="guidance-modal">
      <div v-if="guidanceLoading" style="text-align: center; padding: 40px">
        <a-spin tip="正在获取指引..." />
      </div>
      <div v-else class="guidance-modal-content markdown-content" v-html="renderedGuidance"></div>
      <template #footer>
        <a-button key="back"  type="primary" @click="guidanceModalVisible = false">层次场景图分析</a-button>
        <a-button key="next" type="primary" @click="goToNextStep">下一步</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import {
  UploadOutlined,
  LeftOutlined,
  RightOutlined,
  RobotOutlined,
  ArrowRightOutlined,
  FileTextOutlined,
  PictureOutlined,
  ExperimentOutlined,
  TagOutlined,
  CheckCircleOutlined,
  ZoomInOutlined,
  BulbOutlined,
  CopyOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'
import MarkdownIt from 'markdown-it'
import ThreeDPyramidGraph from '@/components/Three/ThreeDPyramidGraph.vue'
import { getSceneGraph, analyzeShortcomingsStream } from '@/apis/visual_api'

// 導入圖標圖片
import educationIcon from '@/assets/icons/教育.png'
import dailyIcon from '@/assets/icons/日常.png'
import biologyIcon from '@/assets/icons/生物.png'
import geographyIcon from '@/assets/icons/地理.png'

// 類別定義（使用圖片路徑替代圖標組件）
const categories = [
  { key: '日常', label: '数据集1', icon: dailyIcon },
  { key: '教育', label: '数据集2', icon: educationIcon },

  { key: '生物', label: '数据集3', icon: biologyIcon },
  { key: '地理', label: '数据集4', icon: geographyIcon }
]
const activeCategory = ref(categories[0].key)

// 圖片選擇器相關狀態
const imageSelectorVisible = ref(false)
const selectedCategory = ref('')

// 自動獲取所有圖片並分類
const imageModules = import.meta.glob('@/assets/experiment_pics/*/*.{jpg,png,jpeg,gif,webp}', {
  eager: true,
  import: 'default'
})
const categoryImages = {}
for (const path in imageModules) {
  const match = path.match(/experiment_pics\/([^/]+)\/([^/]+)$/)
  if (match) {
    const cat = match[1]
    if (!categoryImages[cat]) categoryImages[cat] = []
    categoryImages[cat].push({
      path: imageModules[path],
      description: match[2]
    })
  }
}
const selectedImage = ref(categoryImages[activeCategory.value]?.[0] || null)

// 圖片預覽狀態
const previewImage = ref(null)

// 懸停圖片路徑
const hoveringImage = ref(null)

// 開始懸停
function startImageHover(imagePath) {
  hoveringImage.value = imagePath
}

// 結束懸停
function endImageHover() {
  hoveringImage.value = null
}

// 打開圖片選擇器
function openImageSelector(category) {
  selectedCategory.value = category
  activeCategory.value = category
  imageSelectorVisible.value = true
}

// 從彈出框中選擇圖片
function selectImageFromModal(img) {
  selectedImage.value = img
  imageSelectorVisible.value = false
}

// 處理上傳圖片
function handleUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const imgObj = {
      path: e.target.result,
      description: file.name || '自定义上传图片'
    }
    selectedImage.value = imgObj
  }
  reader.readAsDataURL(file)
  return false // 阻止默認上傳行為
}

// 獲取類別標籤
function getCategoryLabel(categoryKey) {
  const category = categories.find((cat) => cat.key === categoryKey)
  return category ? category.label : categoryKey
}

// 獲取類別圖標
function getCategoryIcon(categoryKey) {
  const category = categories.find((cat) => cat.key === categoryKey)
  return category ? category.icon : ''
}

// 其餘表單與描述生成
const props = defineProps({
  initialPrompt: { type: String, default: '' },
  isLoading: { type: Boolean, default: false },
  imageDescription: { type: String, default: null }
})
const emits = defineEmits([
  'update:initialPrompt',
  'update:imageDescription',
  'update:isLoading',
  'saveState',
  'next'
])

const apiError = ref(null)
const localInitialPrompt = ref(props.initialPrompt)
const localImageDescription = ref(props.imageDescription)
const internalIsLoading = ref(props.isLoading)

const md = new MarkdownIt({ html: true, breaks: true, linkify: true })
const renderedMarkdown = computed(() => {
  if (!localImageDescription.value) return ''
  try {
    return md.render(localImageDescription.value || '')
  } catch {
    return localImageDescription.value
  }
})

watch(
  () => props.initialPrompt,
  (v) => {
    localInitialPrompt.value = v
  }
)
watch(
  () => props.imageDescription,
  (v) => {
    localImageDescription.value = v
  }
)
watch(
  () => props.isLoading,
  (v) => {
    internalIsLoading.value = v
  }
)
watch(localInitialPrompt, (v) => emits('update:initialPrompt', v))
watch(localImageDescription, (v) => emits('update:imageDescription', v))

async function generateDescription() {
  if (!localInitialPrompt.value.trim() || !selectedImage.value) return
  apiError.value = null
  internalIsLoading.value = true
  emits('update:isLoading', true)
  localImageDescription.value = ''
  emits('update:imageDescription', '')
  try {
    // 準備圖片文件
    let imageFile
    if (selectedImage.value.path.startsWith('data:')) {
      // 如果是上傳的圖片（data URL）
      const res = await fetch(selectedImage.value.path)
      const blob = await res.blob()
      imageFile = new File([blob], selectedImage.value.description || 'uploaded_image.png', {
        type: blob.type
      })
    } else {
      // 如果是預設圖片
      const res = await fetch(selectedImage.value.path)
      const blob = await res.blob()
      const fileName = selectedImage.value.path.split('/').pop()
      imageFile = new File([blob], fileName, { type: blob.type })
    }

    // 準備 FormData
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('prompt', localInitialPrompt.value)

    // 發送請求到新的後端接口
    const result = await getSceneGraph(formData)

    // 將結果格式化為 JSON 並顯示
    const formattedResult = JSON.stringify(result, null, 2)
    localImageDescription.value = `\`\`\`json\n${formattedResult}\n\`\`\``
    emits('update:imageDescription', localImageDescription.value)
  } catch (error) {
    apiError.value = `生成图片描述失败: ${error.message || '未知错误'}`
    localImageDescription.value = null
    emits('update:imageDescription', null)
  } finally {
    if (internalIsLoading.value) {
      internalIsLoading.value = false
      emits('update:isLoading', false)
    }
    nextTick(() => {
      emits('saveState')
    })
  }
}

function goToNextStep() {
  emits('next')
}

// 渲染場景圖
function renderSceneGraph() {
  try {
    // 從 markdown 格式的結果中提取 JSON
    let jsonData = localImageDescription.value

    // 如果是 markdown 格式，提取 JSON 部分
    if (jsonData.includes('```json')) {
      const jsonMatch = jsonData.match(/```json\n([\s\S]*?)\n```/)
      if (jsonMatch) {
        jsonData = jsonMatch[1]
      }
    }

    // 解析 JSON
    const parsedData = JSON.parse(jsonData)

    // 轉換數據格式以適配 ThreeDPyramidGraph 組件
    const nodes = parsedData.nodes
      ? parsedData.nodes.map((node, index) => ({
          id: node.id,
          name: node.id,
          level: node.level || 1,
          color: getColorByLevel(node.level || 1),
          type: node.type || 'Object'
        }))
      : []

    const edges = parsedData.edges
      ? parsedData.edges.map((edge) => ({
          source: edge.source,
          target: edge.target,
          relationship: edge.relationship || 'related'
        }))
      : []

    // 設置場景圖數據
    sceneGraphData.value = { nodes, edges }

    // 顯示可視化模態框
    showGraphVisualization.value = true
  } catch (error) {
    console.error('解析場景圖數據失敗:', error)
    // 可以添加錯誤提示
    apiError.value = `解析場景圖數據失敗: ${error.message}`
  }
}

// 示例布局相關狀態
const exampleLayoutVisible = ref(false)
const selectedCase = ref('case1')

// 導入示例圖片
import exampleImage1 from '@/assets/experiment_pics/日常/1.jpg'
import exampleImage2 from '@/assets/experiment_pics/生物/2.png'

// 案例數據
const caseData = {
  case1: {
    imageSrc: exampleImage1,
    promptTemplate: `你是一位图像分析专家，请将图片内容转换为层次化的知识图谱，遵循"场景→分区→大物→小物"的层次化思维。

**输出要求：**
返回JSON格式：\`{"nodes": [...], "edges": [], "hidden_attributes": []}\`

**nodes格式：**
- \`id\`：实体的中文名称（纯粹的实体名称，不包含任何属性）
- \`type\`：实体类型（英文）
- \`level\`：层级（1-4）

**edges格式：**
- \`source\`：起始节点id
- \`target\`：目标节点id
- \`relationship\`：关系描述

**hidden_attributes格式：**
- \`entity_id\`：实体id
- \`attribute_type\`：属性类型（如：color, material, size, age, gender等）
- \`attribute_value\`：属性值

**层次化结构 - 场景分区+大物->小物原则：**
1. **全局层(level=1)**：场景（如：室内家庭储物场景）
2. **分区层(level=2)**：主体区、背景区（Zone）
   - 主体区：画面主要焦点区域
   - 背景区：画面背景区域
3. **大物体层(level=3)**：主体区/背景区中的大型支撑物体（如桌子、书架、柜子等）
4. **小物体/部件层(level=4)**：放置于大物体上的中小型物体或部件（如电热水壶、耳机、手柄等）

**层次链：**
场景(level=1) → 主体区/背景区(level=2) → 大物体(level=3) → 小物体/部件(level=4)

**大物->小物层次化思维：**
- 先划分主体区/背景区，再在主体区/背景区内找出大型支撑物体，最后将小物体/部件归属于大物体之下。
- 小物体通常位于大物体之上、之内或旁边。
- 关系链应尽量体现这种容器-内容的层次。

**重要规则 - 属性分离：**
1. **节点ID必须是纯粹的实体名称**：
   - 正确：\`泰迪熊\`, \`T恤\`, \`汽车\`, \`小孩\`
   - 错误：\`棕色泰迪熊\`, \`红色T恤\`, \`蓝色汽车\`, \`可爱的小孩\`
2. **所有属性存储在hidden_attributes中：**
   - 颜色：\`{"entity_id": "泰迪熊", "attribute_type": "color", "attribute_value": "棕色"}\`
   - 材质：\`{"entity_id": "桌子", "attribute_type": "material", "attribute_value": "木质"}\`
   - 大小：\`{"entity_id": "包", "attribute_type": "size", "attribute_value": "小"}\`
   - 年龄：\`{"entity_id": "小孩", "attribute_type": "age", "attribute_value": "幼儿"}\`
   - 性别：\`{"entity_id": "小孩", "attribute_type": "gender", "attribute_value": "男性"}\`
3. **建立层级关系**：下级节点通过"contains"或"has_part"关系连接到上级节点
4. **关系类型定义：**
   - **层级关系**："contains"（包含）、"has_part"（部件）
   - **功能关系**："interacts_with"（交互）、"wears"（穿戴）、"uses"（使用）
   - **位置关系**："在...旁边"（相邻）、"在...上方"（上下）、"在...下方"（下上）、"在...左侧"（左右）、"在...右侧"（右左）、"在...前面"（前后）、"在...后面"（后前）
   - **空间关系**："near"（附近）、"beside"（旁边）、"above"（上方）、"below"（下方）、"left_of"（左侧）、"right_of"（右侧）、"in_front_of"（前面）、"behind"（后面）

**实体类型：**
- \`Scene\`：场景（level=1）
- \`Zone\`：区域（level=2）
- \`Object\`：物体（level=3/4）
- \`Part\`：部件（level=4）
- \`Person\`：人物（level=4）
- \`Animal\`：动物（level=4）

**目标**：构建清晰的"场景→分区→大物→小物"层次化场景图，所有属性作为隐含信息存储在hidden_attributes中便于后端查询。`,

    result: `{'nodes': [{'id': '室内场景', 'type': 'Scene', 'level': 1}, {'id': '主体区', 'type': 'Zone', 'level': 2}, {'id': '背景区', 'type': 'Zone', 'level': 2}, {'id': '小孩', 'type': 'Person', 'level': 3}, {'id': '泰迪熊', 'type': 'Object', 'level': 4}, {'id': 'T恤', 'type': 'Object', 'level': 4}, {'id': '食物', 'type': 'Object', 'level': 4}, {'id': '桌子', 'type': 'Object', 'level': 3}, {'id': '背景人物', 'type': 'Person', 'level': 3}], 'edges': [{'source': '室内场景', 'target': '主体区', 'relationship': 'contains'}, {'source': '室内场景', 'target': '背景区', 'relationship': 'contains'}, {'source': '主体区', 'target': '小孩', 'relationship': 'contains'}, {'source': '主体区', 'target': '桌子', 'relationship': 'contains'}, {'source': '背景区', 'target': '背景人物', 'relationship': 'contains'}, {'source': '小孩', 'target': '泰迪熊', 'relationship': 'interacts_with'}, {'source': '小孩', 'target': 'T恤', 'relationship': 'wears'}, {'source': '小孩', 'target': '食物', 'relationship': 'interacts_with'}, {'source': '桌子', 'target': '小孩', 'relationship': 'in_front_of'}], 'hidden_attributes': [{'entity_id': '室内场景', 'attribute_type': 'location', 'attribute_value': '室内'}, {'entity_id': '小孩', 'attribute_type': 'age', 'attribute_value': '幼儿'}, {'entity_id': '小孩', 'attribute_type': 'gender', 'attribute_value': '男性'}, {'entity_id': '泰迪熊', 'attribute_type': 'color', 'attribute_value': '棕色'}, {'entity_id': '泰迪熊', 'attribute_type': 'accessory', 'attribute_value': '红色蝴蝶结'}, {'entity_id': 'T恤', 'attribute_type': 'color', 'attribute_value': '红色'}, {'entity_id': '食物', 'attribute_type': 'type', 'attribute_value': '面包'}, {'entity_id': '桌子', 'attribute_type': 'material', 'attribute_value': '木质'}, {'entity_id': '背景人物', 'attribute_type': 'clothing', 'attribute_value': '黑色T恤'}]}`,
    resultType: 'json'
  },
  case2: {
    imageSrc: exampleImage2,
    promptTemplate: '请描述图中人物的特征，包括服装、姿势和可能的情绪状态，以详细的文本形式返回。',
    result: `# `,
    resultType: 'markdown'
  }
}

// 當前選中的案例數據
const currentCaseData = computed(() => {
  return caseData[selectedCase.value]
})

// 顯示示例布局
function showExampleLayout() {
  exampleLayoutVisible.value = true
}

// 應用當前模板
function applyCurrentTemplate() {
  localInitialPrompt.value = currentCaseData.value.promptTemplate
  exampleLayoutVisible.value = false
}

// 複製提示詞模板
function copyPromptTemplate() {
  navigator.clipboard
    .writeText(currentCaseData.value.promptTemplate)
    .then(() => {
      // 可以添加提示复制成功的逻辑
      console.log('复制成功')
    })
    .catch((err) => {
      console.error('复制失败:', err)
    })
}

// 為案例數據渲染 Markdown (新函數，避免與已有計算屬性衝突)
function renderMarkdownText(text) {
  try {
    return md.render(text || '')
  } catch {
    return text
  }
}

// 應用示例提示詞
function applyExample(exampleText) {
  localInitialPrompt.value = exampleText
  exampleLayoutVisible.value = false
}

// 自定義組件相關狀態
const customComponentVisible = ref(false)

// 顯示自定義組件
function showCustomComponent() {
  localInitialPrompt.value = caseData.case1.promptTemplate
  // 不顯示彈窗，直接應用模板
  // customComponentVisible.value = true;
}

// 應用自定義模板
function applyCustomTemplate() {
  localInitialPrompt.value =
    '请描述图中人物的特征，包括服装、姿势、表情和可能的情绪状态，以详细的文本形式返回。需要包含年龄估计和主要视觉特征。'
  customComponentVisible.value = false
}

// 場景圖可視化相關狀態
const showGraphVisualization = ref(false)
const sceneGraphData = ref({
  nodes: [],
  edges: []
})

// 顯示場景圖可視化
function showSceneGraph() {
  // 應用提示詞模板
  localInitialPrompt.value = caseData.case1.promptTemplate

  // 解析 JSON 字符串為對象
  try {
    // 這裡假設 result 是一個 JSON 字符串，需要解析
    const resultData = JSON.parse(caseData.case1.result.replace(/'/g, '"'))

    // 將數據轉換為 ThreeDPyramidGraph 需要的格式
    const nodes = resultData.nodes.map((node) => ({
      id: node.id,
      name: node.id, // 使用 id 作為名稱
      level: node.level,
      // 根據 level 設置不同顏色
      color: getColorByLevel(node.level),
      type: node.type
    }))

    const edges = resultData.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      relationship: edge.relationship
    }))

    sceneGraphData.value = { nodes, edges }
    showGraphVisualization.value = true
  } catch (error) {
    console.error('解析場景圖數據失敗:', error)
  }
}

// 根據層級獲取顏色
function getColorByLevel(level) {
  const colors = {
    1: '#FF5733', // 場景層 - 紅色
    2: '#33FF57', // 分區層 - 綠色
    3: '#3357FF', // 大物體層 - 藍色
    4: '#F3FF33' // 小物體/部件層 - 黃色
  }
  return colors[level] || '#FFFFFF'
}

// 不需要單獨的關閉函數，因為 a-modal 會自動處理關閉

// 实验指引
const guidanceModalVisible = ref(false)
const guidanceText = ref('')
const guidanceLoading = ref(false)

const renderedGuidance = computed(() => {
  if (guidanceLoading.value) {
    return '' // 加载时显示 spinner，不渲染内容
  }
  // 使用 md 实例渲染 guidanceText 的内容
  return md.render(guidanceText.value || '_等待模型回應中..._')
})

async function handleGetSuggestion() {
  guidanceLoading.value = true
  guidanceModalVisible.value = true
  guidanceText.value = ''
  try {
    // 1. 準備圖片文件 (複用 generateDescription 中的邏輯)
    let imageFile
    if (selectedImage.value.path.startsWith('data:')) {
      const res = await fetch(selectedImage.value.path)
      const blob = await res.blob()
      imageFile = new File([blob], selectedImage.value.description || 'uploaded_image.png', {
        type: blob.type
      })
    } else {
      const res = await fetch(selectedImage.value.path)
      const blob = await res.blob()
      const fileName = selectedImage.value.path.split('/').pop()
      imageFile = new File([blob], fileName, { type: blob.type })
    }

    // 2. 提取 JSON
    let jsonData = localImageDescription.value
    if (jsonData.includes('```json')) {
      const jsonMatch = jsonData.match(/```json\n([\s\S]*?)\n```/)
      if (jsonMatch) {
        jsonData = jsonMatch[1]
      }
    }
    const parsedData = JSON.parse(jsonData)

    // 3. 調用流式API並處理數據
    const reader = await analyzeShortcomingsStream(imageFile, parsedData)
    guidanceLoading.value = false
    const decoder = new TextDecoder()

    const readStream = async () => {
      const { done, value } = await reader.read()
      if (done) {
        return
      }
      guidanceText.value += decoder.decode(value, { stream: true })
      await readStream()
    }

    await readStream()
  } catch (error) {
    console.error('获取指引失败:', error)
    guidanceText.value = `獲取指引失敗: ${error.message || '未知錯誤'}`
    guidanceLoading.value = false
  }
}
</script>

<style scoped>
/* 新增的步驟標題和指引樣式 */
.step-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.step-icon {
  font-size: 28px;
  color: #1890ff;
  margin-right: 12px;
}

.step-title {
  margin-bottom: 0 !important;
  font-weight: 600 !important;
  color: #262626;
}

.step-info {
  margin-bottom: 24px;
  border-radius: 8px;
  font-size: 16px;
}

.step3-image-select-row {
  width: 100%;
  margin-bottom: 32px;
}
.category-nav-scroll {
  display: flex;
  gap: 18px;
  overflow-x: auto;
  padding: 12px 0 18px 0;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.06);
}
.category-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #888;
  font-size: 15px;
  transition: all 0.2s;
  border: 2px solid transparent;
  background: #f7faff;
}
.category-nav-item .cat-icon {
  width: 28px;
  height: 28px;
  margin-bottom: 4px;
  object-fit: contain;
}
.category-nav-item.active {
  color: #1890ff;
  border: 2px solid #1890ff;
  background: #e6f7ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}
.category-nav-item:hover {
  color: #40a9ff;
  background: #f0f7ff;
}
.cat-label {
  font-size: 15px;
  font-weight: 500;
  margin-top: 2px;
}
.main-content-row {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}
.image-select-col {
  flex: 1.2;
  min-width: 320px;
}
.prompt-col {
  flex: 1.5;
  min-width: 340px;
}
.carousel-area {
  margin-bottom: 16px;
}
.image-carousel {
  width: 100%;
  min-height: 220px;
}
.carousel-img-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  transition: box-shadow 0.2s, border 0.2s;
  border-radius: 10px;
}
.carousel-img-wrapper:hover {
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.1);
  background: #f0f7ff;
}
.carousel-img-wrapper img {
  width: 180px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid transparent;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: border 0.2s, box-shadow 0.2s;
}
.carousel-img-wrapper img.selected {
  border: 2px solid #1890ff;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.15);
}
.img-desc {
  margin-top: 8px;
  font-size: 14px;
  color: #555;
  text-align: center;
  word-break: break-all;
}
.upload-area {
  margin: 16px 0 0 0;
  text-align: center;
}

.upload-area :deep(.ant-upload) {
  width: 100%;
}

.upload-area :deep(.ant-upload-drag) {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s ease;
  padding: 20px;
}

.upload-area :deep(.ant-upload-drag:hover) {
  border-color: #1890ff;
  background: #f0f7ff;
}

.upload-area :deep(.ant-upload-drag.ant-upload-drag-hover) {
  border-color: #1890ff;
  background: #e6f7ff;
}

.upload-area :deep(.ant-upload-drag .ant-upload-drag-container) {
  padding: 0;
}

.upload-area :deep(.ant-upload-drag .ant-upload-text) {
  font-size: 14px;
  color: #666;
  margin: 8px 0 0 0;
}

.upload-area :deep(.ant-upload-drag .ant-upload-hint) {
  font-size: 12px;
  color: #999;
  margin: 4px 0 0 0;
}

/* 自定義上傳按鈕樣式 */
.custom-upload-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(82, 196, 26, 0.2);
}

.custom-upload-btn:hover {
  background: linear-gradient(135deg, #73d13d 0%, #52c41a 100%);
  box-shadow: 0 4px 8px rgba(82, 196, 26, 0.3);
  transform: translateY(-1px);
}

.custom-upload-btn:active {
  transform: translateY(0);
}

.custom-upload-btn .upload-icon {
  margin-right: 6px;
  font-size: 16px;
}
/* 優化預覽區域樣式 */
.preview-area {
  margin: 24px 0;
}

.preview-card {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  background: linear-gradient(to bottom, #fafafa, #f0f7ff);
}

.preview-card:hover {
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.15);
}

.preview-card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.preview-card-title :deep(svg) {
  font-size: 20px;
  color: #1890ff;
  margin-right: 8px;
}

.preview-content {
  padding: 16px;
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

/* 新增美觀的圖片邊框 */
.image-frame {
  position: relative;
  padding: 12px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  max-width: 360px;
  width: 100%;
  border: 1px solid #e8e8e8;
}

.image-frame:hover {
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
}

/* 添加裝飾性邊角 */
.frame-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border-color: #1890ff;
  border-style: solid;
  border-width: 0;
  z-index: 1;
}

.frame-corner-tl {
  top: -1px;
  left: -1px;
  border-top-width: 3px;
  border-left-width: 3px;
  border-top-left-radius: 4px;
}

.frame-corner-tr {
  top: -1px;
  right: -1px;
  border-top-width: 3px;
  border-right-width: 3px;
  border-top-right-radius: 4px;
}

.frame-corner-bl {
  bottom: -1px;
  left: -1px;
  border-bottom-width: 3px;
  border-left-width: 3px;
  border-bottom-left-radius: 4px;
}

.frame-corner-br {
  bottom: -1px;
  right: -1px;
  border-bottom-width: 3px;
  border-right-width: 3px;
  border-bottom-right-radius: 4px;
}

.preview-img {
  width: 100%;
  height: auto;
  max-height: 240px;
  object-fit: contain;
  border-radius: 2px;
  transition: all 0.3s ease;
  display: block;
}

.preview-img:hover {
  transform: scale(1.02);
}

.image-info {
  margin-top: 20px;
  text-align: center;
  width: 100%;
  max-width: 360px;
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #1890ff;
}

.image-name {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 8px;
  word-break: break-word;
}

.image-category {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #1890ff;
}

.image-category :deep(svg) {
  margin-right: 4px;
  font-size: 14px;
}

.empty-placeholder {
  padding: 20px;
}

.empty-icon {
  font-size: 48px;
  color: #bfbfbf;
}
.prompt-form {
  margin-top: 0;
}
.form-label :deep(.ant-form-item-label > label) {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}
.prompt-textarea {
  border-radius: 8px;
  font-size: 16px;
  resize: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}
.prompt-textarea:hover {
  border-color: #40a9ff;
}
.action-buttons {
  margin-top: 16px;
}
.generate-btn,
.next-btn,
.render-btn {
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  padding: 0 20px;
}
.generate-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  border: none;
}
.render-btn {
  background: linear-gradient(135deg, #722ed1 0%, #096dd9 100%);
  color: #fff;
  border: none;
}
.next-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
  border: none;
}
.generate-btn:disabled,
.next-btn:disabled,
.render-btn:disabled {
  background: #f5f5f5;
  color: #aaa;
  border: 1px solid #d9d9d9;
}
.result-collapse {
  margin-top: 36px;
  background-color: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}
.collapse-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}
.collapse-header :deep(svg) {
  margin-right: 8px;
  font-size: 20px;
  color: #1890ff;
}
.description-result {
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  font-size: 16px;
  line-height: 1.8;
  user-select: text;
}

.scrollable-result {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
}
.markdown-content {
  color: #262626;
}
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 16px;
  margin-bottom: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: #262626;
}
.markdown-content :deep(h1) {
  font-size: 24px;
}
.markdown-content :deep(h2) {
  font-size: 22px;
}
.markdown-content :deep(h3) {
  font-size: 20px;
}
.markdown-content :deep(h4) {
  font-size: 18px;
}
.markdown-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.8;
}
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}
.markdown-content :deep(li) {
  margin-bottom: 6px;
}
.markdown-content :deep(a) {
  color: #1890ff;
  text-decoration: none;
}
.markdown-content :deep(a:hover) {
  text-decoration: underline;
}
.markdown-content :deep(blockquote) {
  padding: 8px 16px;
  margin: 16px 0;
  border-left: 4px solid #1890ff;
  background-color: #e6f7ff;
  color: #595959;
}
.markdown-content :deep(code) {
  background-color: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 14px;
}
.markdown-content :deep(pre) {
  background-color: #f0f2f5;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 16px 0;
}
.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}
.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}
.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}
.markdown-content :deep(th) {
  background-color: #fafafa;
  font-weight: 600;
}
.markdown-content :deep(tr:nth-child(even)) {
  background-color: #fafafa;
}
@media (max-width: 900px) {
  .main-content-row {
    flex-direction: column;
    gap: 16px;
  }
  .image-select-col,
  .prompt-col {
    min-width: 0;
    width: 100%;
  }
  .carousel-img-wrapper img {
    width: 120px;
    height: 80px;
  }
  .preview-img {
    max-width: 180px;
    max-height: 120px;
  }
  .step3-image-select-row {
    padding: 10px;
  }
}

.image-selector-area {
  margin-bottom: 16px;
}

.selector-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  background: #fafafa;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  margin-bottom: 16px;
}

.select-image-btn {
  height: 60px;
  font-size: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.selected-category-info {
  font-size: 14px;
  color: #666;
}

.category-label {
  font-weight: 500;
  color: #1890ff;
}

.image-selector-modal {
  border-radius: 12px;
}

.image-selector-modal :deep(.ant-modal-content) {
  border-radius: 12px;
  overflow: hidden;
}

.image-selector-modal :deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
}

.image-selector-modal :deep(.ant-modal-body) {
  padding: 0;
}

.image-selector-content {
  padding: 0;
}

.image-carousel {
  width: 100%;
  min-height: 250px;
  position: relative;
}

.carousel-img-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 16px;
  transition: all 0.3s ease;
  border-radius: 12px;
  margin: 0 8px;
}

.carousel-img-wrapper:hover {
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.15);
  background: #f0f7ff;
  transform: translateY(-2px);
}

.carousel-img-wrapper img {
  width: 160px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.carousel-img-wrapper img.selected {
  border: 2px solid #1890ff;
  box-shadow: 0 4px 16px rgba(24, 144, 255, 0.25);
  transform: scale(1.05);
}

.img-desc {
  margin-top: 12px;
  font-size: 14px;
  color: #555;
  text-align: center;
  word-break: break-all;
  font-weight: 500;
}

/* 優化箭頭樣式 */
.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e8e8e8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #1890ff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  z-index: 10;
}

.carousel-arrow:hover {
  background: #1890ff;
  color: white;
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.3);
  transform: translateY(-50%) scale(1.1);
}

/* 調整選擇框大小 */
.selector-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  background: #fafafa;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  margin-bottom: 16px;
  min-height: 120px;
  justify-content: center;
}

.select-image-btn {
  height: 48px;
  font-size: 14px;
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 0 20px;
}

.selected-category-info {
  font-size: 13px;
  color: #666;
}

.category-label {
  font-weight: 500;
  color: #1890ff;
}

/* 上傳按鈕導航項樣式 */
.upload-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 80px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #888;
  font-size: 15px;
  transition: all 0.2s;
  border: 2px solid transparent;
  background: transparent;
}

.upload-nav-btn {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 70px;
}

.upload-nav-btn:hover {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  transform: translateY(-1px);
}

.upload-nav-btn:active {
  transform: translateY(0);
}

.upload-nav-btn :deep(.anticon) {
  font-size: 14px;
  margin-right: 4px;
}

/* 移除原有的上傳區域樣式 */
.upload-area {
  display: none;
}

/* 響應式調整 */
@media (max-width: 768px) {
  .image-selector-modal {
    width: 95% !important;
    margin: 0 auto;
  }

  .carousel-img-wrapper img {
    width: 120px;
    height: 90px;
  }

  .carousel-arrow {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }
}

/* 優化輪播圖樣式 */
.image-selector-modal {
  border-radius: 12px;
}

.image-selector-modal :deep(.ant-modal-content) {
  border-radius: 12px;
  overflow: hidden;
}

.image-selector-modal :deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
  background: #fafafa;
}

.image-selector-modal :deep(.ant-modal-title) {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.image-selector-modal :deep(.ant-modal-body) {
  padding: 0;
}

.image-selector-content {
  padding: 0;
}

.category-info {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(to right, #f7faff, #e6f7ff);
  border-bottom: 1px solid #e6f7ff;
}

.category-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
  padding: 8px;
}

.category-icon img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.category-description h3 {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  margin: 0 0 4px 0;
}

.category-description p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.image-carousel {
  width: 100%;
  padding: 24px;
  background: white;
}

.carousel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.carousel-img-wrapper {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  position: relative;
}

.img-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.carousel-img-wrapper:hover .img-card {
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
  transform: translateY(-2px);
}

.img-preview {
  position: relative;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
}

.img-preview img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.carousel-img-wrapper:hover .img-preview img {
  transform: scale(1.05);
}

.select-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(24, 144, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
}

.select-overlay :deep(svg) {
  font-size: 32px;
  color: white;
}

.carousel-img-wrapper.selected .select-overlay {
  opacity: 1;
}

.carousel-img-wrapper.selected .img-card {
  box-shadow: 0 0 0 2px #1890ff, 0 4px 12px rgba(24, 144, 255, 0.2);
}

.img-desc {
  padding: 12px;
  font-size: 14px;
  color: #262626;
  text-align: center;
  background: white;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  word-break: break-word;
  line-height: 1.4;
}

.carousel-arrow {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  color: #1890ff;
  font-size: 16px;
  z-index: 10;
  transition: all 0.3s ease;
  cursor: pointer;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

.carousel-arrow-prev {
  left: -20px;
}

.carousel-arrow-next {
  right: -20px;
}

.carousel-arrow:hover {
  background: #1890ff;
  color: white;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

/* 自定義輪播指示點樣式 */
.image-carousel :deep(.slick-dots) {
  bottom: -5px;
}

.image-carousel :deep(.slick-dots li button) {
  background: #d9d9d9;
  border-radius: 4px;
  width: 8px;
  height: 8px;
}

.image-carousel :deep(.slick-dots li.slick-active button) {
  background: #1890ff;
  width: 24px;
}

/* 移除原有的覆蓋層預覽樣式 */
.preview-overlay {
  display: none;
}

/* 增強輪播圖內圖片懸停效果 */
.carousel-img-wrapper {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  position: relative;
}

.img-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

/* 普通懸停效果 */
.carousel-img-wrapper:hover .img-card {
  box-shadow: 0 8px 20px rgba(24, 144, 255, 0.2);
  transform: translateY(-4px);
}

/* 懸停放大效果 */
.carousel-img-wrapper.hovering {
  z-index: 100;
  position: relative;
}

.carousel-img-wrapper.hovering .img-card {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  transform: none;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
}

.carousel-img-wrapper.hovering .img-preview {
  height: 75%;
}

.img-preview {
  position: relative;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
  transition: all 0.3s ease;
}

.img-preview img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.carousel-img-wrapper:hover .img-preview img {
  transform: scale(1.08);
}

/* 懸停覆蓋層 */
.hover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
}

.hover-overlay :deep(svg) {
  font-size: 32px;
  color: white;
}

.carousel-img-wrapper:hover .hover-overlay {
  opacity: 1;
}

.carousel-img-wrapper.selected .hover-overlay {
  display: none;
}

/* 調整網格佈局，確保有足夠空間放大 */
.carousel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
  padding: 24px 0;
  position: relative;
}

/* 調整輪播容器 */
.image-carousel {
  width: 100%;
  padding: 24px;
  background: white;
  overflow: visible;
}

.image-carousel :deep(.slick-list) {
  overflow: visible;
  padding: 20px 0;
}

.image-carousel :deep(.slick-track) {
  display: flex;
  align-items: stretch;
}

/* 示例提示詞樣式 */
.example-prompts {
  margin-top: 12px;
  border-top: 1px dashed #e8e8e8;
  padding-top: 12px;
}

.example-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 8px;
}

.example-title :deep(svg) {
  font-size: 14px;
  color: #1890ff;
  margin-right: 6px;
}

.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-item {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  background: #f0f7ff;
  border: 1px solid #e6f7ff;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 13px;
  color: #1890ff;
}

.example-item:hover {
  background: #e6f7ff;
  border-color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.15);
}

.example-item :deep(svg) {
  font-size: 14px;
  margin-right: 4px;
  color: #1890ff;
}

/* 示例布局弹窗樣式 */
.example-layout-modal {
  border-radius: 12px;
}

.example-layout-modal :deep(.ant-modal-content) {
  border-radius: 12px;
  overflow: hidden;
}

.example-layout-modal :deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
  background: #fafafa;
}

.example-layout-modal :deep(.ant-modal-title) {
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.example-layout-content {
  padding: 16px;
}

/* 案例選擇器 */
.example-case-selector {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.selector-label {
  font-weight: 500;
  margin-right: 12px;
  color: #262626;
}

/* 布局網格 */
.example-layout-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

/* 每個區域的樣式 */
.layout-section {
  display: flex;
  flex-direction: column;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.section-title {
  padding: 10px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;
  font-weight: 500;
  color: #262626;
  display: flex;
  align-items: center;
}

.section-subtitle {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: normal;
  margin-left: 8px;
}

.copy-btn {
  margin-left: auto;
  padding: 0 4px;
}

.section-content {
  padding: 16px;
  flex-grow: 1;
  min-height: 200px;
  max-height: 300px;
  overflow: auto;
}

/* 圖片區域 */
.image-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.example-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 提示詞區域 */
.prompt-section {
  font-size: 14px;
  line-height: 1.6;
}

/* 結果區域 */
.result-section {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
}

.json-result {
  margin: 0;
  white-space: pre-wrap;
  color: #333;
}

.markdown-result {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
}

.markdown-result :deep(h1) {
  font-size: 20px;
  margin-top: 0;
}

.markdown-result :deep(h2) {
  font-size: 16px;
}

.markdown-result :deep(ul) {
  padding-left: 20px;
}

/* 操作按鈕 */
.example-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 自定義組件樣式 */
.custom-component-modal {
  border-radius: 12px;
}

.custom-component-modal :deep(.ant-modal-content) {
  border-radius: 12px;
  overflow: hidden;
}

.custom-component-content {
  padding: 16px;
}

.placeholder-component {
  background: #f9f9f9;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  padding: 20px;
  min-height: 300px;
}

.placeholder-header {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.placeholder-header :deep(svg) {
  font-size: 20px;
  color: #1890ff;
  margin-right: 8px;
}

.placeholder-body {
  font-size: 14px;
  line-height: 1.6;
  color: #595959;
}

.placeholder-body ul {
  padding-left: 20px;
  margin-top: 12px;
}

.placeholder-body li {
  margin-bottom: 8px;
}

.custom-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 場景圖可視化樣式 */
.scene-graph-visualization {
  margin-top: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  background: #fff;
}

.visualization-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.visualization-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.visualization-content {
  height: 400px;
  width: 100%;
}

/* 場景圖模態框樣式 */
.scene-graph-modal {
  border-radius: 12px;
}

.scene-graph-modal :deep(.ant-modal-content) {
  border-radius: 12px;
  overflow: hidden;
}

.scene-graph-modal :deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
  background: #fafafa;
}

.scene-graph-modal :deep(.ant-modal-body) {
  padding: 0;
}

.scene-graph-content {
  height: 700px;
  width: 100%;
}

.guidance-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.guidance-text {
  margin-left: 12px;
  font-size: 14px;
  color: #595959;
  font-weight: 500;
}

.guidance-modal-content {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif, 'Apple Color Emoji',
    'Segoe UI Emoji', 'Segoe UI Symbol';
  font-size: 15px;
  line-height: 1.8;
  color: #262626;
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 8px;
}
</style>