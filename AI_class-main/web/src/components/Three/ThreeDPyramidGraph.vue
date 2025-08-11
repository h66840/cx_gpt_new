<template>
  <div class="graph-component">
    <div ref="graphContainer" class="graph-container">
      </div>
    <div class="controls-panel">
      <input
        type="text"
        v-model="searchText"
        class="search-input"
        placeholder="输入节点ID或名称（多个用逗号分隔）"
        @keypress.enter="handleHighlight"
      />
      <button @click="handleHighlight" class="highlight-button">高亮</button>
      <button @click="handleClear" class="clear-button">清除高亮</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';

// 1. 定义组件的 Props
const props = defineProps({
  graphData: {
    type: Object,
    required: true,
  },
  layoutConfig: {
    type: Object,
    default: () => ({
      layerHeight: -70,
      horizontalSpacing: 50,
    }),
  },
  bloomParams: {
    type: Object,
    default: () => ({
      exposure: 1,
      bloomStrength: 1.5,
      bloomThreshold: 0,
      bloomRadius: 0,
    }),
  },
  nodeRadius: {
    type: Number,
    default: 8,
  },
});

// 2. 定义响应式变量和 DOM 引用
const graphContainer = ref(null);
const searchText = ref('');
let sceneGraph = null; // 用于存储 SceneGraph 类的实例

// 3. 将核心逻辑封装在 onMounted 钩子中
onMounted(() => {
  if (graphContainer.value) {
    // 确保 `SceneGraph` 类和布局函数在 `onMounted` 内部或外部定义
    sceneGraph = new SceneGraph(graphContainer.value, {
      nodeRadius: props.nodeRadius,
      bloomParams: props.bloomParams,
    });
    
    // 首次绘制图表
    drawChart();
  }
});

// 4. 监听数据变化，动态更新图表
watch(
  () => props.graphData,
  (newData) => {
    if (newData && sceneGraph) {
      console.log('Graph data changed, redrawing chart.');
      drawChart();
    }
  },
  { deep: true } // 使用深度监听确保对象内部变化也能被捕获
);

// 5. 在组件卸载时清理资源
onUnmounted(() => {
  if (sceneGraph) {
    sceneGraph.destroy();
    sceneGraph = null;
  }
});

// --- 辅助函数和类 ---

function drawChart() {
  const processedData = generatePyramidLayout(props.graphData, props.layoutConfig);
  sceneGraph.createChart(processedData);
}

const handleHighlight = () => {
  if (sceneGraph) {
    sceneGraph.searchAndHighlight(searchText.value);
  }
};

const handleClear = () => {
  if (sceneGraph) {
    searchText.value = '';
    sceneGraph.clearHighlights();
  }
};

/**
 * 文本精灵图生成函数 (保持不变)
 */
function createTextSprite(text, options = {}) {
  const { fontsize = 48, fontface = 'Arial', textColor = { r: 255, g: 255, b: 255, a: 1.0 } } = options;
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  context.font = `Bold ${fontsize}px ${fontface}`;
  const metrics = context.measureText(text);
  const textWidth = metrics.width;
  canvas.width = textWidth + 10;
  canvas.height = fontsize + 10;
  context.font = `Bold ${fontsize}px ${fontface}`;
  context.fillStyle = `rgba(${textColor.r}, ${textColor.g}, ${textColor.b}, ${textColor.a})`;
  context.fillText(text, 5, fontsize + 2);
  const texture = new THREE.Texture(canvas);
  texture.needsUpdate = true;
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  const sprite = new THREE.Sprite(spriteMaterial);
  sprite.scale.set(canvas.width / 4, canvas.height / 4, 1.0);
  return sprite;
}

/**
 * 金字塔布局生成器 (保持不变)
 */
