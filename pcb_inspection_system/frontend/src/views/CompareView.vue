<template>
  <div class="compare">
    <div class="page-title">
      <el-icon :size="28"><CopyDocument /></el-icon>
      <span>原图 vs 检测结果对比</span>
      <el-tag type="success" size="small">并排对比｜热力图分析</el-tag>
    </div>

    <div class="card">
      <!-- 上传区 -->
      <div class="upload-area">
        <el-upload
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleImageSelect"
          accept="image/*"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">点击或拖拽上传 PCB 图片</div>
          <div class="upload-hint">支持 JPG / PNG</div>
        </el-upload>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!selectedFile"
          @click="detectAndCompare"
          class="detect-btn"
        >
          <el-icon><Search /></el-icon> 开始检测
        </el-button>
      </div>

      <!-- 选项卡切换：缺陷标注 / 热力图 -->
      <div v-if="showResult" class="view-tabs">
        <el-radio-group v-model="viewMode" size="large">
          <el-radio-button value="annotated">
            <el-icon><Warning /></el-icon> 缺陷标注图
          </el-radio-button>
          <el-radio-button value="heatmap">
            <el-icon><TrendCharts /></el-icon> 缺陷热力图
          </el-radio-button>
          <el-radio-button value="overlay">
            <el-icon><Layers /></el-icon> 热力叠加图
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 左右对比区 -->
      <div v-if="showResult" class="compare-container">
        <div class="compare-item">
          <div class="compare-header">
            <el-icon><Picture /></el-icon>
            <span>原始图片</span>
          </div>
          <el-image :src="originalImgUrl" fit="contain" class="compare-img" ref="originalImageRef" />
        </div>

        <div class="compare-divider">
          <el-icon><Right /></el-icon>
        </div>

        <div class="compare-item">
          <div class="compare-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>{{ viewModeLabel }}</span>
            <el-tag v-if="viewMode === 'annotated'" type="danger" size="small">
              缺陷数: {{ detectResult?.defect_count || 0 }}
            </el-tag>
            <el-tag v-else type="warning" size="small">
              密度越高红色越深
            </el-tag>
          </div>

          <!-- 缺陷标注图 -->
          <el-image
            v-if="viewMode === 'annotated'"
            :src="detectImgUrl"
            fit="contain"
            class="compare-img"
          />

          <!-- 纯热力图 -->
          <canvas
            v-if="viewMode === 'heatmap'"
            ref="heatmapCanvas"
            class="compare-img"
            style="background: #1a1a2e;"
          ></canvas>

          <!-- 热力叠加图 -->
          <canvas
            v-if="viewMode === 'overlay'"
            ref="overlayCanvas"
            class="compare-img"
          ></canvas>
        </div>
      </div>

      <!-- 缺陷列表 -->
      <div v-if="detectResult?.defects?.length" class="defect-summary">
        <div class="summary-header">
          <el-icon><List /></el-icon>
          <span>检出缺陷明细</span>
        </div>
        <el-table :data="detectResult.defects" stripe border>
          <el-table-column prop="class" label="缺陷类型">
            <template #default="{ row }">
              <el-tag :type="getDefectType(row.class)">{{ row.class }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="200">
            <template #default="{ row }">
              <el-progress
                :percentage="row.confidence * 100"
                :color="row.confidence > 0.7 ? '#67c23a' : '#e6a23c'"
              />
            </template>
          </el-table-column>
          <el-table-column label="位置信息">
            <template #default="{ row }">
              [{{ row.bbox?.join(', ') || '无位置信息' }}]
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { saveDetection } from '@/stores/history'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const selectedFile = ref(null)
const originalImgUrl = ref('')
const detectImgUrl = ref('')
const detectResult = ref(null)
const loading = ref(false)
const showResult = ref(false)
const viewMode = ref('annotated')
const heatmapCanvas = ref(null)
const overlayCanvas = ref(null)
const originalImageRef = ref(null)

const viewModeLabel = ref({
  annotated: '缺陷标注图',
  heatmap: '缺陷热力图',
  overlay: '热力叠加图'
})

function getDefectType(type) {
  const map = {
    missing_hole: 'danger',
    mouse_bite: 'warning',
    open_circuit: 'info',
    short: 'danger',
    spur: 'warning',
    spurious_copper: 'success'
  }
  return map[type] || 'info'
}

function handleImageSelect(uploadFile) {
  const file = uploadFile.raw
  selectedFile.value = file
  originalImgUrl.value = URL.createObjectURL(file)
  showResult.value = false
  detectResult.value = null
  detectImgUrl.value = ''
  ElMessage.success('图片已加载，点击检测')
}

async function detectAndCompare() {
  if (!selectedFile.value) return

  loading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const res = await axios.post('http://localhost:8000/detect', formData)

    detectResult.value = res.data
    detectImgUrl.value = res.data.result_image
    showResult.value = true
    viewMode.value = 'annotated'

    // ===== 保存到历史记录 =====
    await saveDetection({
      filename: selectedFile.value.name,
      defect_count: res.data.defect_count,
      defects: res.data.defects,
      userId: userStore.currentUser?.id,
      username: userStore.currentUser?.username
    })
    // ==========================

    ElMessage.success(`检测完成，发现 ${res.data.defect_count} 处缺陷`)

    // 等待 DOM 更新后生成热力图
    await nextTick()
    generateHeatmap()
  } catch (err) {
    console.error(err)
    ElMessage.error('检测失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

// 生成热力图
async function generateHeatmap() {
  if (!detectResult.value?.defects?.length) return

  // 等待图片加载完成
  const img = new Image()
  img.src = originalImgUrl.value
  img.onload = () => {
    const width = img.width
    const height = img.height

    // 设置 canvas 尺寸
    if (heatmapCanvas.value) {
      heatmapCanvas.value.width = width
      heatmapCanvas.value.height = height
      drawHeatmapOnCanvas(heatmapCanvas.value, width, height)
    }

    if (overlayCanvas.value) {
      overlayCanvas.value.width = width
      overlayCanvas.value.height = height
      drawOverlayHeatmap(overlayCanvas.value, img, width, height)
    }
  }
}

// 绘制纯热力图
function drawHeatmapOnCanvas(canvas, width, height) {
  const ctx = canvas.getContext('2d')

  // 创建热力图数据点
  const points = detectResult.value.defects.map(d => ({
    x: (d.bbox[0] + d.bbox[2]) / 2,  // 中心点 x
    y: (d.bbox[1] + d.bbox[3]) / 2,  // 中心点 y
    value: d.confidence * 100  // 权重 = 置信度
  }))

  // 清空画布
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, width, height)

  // 为每个点绘制高斯模糊圆
  points.forEach(point => {
    const radius = Math.min(width, height) * 0.08  // 半径
    const intensity = Math.min(1, point.value / 100)  // 强度 0-1

    // 颜色映射：蓝 -> 绿 -> 黄 -> 红
    let r, g, b
    if (intensity < 0.33) {
      r = 0
      g = intensity * 3 * 255
      b = 255
    } else if (intensity < 0.66) {
      r = (intensity - 0.33) * 3 * 255
      g = 255
      b = 255 - (intensity - 0.33) * 3 * 255
    } else {
      r = 255
      g = 255 - (intensity - 0.66) * 3 * 255
      b = 0
    }

    ctx.save()
    ctx.shadowBlur = radius
    ctx.shadowColor = `rgba(${r}, ${g}, ${b}, ${intensity * 0.8})`
    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${intensity * 0.6})`
    ctx.beginPath()
    ctx.arc(point.x, point.y, radius / 2, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()
  })
}

// 绘制热力叠加图（热力图 + 原图）
function drawOverlayHeatmap(canvas, originalImg, width, height) {
  const ctx = canvas.getContext('2d')

  // 先绘制原图
  ctx.drawImage(originalImg, 0, 0, width, height)

  // 获取图像数据用于叠加
  const imageData = ctx.getImageData(0, 0, width, height)
  const data = imageData.data

  // 生成热力图叠加层
  const points = detectResult.value.defects.map(d => ({
    x: (d.bbox[0] + d.bbox[2]) / 2,
    y: (d.bbox[1] + d.bbox[3]) / 2,
    value: d.confidence * 100
  }))

  // 为每个像素计算热力强度（简化版：只在高斯半径内处理）
  const radius = Math.min(width, height) * 0.08
  points.forEach(point => {
    const startX = Math.max(0, Math.floor(point.x - radius))
    const endX = Math.min(width, Math.ceil(point.x + radius))
    const startY = Math.max(0, Math.floor(point.y - radius))
    const endY = Math.min(height, Math.ceil(point.y + radius))

    for (let y = startY; y < endY; y++) {
      for (let x = startX; x < endX; x++) {
        const dx = x - point.x
        const dy = y - point.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        if (distance < radius) {
          const intensity = (1 - distance / radius) * (point.value / 100)
          const idx = (y * width + x) * 4

          // 叠加红色调
          data[idx] = Math.min(255, data[idx] + intensity * 200)     // R
          data[idx + 1] = Math.max(0, data[idx + 1] - intensity * 50) // G
          data[idx + 2] = Math.max(0, data[idx + 2] - intensity * 80) // B
        }
      }
    }
  })

  ctx.putImageData(imageData, 0, 0)
}

// 监听视图模式切换，重新绘制热力图
watch(viewMode, async (newMode) => {
  if (newMode === 'heatmap' || newMode === 'overlay') {
    await nextTick()
    generateHeatmap()
  }
})
</script>

<style scoped>
.compare {
  padding: 20px;
}

.upload-area {
  text-align: center;
  margin-bottom: 32px;
}

.upload-icon {
  font-size: 48px;
  color: #00d4ff;
}

.detect-btn {
  margin-top: 20px;
  background: linear-gradient(135deg, #00b4aa, #2c6e9e);
  border: none;
  padding: 12px 32px;
}

.view-tabs {
  text-align: center;
  margin-bottom: 24px;
}

.compare-container {
  display: flex;
  gap: 24px;
  justify-content: center;
  align-items: stretch;
  margin: 32px 0;
  flex-wrap: wrap;
}

.compare-item {
  flex: 1;
  min-width: 280px;
  background: #f9fafc;
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
}

.compare-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e6e9f0;
}

.compare-img {
  width: 100%;
  max-height: 450px;
  border-radius: 12px;
  border: 1px solid #eef2f9;
  object-fit: contain;
}

.compare-divider {
  display: flex;
  align-items: center;
  font-size: 28px;
  color: #aaa;
}

.defect-summary {
  margin-top: 24px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}
</style>