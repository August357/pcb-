<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <el-menu
      :default-active="activeIndex"
      class="nav-menu"
      mode="horizontal"
      router
      background-color="#1a1a2e"
      text-color="#eee"
      active-text-color="#00d4ff"
    >
      <div class="logo">
        <el-icon><Cpu /></el-icon>
        <span>PCB 缺陷检测系统</span>
      </div>
      <div class="nav-links">
        <el-menu-item index="/">
          <el-icon><Picture /></el-icon>
          <span>单张检测</span>
        </el-menu-item>
        <el-menu-item index="/batch">
          <el-icon><Files /></el-icon>
          <span>批量检测</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><DataLine /></el-icon>
          <span>历史统计</span>
        </el-menu-item>
        <el-menu-item index="/camera">
          <el-icon><Camera /></el-icon>
          <span>实时检测</span>
        </el-menu-item>
        <el-menu-item index="/compare">
          <el-icon><CopyDocument /></el-icon>
          <span>对比检测</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isAdmin()" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>管理面板</span>
        </el-menu-item>
      </div>
      <div class="user-info">
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            {{ userStore.currentUser?.name || '用户' }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-menu>

    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeIndex = computed(() => route.path)

function handleCommand(command) {
  if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

/* 导航栏样式 */
.nav-menu {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: bold;
  color: #00d4ff;
}

.logo .el-icon {
  font-size: 24px;
}

.nav-links {
  display: flex;
  gap: 10px;
}

.nav-menu .el-menu-item {
  font-size: 1rem;
  border-bottom: none;
}

.nav-menu .el-menu-item:hover {
  background-color: rgba(0, 212, 255, 0.1) !important;
}

.user-info {
  margin-left: 20px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #eee;
}

.user-dropdown:hover {
  color: #00d4ff;
}

/* 主内容区 */
.main-content {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 卡片通用样式 */
.card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  padding: 30px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title .el-icon {
  font-size: 28px;
  color: #00d4ff;
}
</style>