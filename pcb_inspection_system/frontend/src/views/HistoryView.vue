<template>
  <div class="history">
    <div class="page-title">
      <el-icon :size="28"><DataLine /></el-icon>
      <span>{{ isAdmin ? '所有用户检测记录' : '我的检测历史' }}</span>
      <div class="btn-group">
        <el-button type="success" plain @click="exportToExcel">
          <el-icon><Download /></el-icon> 导出 Excel
        </el-button>
        <el-button type="danger" plain @click="handleClearHistory">
          <el-icon><Delete /></el-icon> 清空历史记录
        </el-button>
      </div>
    </div>

    <div class="card">
      <!-- 管理员专属：用户筛选下拉框 -->
      <div v-if="isAdmin" class="filter-bar">
        <el-select v-model="selectedUserId" placeholder="筛选用户" clearable @change="filterByUser">
          <el-option label="全部用户" :value="null" />
          <el-option
            v-for="user in userList"
            :key="user.userId"
            :label="user.username"
            :value="user.userId"
          />
        </el-select>
        <el-tag type="info" size="small">当前显示：{{ filterInfo }}</el-tag>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-icon total"><el-icon><Document /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ filteredHistory.length }}</div>
            <div class="stat-label">检测次数</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon defects"><el-icon><Warning /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ totalDefects }}</div>
            <div class="stat-label">发现缺陷总数</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon avg"><el-icon><TrendCharts /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ avgDefects }}</div>
            <div class="stat-label">平均每图缺陷数</div>
          </div>
        </el-card>
      </div>

      <!-- 饼图区域 -->
      <div class="chart-section">
        <h3>📊 缺陷类型分布</h3>
        <div ref="chartRef" class="chart pie-chart"></div>
      </div>

      <!-- 趋势图区域 -->
      <div class="chart-section">
        <h3>📈 检测趋势（近7天）</h3>
        <div ref="trendChartRef" class="chart trend-chart"></div>
      </div>

      <!-- 历史记录表格 -->
      <div class="history-table">
        <h3>📋 详细记录</h3>
        <el-table :data="filteredHistory" stripe border>
          <el-table-column v-if="isAdmin" prop="username" label="用户名" width="120" />
          <el-table-column prop="filename" label="图片名称" min-width="200" />
          <el-table-column prop="timestamp" label="检测时间" width="180" />
          <el-table-column prop="defect_count" label="缺陷数量" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="row.defect_count > 0 ? 'danger' : 'success'">
                {{ row.defect_count }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="缺陷详情">
            <template #default="{ row }">
              <el-tag
                v-for="(d, idx) in row.defects"
                :key="idx"
                size="small"
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ d.class }} ({{ (d.confidence * 100).toFixed(0) }}%)
              </el-tag>
              <span v-if="!row.defects?.length">无</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAllDetections, clearHistory, getStatsByUser } from '@/stores/history'
import { useUserStore } from '@/stores/user'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.isAdmin())

const history = ref([])
const filteredHistory = ref([])
const chartRef = ref(null)
const trendChartRef = ref(null)
let chartInstance = null
let trendChartInstance = null
const userList = ref([])
const selectedUserId = ref(null)

// 计算统计数据
const totalDefects = computed(() => {
  return filteredHistory.value.reduce((sum, r) => sum + (r.defect_count || 0), 0)
})

const avgDefects = computed(() => {
  if (filteredHistory.value.length === 0) return '0'
  return (totalDefects.value / filteredHistory.value.length).toFixed(1)
})

const filterInfo = computed(() => {
  if (selectedUserId.value) {
    const user = userList.value.find(u => u.userId === selectedUserId.value)
    return user ? `${user.username} 的记录` : '用户记录'
  }
  return '全部用户'
})

// 加载历史记录
async function loadHistory() {
  history.value = await getAllDetections()
  filterByUser()
  await renderChart()
  await renderTrendChart()
}

// 按用户筛选
function filterByUser() {
  if (selectedUserId.value) {
    filteredHistory.value = history.value.filter(r => r.userId === selectedUserId.value)
  } else {
    filteredHistory.value = [...history.value]
  }
}

// 加载用户列表（管理员用）
async function loadUserList() {
  if (isAdmin.value) {
    const stats = await getStatsByUser()
    userList.value = stats.map(s => ({
      userId: s.userId,
      username: s.username
    }))
  }
}

