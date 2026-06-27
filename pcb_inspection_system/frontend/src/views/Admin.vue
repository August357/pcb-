<template>
  <div class="admin">
    <div class="page-title">
      <el-icon :size="28"><Setting /></el-icon>
      <span>管理面板</span>
      <el-tag type="danger" size="small">管理员专属</el-tag>
      <!-- 导出按钮 -->
      <el-button type="success" plain @click="exportUserStats" style="margin-left: auto;">
        <el-icon><Download /></el-icon> 导出用户统计
      </el-button>
    </div>

    <div class="card">
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-icon"><el-icon><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ userStore.users.length }}</div>
            <div class="stat-label">注册用户数</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon"><el-icon><Document /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ detectionCount }}</div>
            <div class="stat-label">总检测次数</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon"><el-icon><Warning /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ totalDefects }}</div>
            <div class="stat-label">发现缺陷总数</div>
          </div>
        </el-card>
      </div>

      <h3>用户列表</h3>
      <el-table :data="userStore.users" stripe border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="name" label="昵称" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320">
          <template #default="{ row }">
            <template v-if="row.role !== 'admin'">
              <el-button type="info" size="small" plain @click="viewUserRecords(row)">
                查看记录
              </el-button>
              <el-button type="primary" size="small" plain @click="openEditDialog(row)">
                编辑
              </el-button>
              <el-button type="danger" size="small" plain @click="deleteUser(row.id)">
                删除
              </el-button>
            </template>
            <span v-else class="admin-tip">内置管理员（不可操作）</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 编辑用户弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户" width="400px">
      <el-form :model="editingUser" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editingUser.username" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editingUser.name" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editingUser.password" placeholder="留空则不修改" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editingUser.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUserEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看用户检测记录弹窗 -->
    <el-dialog
      v-model="recordsDialogVisible"
      :title="`${selectedUserForRecords?.name} 的检测记录`"
      width="900px"
    >
      <el-table :data="userRecords" stripe border max-height="400">
        <el-table-column prop="filename" label="图片名称" min-width="200" />
        <el-table-column prop="timestamp" label="检测时间" width="180" />
        <el-table-column prop="defect_count" label="缺陷数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.defect_count > 0 ? 'danger' : 'success'" size="small">
              {{ row.defect_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="缺陷详情" min-width="250">
          <template #default="{ row }">
            <div v-if="row.defects && row.defects.length > 0">
              <el-tag
                v-for="(d, idx) in row.defects"
                :key="idx"
                size="small"
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ d.class }} ({{ (d.confidence * 100).toFixed(0) }}%)
              </el-tag>
            </div>
            <span v-else class="no-defect">无缺陷</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="record-stats" v-if="userRecords.length > 0">
        <el-divider />
        <div class="stats-summary">
          <el-tag type="info">总检测次数：{{ userRecords.length }}</el-tag>
          <el-tag type="danger" style="margin-left: 10px;">总缺陷数：{{ userTotalDefects }}</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="recordsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getAllDetections, getStatsByUser } from '@/stores/history'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

const userStore = useUserStore()
const detectionCount = ref(0)
const totalDefects = ref(0)

// 编辑用户相关
const editDialogVisible = ref(false)
const editingUser = ref(null)

// 查看记录相关
const recordsDialogVisible = ref(false)
const userRecords = ref([])
const selectedUserForRecords = ref(null)

// 当前查看用户的总缺陷数
const userTotalDefects = computed(() => {
  return userRecords.value.reduce((sum, r) => sum + (r.defect_count || 0), 0)
})

// 打开编辑弹窗
function openEditDialog(user) {
  editingUser.value = { ...user }
  editDialogVisible.value = true
}

// 保存编辑
async function saveUserEdit() {
  if (editingUser.value) {
    userStore.updateUser(editingUser.value)
    editDialogVisible.value = false
    ElMessage.success('更新成功')
  }
}

// 删除用户
async function deleteUser(userId) {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？删除后无法恢复，该用户的所有检测记录也会被删除', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })

    const result = await userStore.deleteUser(userId)
    if (result.success) {
      ElMessage.success('删除成功')
      // 刷新用户列表和统计数据
      await loadStats()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消
  }
}

// 查看用户检测记录
async function viewUserRecords(user) {
  selectedUserForRecords.value = user
  const allRecords = await getAllDetections()
  userRecords.value = allRecords.filter(r => r.userId === user.id)
  recordsDialogVisible.value = true
}

// 导出用户统计 Excel
async function exportUserStats() {
  try {
    const userStats = await getStatsByUser()

    if (userStats.length === 0) {
      ElMessage.warning('暂无用户数据可导出')
      return
    }

    // 准备导出数据
    const exportData = userStats.map(stat => ({
      '用户名': stat.username,
      '用户ID': stat.userId,
      '检测次数': stat.totalDetections,
      '发现缺陷总数': stat.totalDefects,
      '平均每图缺陷数': stat.totalDetections > 0
        ? (stat.totalDefects / stat.totalDetections).toFixed(2)
        : 0
    }))

    // 添加汇总行
    const totalDetections = userStats.reduce((sum, s) => sum + s.totalDetections, 0)
    const totalDefects = userStats.reduce((sum, s) => sum + s.totalDefects, 0)

    exportData.push({
      '用户名': '【汇总】',
      '用户ID': '-',
      '检测次数': totalDetections,
      '发现缺陷总数': totalDefects,
      '平均每图缺陷数': totalDetections > 0 ? (totalDefects / totalDetections).toFixed(2) : 0
    })

    // 创建工作簿
    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '用户检测统计')

    // 设置列宽
    ws['!cols'] = [
      { wch: 20 },  // 用户名
      { wch: 12 },  // 用户ID
      { wch: 12 },  // 检测次数
      { wch: 16 },  // 发现缺陷总数
      { wch: 18 }   // 平均每图缺陷数
    ]

    // 导出文件
    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
    const blob = new Blob([excelBuffer], { type: 'application/octet-stream' })
    const fileName = `用户检测统计_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`
    saveAs(blob, fileName)

    ElMessage.success(`导出成功！共导出 ${userStats.length} 个用户的统计`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 加载统计数据
async function loadStats() {
  const records = await getAllDetections()
  detectionCount.value = records.length
  totalDefects.value = records.reduce((sum, r) => sum + (r.defect_count || 0), 0)
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.admin { padding: 20px; }

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 150px;
  display: flex;
  align-items: center;
  padding: 15px;
  border-radius: 16px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon .el-icon {
  font-size: 28px;
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #1a1a2e;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.admin-tip {
  font-size: 12px;
  color: #999;
}

.record-stats {
  margin-top: 16px;
}

.stats-summary {
  display: flex;
  justify-content: flex-end;
  padding: 8px 0;
}

.no-defect {
  color: #999;
  font-size: 12px;
}
</style>