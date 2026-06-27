<template>
  <div class="camera">
    <div class="page-title">
      <el-icon :size="28"><Camera /></el-icon>
      <span>实时摄像头检测</span>
      <el-tag type="success" size="small">右侧结果由滑块控制</el-tag>
    </div>

    <div class="card">
      <!-- 置信度滑块：控制右侧显示哪些缺陷 -->
      <div class="threshold-bar">
        <span>右侧显示阈值：</span>
        <el-slider
          v-model="displayThreshold"
          :min="0.2"
          :max="0.9"
          :step="0.01"
          style="width: 260px"
        />
        <el-tag :type="thresholdTagType" size="small">
          只显示置信度 ≥ {{ (displayThreshold * 100).toFixed(0) }}% 的缺陷
        </el-tag>
      </div>

      <!-- 实时 / 检测结果切换 -->
      <div class="mode-bar">
        <el-radio-group v-model="mode" size="default">
          <el-radio-button value="live">
            <el-icon><VideoCamera /></el-icon> 实时画面
          </el-radio-button>
          <el-radio-button value="result">
            <el-icon><Picture /></el-icon> 检测结果
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 实时画面区 -->
      <div v-show="mode === 'live'" class="video-container">
        <div class="video-wrapper">
          <img v-if="liveImage" :src="liveImage" class="video-feed" />
          <div v-else class="placeholder">
            <el-icon :size="48"><VideoCamera /></el-icon>
            <p>等待摄像头连接...</p>
          </div>
        </div>

        <div class="action-panel">
          <el-button
            type="primary"
            size="large"
            :disabled="!isRunning"
            @click="captureAndDetect"
          >
            <el-icon><Camera /></el-icon> 拍照检测
          </el-button>
          <p class="hint">对准 PCB 板后点击「拍照检测」</p>
        </div>
      </div>

      <!-- 检测结果区（右侧完全由滑块控制） -->
      <div v-show="mode === 'result' && resultImage" class="result-container">
        <div class="result-wrapper">
          <el-image :src="resultImage" fit="contain" class="result-image" />
        </div>
        <div class="result-info">
          <el-tag type="danger" size="large">
            共发现 {{ filteredDefects.length }} 处缺陷
          </el-tag>
          <div class="defect-list">
            <div
              v-for="(d, idx) in filteredDefects"
              :key="idx"
              class="defect-tag"
            >
              <el-tag :type="getDefectType(d.class)" size="large">
                {{ d.class.replace('_', ' ') }}
                ({{ (d.confidence * 100).toFixed(1) }}%)
              </el-tag>
            </div>
            <div v-if="filteredDefects.length === 0" class="silent-tip">
              当前阈值下未显示缺陷（图上框仍在，右侧已过滤）
            </div>
          </div>
          <el-button type="info" @click="backToLive" class="back-btn">
            <el-icon><Refresh /></el-icon> 重新拍照
          </el-button>
        </div>
      </div>

      <div class="controls">
        <el-button type="primary" @click="startCamera" :disabled="isRunning">
          <el-icon><VideoPlay /></el-icon> 开启摄像头
        </el-button>
        <el-button type="danger" @click="stopCamera" :disabled="!isRunning">
          <el-icon><VideoPause /></el-icon> 停止检测
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { saveDetection } from '@/stores/history'
import { useUserStore } from '@/stores/user'

let ws = null
const isRunning = ref(false)
const liveImage = ref(null)
const mode = ref('live')
const resultImage = ref(null)
const allRawDefects = ref([])

// 右侧显示阈值（用户可拖拽）
const displayThreshold = ref(0.5)

const userStore = useUserStore()

const thresholdTagType = computed(() => {
  const t = displayThreshold.value
  if (t >= 0.7) return 'danger'
  if (t >= 0.5) return 'warning'
  return 'info'
})

// 根据滑块过滤缺陷
const filteredDefects = computed(() => {
  return allRawDefects.value.filter(d => d.confidence >= displayThreshold.value)
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

function startCamera() {
  if (ws) return

  ws = new WebSocket('ws://localhost:8000/ws')

  ws.onopen = () => {
    isRunning.value = true
    mode.value = 'live'
    ElMessage.success('摄像头已开启')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    liveImage.value = data.image
  }

  ws.onerror = () => {
    ElMessage.error('连接失败，请确保后端已启动')
    stopCamera()
  }

  ws.onclose = () => {
    isRunning.value = false
  }
}

function stopCamera() {
  if (ws) {
    ws.close()
    ws = null
  }
  isRunning.value = false
  liveImage.value = null
  mode.value = 'live'
  resultImage.value = null
  allRawDefects.value = []
  ElMessage.info('摄像头已关闭')
}

async function captureAndDetect() {
  if (!liveImage.value) {
    ElMessage.warning('无画面，请先开启摄像头')
    return
  }

  const img = new Image()
  img.crossOrigin = 'Anonymous'
  img.src = liveImage.value

  img.onload = async () => {
    const canvas = document.createElement('canvas')
    canvas.width = img.width
    canvas.height = img.height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0)

    canvas.toBlob(async (blob) => {
      const formData = new FormData()
      formData.append('file', blob, 'capture.jpg')

      try {
        const res = await axios.post('http://localhost:8000/detect', formData)

        // 后端返回所有缺陷框（全量）
        allRawDefects.value = res.data.defects || []
        resultImage.value = res.data.result_image
        mode.value = 'result'

        // 保存历史：保留全部缺陷（不过滤）
        await saveDetection({
          filename: `摄像头拍照_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.jpg`,
          defect_count: res.data.defects?.length || 0,
          defects: res.data.defects || [],
          userId: userStore.currentUser?.id,
          username: userStore.currentUser?.username
        })

        ElMessage.success(`检测完成，右侧显示由阈值控制`)
      } catch (err) {
        console.error(err)
        ElMessage.error('检测失败')
      }
    }, 'image/jpeg')
  }
}

function backToLive() {
  mode.value = 'live'
  resultImage.value = null
  allRawDefects.value = []
}

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.camera {
  padding: 20px;
}

.threshold-bar {
  background: #f5f7fa;
  border-radius: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.mode-bar {
  margin-bottom: 20px;
  text-align: center;
}

.video-container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.video-wrapper {
  flex: 2;
  background: #1a1a2e;
  border-radius: 16px;
  overflow: hidden;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-feed {
  width: 100%;
  height: auto;
}

.placeholder {
  text-align: center;
  color: #ccc;
  padding: 60px;
}

.action-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.hint {
  color: #888;
  font-size: 14px;
}

.result-container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.result-wrapper {
  flex: 2;
  background: #f5f7fa;
  border-radius: 16px;
  overflow: hidden;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-image {
  width: 100%;
  height: auto;
}

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.defect-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.silent-tip {
  color: #888;
  font-size: 13px;
  font-style: italic;
}

.back-btn {
  margin-top: 10px;
}

.controls {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 24px;
}
</style>