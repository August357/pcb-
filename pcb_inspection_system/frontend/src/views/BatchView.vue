<template>
  <div class="batch">
    <div class="page-title">
      <el-icon :size="28"><Files /></el-icon>
      <span>批量图片检测</span>
    </div>

    <div class="card">
      <div class="upload-section">
        <el-upload
          class="batch-upload"
          drag
          multiple
          :auto-upload="false"
          :show-file-list="true"
          :on-change="handleFiles"
          :file-list="fileList"
          accept="image/*"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">点击或拖拽上传多张 PCB 图片</div>
          <div class="upload-hint">支持批量选择，一次处理多张图片</div>
        </el-upload>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="files.length === 0"
          @click="batchDetect"
          class="detect-btn"
        >
          <el-icon><Search /></el-icon>
          {{ loading ? `批量检测中 (${processedCount}/${files.length})` : '开始批量检测' }}
        </el-button>
      </div>

      <div v-if="results.length" class="results-section">
        <el-divider />
        <h3>检测结果（共 {{ results.length }} 张图片）</h3>

        <div class="results-list">
          <el-collapse v-model="activeCollapse">
            <el-collapse-item v-for="(item, idx) in results" :key="idx" :name="idx">
              <template #title>
                <div class="collapse-title">
                  <el-icon><Picture /></el-icon>
                  <span>{{ item.filename }}</span>
                  <el-tag :type="item.defect_count > 0 ? 'danger' : 'success'" size="small">
                    缺陷数：{{ item.defect_count }}
                  </el-tag>
                </div>
              </template>

              <div class="result-detail">
                <div v-if="item.defects.length > 0" class="defect-list">
                  <el-table :data="item.defects" size="small" border>
                    <el-table-column prop="class" label="缺陷类型">
                      <template #default="{ row }">
                        <el-tag :type="getDefectType(row.class)" size="small">
                          {{ row.class }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="confidence" label="置信度" width="200">
                      <template #default="{ row }">
                        <el-progress
                          :percentage="row.confidence * 100"
                          :stroke-width="8"
                          :show-text="false"
                        />
                        <span class="conf-value">{{ (row.confidence * 100).toFixed(1) }}%</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <div v-else class="no-defect">
                  <el-icon><SuccessFilled /></el-icon>
                  未发现缺陷
                </div>
                <el-image
                  :src="item.result_image"
                  fit="contain"
                  :preview-src-list="[item.result_image]"
                  class="result-thumb"
                />
              </div>
            </el-collapse-item>
          </el-collapse>
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

const files = ref([])
const fileList = ref([])
const loading = ref(false)
const results = ref([])
const activeCollapse = ref([])
const processedCount = ref(0)

function handleFiles(uploadFile, uploadFiles) {
  files.value = uploadFiles.filter(f => f.raw).map(f => f.raw)
  fileList.value = uploadFiles
  results.value = []
}

async function batchDetect() {
  if (files.value.length === 0) return

  loading.value = true
  processedCount.value = 0
  const formData = new FormData()
  files.value.forEach(f => formData.append('files', f))

  try {
    const res = await axios.post('http://localhost:8000/detect_batch', formData)
    results.value = res.data.results
    processedCount.value = results.value.length

    for (const r of res.data.results) {
      await saveDetection({
        filename: r.filename,
        defect_count: r.defect_count,
        defects: r.defects,
      })
    }

    ElMessage.success(`批量检测完成！共处理 ${results.value.length} 张图片`)
    activeCollapse.value = results.value.map((_, i) => i)
  } catch (err) {
    console.error(err)
    ElMessage.error('批量检测失败，请确保后端服务已启动')
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
</script>

<style scoped>
.batch {
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

.batch-upload {
  margin-bottom: 20px;
}

.detect-btn {
  margin-top: 20px;
  padding: 12px 32px;
  font-size: 16px;
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border: none;
}

.results-section {
  margin-top: 30px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.result-detail {
  padding: 15px;
  background: #fafafa;
  border-radius: 8px;
}

.defect-list {
  margin-bottom: 15px;
}

.conf-value {
  margin-left: 10px;
  font-size: 12px;
  color: #666;
}

.no-defect {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #67c23a;
  padding: 10px 0;
}

.result-thumb {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>