// 清空历史
async function handleClearHistory() {
  try {
    await ElMessageBox.confirm(
      isAdmin.value ? '清空后将删除所有用户的检测记录，无法恢复！' : '清空后将删除你的所有检测记录，无法恢复！',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await clearHistory()
    await loadHistory()
    await loadUserList()
    ElMessage.success('历史记录已清空')
  } catch {
    // 用户取消
  }
}

// 导出 Excel
function exportToExcel() {
  if (filteredHistory.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  const exportData = filteredHistory.value.map(record => ({
    用户名: record.username || '-',
    图片名称: record.filename,
    检测时间: record.timestamp,
    缺陷数量: record.defect_count,
    缺陷详情: record.defects.map(d => `${d.class}(${(d.confidence * 100).toFixed(1)}%)`).join('; ')
  }))

  const ws = XLSX.utils.json_to_sheet(exportData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'PCB检测历史')

  ws['!cols'] = [
    { wch: 15 }, { wch: 30 }, { wch: 20 },
    { wch: 12 }, { wch: 50 }
  ]

  const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const blob = new Blob([excelBuffer], { type: 'application/octet-stream' })
  const fileName = `PCB检测历史_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`
  saveAs(blob, fileName)

  ElMessage.success(`导出成功！共导出 ${exportData.length} 条记录`)
}

// 渲染饼图（优化标签避免重叠）
async function renderChart() {
  await nextTick()
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  const defectCounts = {}
  for (const record of filteredHistory.value) {
    for (const defect of record.defects || []) {
      const name = defect.class || '未知'
      defectCounts[name] = (defectCounts[name] || 0) + 1
    }
  }

  const chartData = Object.entries(defectCounts).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value
  }))

  chartInstance = echarts.init(chartRef.value)

  if (chartData.length === 0) {
    chartInstance.setOption({
      title: {
        text: '暂无缺陷数据',
        left: 'center',
        top: 'center',
        textStyle: { fontSize: 14, color: '#999' }
      }
    })
    return
  }

  chartInstance.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}次 ({d}%)' },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'center',
      textStyle: { fontSize: 11 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['55%', '55%'],
      data: chartData,
      avoidLabelOverlap: true,
      label: {
        show: true,
        formatter: '{b}: {d}%',
        position: 'outside',
        bleedMargin: 10,
        fontSize: 11
      },
      labelLine: {
        length: 12,
        length2: 8,
        smooth: true
      },
      emphasis: { scale: true }
    }]
  })
}

// 渲染趋势图
async function renderTrendChart() {
  await nextTick()
  if (!trendChartRef.value) return

  if (trendChartInstance) {
    trendChartInstance.dispose()
    trendChartInstance = null
  }

  // 按日期统计检测次数和缺陷总数
  const dateMap = new Map()

  for (const record of filteredHistory.value) {
    const date = record.timestamp?.split('T')[0]
    if (!date) continue

    if (!dateMap.has(date)) {
      dateMap.set(date, { date, detections: 0, defects: 0 })
    }
    const stat = dateMap.get(date)
    stat.detections++
    stat.defects += record.defect_count || 0
  }

  let trendData = Array.from(dateMap.values())
  trendData.sort((a, b) => a.date.localeCompare(b.date))

  if (trendData.length > 7) {
    trendData = trendData.slice(-7)
  }

  const dates = trendData.map(d => d.date.slice(5))
  const detections = trendData.map(d => d.detections)
  const defects = trendData.map(d => d.defects)

  trendChartInstance = echarts.init(trendChartRef.value)

  if (dates.length === 0) {
    trendChartInstance.setOption({
      title: {
        text: '暂无检测数据',
        left: 'center',
        top: 'center',
        textStyle: { fontSize: 14, color: '#999' }
      }
    })
    return
  }

  trendChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测次数', '缺陷总数'], top: 0 },
    grid: { left: '8%', right: '8%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: dates, name: '日期' },
    yAxis: { type: 'value', name: '数量' },
    series: [
      {
        name: '检测次数',
        type: 'line',
        data: detections,
        smooth: true,
        lineStyle: { color: '#5470c6', width: 2 },
        areaStyle: { opacity: 0.1 },
        symbol: 'circle',
        symbolSize: 6
      },
      {
        name: '缺陷总数',
        type: 'line',
        data: defects,
        smooth: true,
        lineStyle: { color: '#fac858', width: 2 },
        areaStyle: { opacity: 0.1 },
        symbol: 'diamond',
        symbolSize: 6
      }
    ]
  })
}

// 监听筛选变化
watch(selectedUserId, () => {
  filterByUser()
  renderChart()
  renderTrendChart()
})

// 窗口大小变化
window.addEventListener('resize', () => {
  if (chartInstance) chartInstance.resize()
  if (trendChartInstance) trendChartInstance.resize()
})

onMounted(() => {
  loadUserList()
  loadHistory()
})
</script>

<style scoped>
.history { padding: 20px; }

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.btn-group {
  margin-left: auto;
  display: flex;
  gap: 12px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 12px;
}

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
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.stat-icon.total { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.stat-icon.defects { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-icon.avg { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }

.stat-icon .el-icon { font-size: 28px; color: white; }

.stat-value { font-size: 28px; font-weight: bold; color: #1a1a2e; }
.stat-label { font-size: 14px; color: #888; }

/* 图表区域 - 上下布局 */
.chart-section {
  margin: 20px 0;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
  text-align: center;
}

.pie-chart {
  width: 100%;
  height: 420px;
}

.trend-chart {
  width: 100%;
  height: 360px;
}

.history-table { margin-top: 20px; }
.history-table h3 { margin-bottom: 16px; font-size: 18px; color: #333; }
</style>