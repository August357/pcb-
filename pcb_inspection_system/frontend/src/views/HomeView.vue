<template>
  <div class="home">
    <div class="page-title">
      <el-icon :size="28"><Picture /></el-icon>
      <span>单张图片检测</span>
    </div>

    <div class="card">
      <!-- 上传区域 -->
      <div class="upload-section">
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileUpload"
          accept="image/*"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">点击或拖拽上传 PCB 图片</div>
          <div class="upload-hint">支持 JPG、PNG、BMP 格式</div>
        </el-upload>

        <div v-if="currentFileName" class="file-info">
          <el-tag type="success" effect="plain">
            <el-icon><Document /></el-icon>
            {{ currentFileName }}
          </el-tag>
        </div>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!file"
          @click="detect"
          class="detect-btn"
        >
          <el-icon><Search /></el-icon>
          {{ loading ? '检测中...' : '开始检测' }}
        </el-button>
      </div>

      <!-- 检测结果 -->
      <div v-if="result" class="result-section">
        <el-divider />

        <div class="result-header">
          <h3>检测结果</h3>
          <el-tag type="danger" size="large">
            共发现 {{ result.defect_count }} 处缺陷
          </el-tag>
        </div>

        <!-- 缺陷列表 -->
        <div class="defect-list">
          <el-table :data="result.defects" stripe border style="width: 100%">
            <el-table-column prop="class" label="缺陷类型" width="180">
              <template #default="{ row }">
                <el-tag :type="getDefectType(row.class)" effect="dark">
                  {{ row.class }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="150">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.confidence * 100"
                  :color="getProgressColor(row.confidence)"
                  :format="() => `${(row.confidence * 100).toFixed(1)}%`"
                />
              </template>
            </el-table-column>
            <el-table-column label="位置信息">
              <template #default="{ row }">
                <span class="bbox-info">[{{ row.bbox.join(', ') }}]</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 检测结果图 -->
        <div class="result-image">
          <h4>缺陷标注图</h4>
          <el-image
            :src="result.result_image"
            fit="contain"
            :preview-src-list="[result.result_image]"
            class="detected-image"
          >
            <template #error>
              <div class="image-error">加载失败</div>
            </template>
          </el-image>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { saveDetection } from '@/stores/history'

const file = ref(null)
const currentFileName = ref('')
const loading = ref(false)
const result = ref(null)

function handleFileUpload(uploadFile) {
  file.value = uploadFile.raw
  currentFileName.value = uploadFile.name
  result.value = null
  ElMessage.success('图片已加载')
}

async function detect() {
  if (!file.value) return

  loading.value = true
  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const res = await axios.post('http://localhost:8000/detect', formData)
    result.value = res.data

    await saveDetection({
      filename: file.value.name,
      defect_count: res.data.defect_count,
      defects: res.data.defects,
    })

    ElMessage.success('检测完成！')
  } catch (err) {
    console.error(err)
    ElMessage.error('检测失败，请确保后端服务已启动')
  } finally {
    loading.value = false
  }
}

function getDefectType(type) {
  const typeMap = {
    'missing_hole': 'danger',
    'mouse_bite': 'warning',
    'open_circuit': 'info',
    'short': 'danger',
    'spur': 'warning',
    'spurious_copper': 'success'
  }
  return typeMap[type] || 'info'
}

function getProgressColor(confidence) {
  if (confidence > 0.8) return '#67c23a'
  if (confidence > 0.6) return '#e6a23c'
  return '#f56c6c'
}
</script>

<style scoped>
.home {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.upload-section {
  text-align: center;
  padding: 20px 0;
}

.upload-area {
  margin-bottom: 20px;
}

.upload-icon {
  font-size: 48px;
  color: #00d4ff;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  color: #666;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.file-info {
  margin: 20px 0;
}

.detect-btn {
  margin-top: 20px;
  padding: 12px 32px;
  font-size: 16px;
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border: none;
}

.result-section {
  margin-top: 30px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-header h3 {
  font-size: 18px;
  color: #333;
}

.defect-list {
  margin: 20px 0;
}

.result-image {
  margin-top: 30px;
}

.result-image h4 {
  font-size: 16px;
  color: #555;
  margin-bottom: 15px;
}

.detected-image {
  width: 100%;
  max-height: 500px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.bbox-info {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}
</style>