function generatePyramidLayout(graphData, config) {
    const { nodes, edges } = graphData;
    const { layerHeight, horizontalSpacing } = config;

    const adj = new Map();
    const inDegree = new Map();
    nodes.forEach(node => {
        adj.set(node.id, []);
        inDegree.set(node.id, 0);
    });

    edges.forEach(edge => {
        adj.get(edge.source).push(edge.target);
        inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    const rootNodes = nodes.filter(node => inDegree.get(node.id) === 0).map(n => n.id);
    if (rootNodes.length === 0) {
        console.error("未找到根节点 (入度为0的节点)");
        return graphData;
    }

    const layers = [];
    const queue = [...rootNodes];
    const visited = new Set(rootNodes);

    while (queue.length > 0) {
        const currentLayerSize = queue.length;
        const currentLayer = [];
        for (let i = 0; i < currentLayerSize; i++) {
            const u = queue.shift();
            currentLayer.push(u);
            (adj.get(u) || []).forEach(v => {
                if (!visited.has(v)) {
                    visited.add(v);
                    queue.push(v);
                }
            });
        }
        layers.push(currentLayer);
    }

    const nodePositions = new Map();
    layers.forEach((layer, layerIndex) => {
        const numNodesInLayer = layer.length;
        const layerRadius = (layerIndex > 0) ? (layerIndex * horizontalSpacing) : 0;

        layer.forEach((nodeId, nodeIndex) => {
            const angle = (numNodesInLayer > 1) ? (2 * Math.PI / numNodesInLayer) * nodeIndex : 0;
            const x = layerRadius * Math.cos(angle);
            const y = layerIndex * layerHeight;
            const z = layerRadius * Math.sin(angle);
            nodePositions.set(nodeId, { x, y, z });
        });
    });

    const positionedNodes = nodes.map(node => ({
        ...node,
        position: nodePositions.get(node.id) || { x: 0, y: 0, z: 0 }
    }));

    return { nodes: positionedNodes, edges };
}

/**
 * 核心场景图类 (大部分逻辑保持不变, 构造函数和销毁函数有调整)
 */
class SceneGraph {
  constructor(container, options = {}) {
    this.container = container;
    this.nodeRadius = options.nodeRadius || 8;
    this.bloomParams = options.bloomParams || {};
    
    // --- State properties ---
    this.originalNodeColors = new Map();
    this.originalEdgeColors = new Map();
    this.nodeMeshes = new Map();
    this.edgeArrows = new Map();
    this.glowingObjects = new Set();
    this.nonGlowingObjects = new Set();
    this.highlightedObjects = new Set();
    this.baseHighlightColor = new THREE.Color(0x00ff00);
    this.animationFrameId = null;

    this.init();
  }

  init() {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 2000);
    this.camera.position.set(0, -80, 250);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.target.set(0, -100, 0);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(50, 50, 50);
    this.scene.add(directionalLight);

    this.composer = new EffectComposer(this.renderer);
    this.renderPass = new RenderPass(this.scene, this.camera);
    this.composer.addPass(this.renderPass);

    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
      this.bloomParams.bloomStrength,
      this.bloomParams.bloomRadius,
      this.bloomParams.bloomThreshold
    );
    this.composer.addPass(this.bloomPass);

    window.addEventListener('resize', this.onWindowResize);
    this.animate();
  }

  // 使用箭头函数确保 `this` 指向类实例
  onWindowResize = () => {
    this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.composer.setSize(this.container.clientWidth, this.container.clientHeight);
  }

  createChart(graphData) {
    const { nodes, edges } = graphData;

    // Clear previous graph elements
    if (this.graphGroup) {
      this.scene.remove(this.graphGroup);
      this.graphGroup.traverse(object => {
          if (object.geometry) object.geometry.dispose();
          if (object.material) {
              if (Array.isArray(object.material)) {
                  object.material.forEach(material => material.dispose());
              } else {
                  object.material.dispose();
              }
          }
          if(object.texture) object.texture.dispose();
      });
    }

    this.graphGroup = new THREE.Group();
    this.scene.add(this.graphGroup);

    this.nodeMeshes.clear();
    this.edgeArrows.clear();
    this.originalNodeColors.clear();
    this.originalEdgeColors.clear();
    this.glowingObjects.clear();
    this.nonGlowingObjects.clear();
    this.highlightedObjects.clear();

    this.graphNodes = nodes;
    this.graphEdges = edges;

    nodes.forEach(node => {
      const position = new THREE.Vector3(node.position.x, node.position.y, node.position.z);
      const color = new THREE.Color(node.color || '#ffffff');
      const geometry = new THREE.SphereGeometry(this.nodeRadius, 32, 16);
      const material = new THREE.MeshBasicMaterial({ color: color, wireframe: true });

      const nodeMesh = new THREE.Mesh(geometry, material);
      nodeMesh.position.copy(position);
      nodeMesh.userData = { id: node.id, type: 'node' };
      this.graphGroup.add(nodeMesh);
      this.nodeMeshes.set(node.id, nodeMesh);
      this.originalNodeColors.set(node.id, color.getHex());
      this.nonGlowingObjects.add(nodeMesh);

      const text = createTextSprite(node.name, { fontsize: 32 });
      text.position.set(position.x + this.nodeRadius, position.y + this.nodeRadius, position.z);
      this.graphGroup.add(text);
      this.nonGlowingObjects.add(text);
    });

    edges.forEach(edge => {
      const sourceNode = this.nodeMeshes.get(edge.source);
      const targetNode = this.nodeMeshes.get(edge.target);
      if (!sourceNode || !targetNode) return;

      const startPoint = sourceNode.position;
      const endPoint = targetNode.position;
      const direction = new THREE.Vector3().subVectors(endPoint, startPoint).normalize();
      const distance = startPoint.distanceTo(endPoint);
      const arrowLength = distance - this.nodeRadius * 2;
      if (arrowLength <= 0) return;

      const newStartPoint = new THREE.Vector3().addVectors(startPoint, direction.clone().multiplyScalar(this.nodeRadius));
      const hexColor = new THREE.Color(edge.color || '#ffffff').getHex();
      const arrowHelper = new THREE.ArrowHelper(direction, newStartPoint, arrowLength, hexColor, 8, 4);
      arrowHelper.userData = { id: `${edge.source}-${edge.target}`, type: 'edge', source: edge.source, target: edge.target };
      
      this.graphGroup.add(arrowHelper);
      this.edgeArrows.set(arrowHelper.userData.id, arrowHelper);
      this.originalEdgeColors.set(arrowHelper.userData.id, hexColor);
      this.nonGlowingObjects.add(arrowHelper.line);
      this.nonGlowingObjects.add(arrowHelper.cone);
    });
  }

  // --- 高亮和辉光方法 (保持不变) ---
  darkenNonGlowingObjects() {
      this.nonGlowingObjects.forEach(obj => {
          if (obj.material) {
              if (!obj.userData.originalMaterial) {
                  obj.userData.originalMaterial = obj.material;
              }
              obj.material = new THREE.MeshBasicMaterial({ color: 0x000000 });
          }
      });
  }

  restoreOriginalMaterials() {
      this.nonGlowingObjects.forEach(obj => {
          if (obj.userData.originalMaterial) {
              obj.material = obj.userData.originalMaterial;
              delete obj.userData.originalMaterial;
          }
      });
  }
  
  highlightObject(object, highlightColor) {
    let objForGlowing = null;
    if (object.isMesh && object.userData.type === 'node') {
        if (!this.originalNodeColors.has(object.userData.id)) {
            this.originalNodeColors.set(object.userData.id, object.material.color.getHex());
        }
        object.material.color.set(highlightColor);
        object.material.color.multiplyScalar(2.0);
        objForGlowing = object;
    } else if (object.isArrowHelper && object.userData.type === 'edge') {
        if (!this.originalEdgeColors.has(object.userData.id)) {
            this.originalEdgeColors.set(object.userData.id, object.line.material.color.getHex());
        }
        object.line.material.color.set(highlightColor);
        object.line.material.color.multiplyScalar(2.0);
        object.cone.material.color.set(highlightColor);
        object.cone.material.color.multiplyScalar(2.0);
        objForGlowing = [object.line, object.cone];
    }

    if (objForGlowing) {
        if (Array.isArray(objForGlowing)) {
            objForGlowing.forEach(o => {
                this.nonGlowingObjects.delete(o);
                this.glowingObjects.add(o);
            });
        } else {
            this.nonGlowingObjects.delete(objForGlowing);
            this.glowingObjects.add(objForGlowing);
        }
    }
    this.highlightedObjects.add(object);
  }

  resetObjectColor(object) {
    let objForGlowing = null;
    if (object.isMesh && object.userData.type === 'node') {
        const originalColor = this.originalNodeColors.get(object.userData.id);
        if (originalColor !== undefined) {
            object.material.color.set(originalColor);
        }
        objForGlowing = object;
    } else if (object.isArrowHelper && object.userData.type === 'edge') {
        const originalColor = this.originalEdgeColors.get(object.userData.id);
        if (originalColor !== undefined) {
            object.line.material.color.set(originalColor);
            object.cone.material.color.set(originalColor);
        }
        objForGlowing = [object.line, object.cone];
    }
    if (objForGlowing) {
        if (Array.isArray(objForGlowing)) {
            objForGlowing.forEach(o => {
                this.glowingObjects.delete(o);
                this.nonGlowingObjects.add(o);
            });
        } else {
            this.glowingObjects.delete(objForGlowing);
            this.nonGlowingObjects.add(objForGlowing);
        }
    }
    this.highlightedObjects.delete(object);
  }

  clearHighlights() {
    Array.from(this.highlightedObjects).forEach(obj => {
        this.resetObjectColor(obj);
    });
    this.highlightedObjects.clear();
  }

  searchAndHighlight(namesToSearchStr) {
    this.clearHighlights();
    const highlightColor = this.baseHighlightColor;
    const searchTerms = namesToSearchStr.split(',').map(term => term.trim().toLowerCase()).filter(term => term !== '');

    if (searchTerms.length === 0) return;

    const foundNodeIds = new Set();
    searchTerms.forEach(term => {
        const foundNode = this.graphNodes.find(
            node => node.name.toLowerCase() === term || node.id.toLowerCase() === term
        );
        if (foundNode) {
            const nodeMesh = this.nodeMeshes.get(foundNode.id);
            if (nodeMesh) {
                this.highlightObject(nodeMesh, highlightColor);
                foundNodeIds.add(foundNode.id);
            }
        }
    });

    if (foundNodeIds.size === 0) return;

    this.graphEdges.forEach(edge => {
        if (foundNodeIds.has(edge.source) && foundNodeIds.has(edge.target)) {
            const edgeId = `${edge.source}-${edge.target}`;
            const edgeArrow = this.edgeArrows.get(edgeId);
            if (edgeArrow) {
                this.highlightObject(edgeArrow, highlightColor);
            }
        }
    });
  }

  animate = () => {
    this.animationFrameId = requestAnimationFrame(this.animate);
    this.controls.update();

    this.darkenNonGlowingObjects();
    this.composer.render();
    this.restoreOriginalMaterials();
    
    // 最终渲染以确保所有内容（包括非辉光对象和文本）都正确显示
    this.renderer.render(this.scene, this.camera);
  }

  // --- 新增销毁方法 ---
  destroy() {
    console.log('Destroying SceneGraph instance.');
    // 停止动画循环
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    // 移除事件监听
    window.removeEventListener('resize', this.onWindowResize);

    // 释放 Three.js 资源
    if (this.graphGroup) {
         this.scene.remove(this.graphGroup);
         this.graphGroup.traverse(object => {
          if (object.geometry) object.geometry.dispose();
          if (object.material) {
              if (Array.isArray(object.material)) {
                  object.material.forEach(material => material.dispose());
              } else {
                  object.material.dispose();
              }
          }
          if(object.texture) object.texture.dispose();
      });
    }
    this.renderer.dispose();
    
    // 从 DOM 中移除 canvas
    if (this.renderer.domElement.parentElement) {
        this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
  }
}
</script>

<style scoped>
/* 所有的 CSS 样式都从原 HTML 文件中复制到这里 */
.graph-component {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #222;
  color: #eee;
  overflow: hidden;
}

.graph-container {
  flex-grow: 1;
  width: 100%;
  background-color: black;
  position: relative;
}

.controls-panel {
  width: 100%;
  padding: 15px;
  background-color: #333;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #555;
  border-radius: 4px;
  background-color: #444;
  color: #eee;
  font-size: 1em;
  width: 350px;
  outline: none;
}

.search-input::placeholder {
  color: #bbb;
}

.highlight-button,
.clear-button {
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.2s ease;
}

.highlight-button:hover,
.clear-button:hover {
  background-color: #0056b3;
}

.clear-button {
  background-color: #dc3545;
}

.clear-button:hover {
  background-color: #c82333;
}
</style>