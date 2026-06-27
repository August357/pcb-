import { defineStore } from 'pinia'
import { clearHistoryByUserId } from './history'

export const useUserStore = defineStore('user', {
  state: () => ({
    currentUser: null,
    users: []
  }),

  actions: {
    // 初始化用户数据
    initUsers() {
      const stored = localStorage.getItem('pcb_users')
      if (stored) {
        this.users = JSON.parse(stored)
      } else {
        this.users = [
          { id: 1, username: 'admin', password: '123456', role: 'admin', name: '管理员' },
          { id: 2, username: 'user1', password: '123456', role: 'user', name: '普通用户' }
        ]
        localStorage.setItem('pcb_users', JSON.stringify(this.users))
      }
      console.log('用户数据已加载:', this.users)
    },

    saveUsers() {
      localStorage.setItem('pcb_users', JSON.stringify(this.users))
    },

    // 登录
    login(username, password) {
      console.log('登录尝试:', username, password)
      console.log('当前用户列表:', this.users)

      const user = this.users.find(u => u.username === username && u.password === password)
      if (user) {
        this.currentUser = { ...user }
        localStorage.setItem('pcb_current_user', JSON.stringify(this.currentUser))
        console.log('登录成功:', this.currentUser)
        return { success: true, user: this.currentUser }
      }
      console.log('登录失败: 用户名或密码错误')
      return { success: false, message: '用户名或密码错误' }
    },

    // 注册
    register(username, password, name) {
      if (this.users.find(u => u.username === username)) {
        return { success: false, message: '用户名已存在' }
      }
      const newUser = {
        id: Date.now(),
        username,
        password,
        role: 'user',
        name: name || username
      }
      this.users.push(newUser)
      this.saveUsers()
      return { success: true, user: newUser }
    },

    // 更新用户
    updateUser(user) {
      const index = this.users.findIndex(u => u.id === user.id)
      if (index !== -1) {
        this.users[index] = { ...user }
        this.saveUsers()
        if (this.currentUser?.id === user.id) {
          this.currentUser = { ...user }
          localStorage.setItem('pcb_current_user', JSON.stringify(this.currentUser))
        }
      }
    },

    // 删除用户（同时删除该用户的检测记录）
    async deleteUser(userId) {
      const user = this.users.find(u => u.id === userId)
      if (user && user.role === 'admin') {
        return { success: false, message: '不能删除管理员账号' }
      }

      const index = this.users.findIndex(u => u.id === userId)
      if (index !== -1) {
        this.users.splice(index, 1)
        this.saveUsers()

        // 删除该用户的所有检测记录
        await clearHistoryByUserId(userId)

        return { success: true }
      }
      return { success: false, message: '用户不存在' }
    },

    // 退出登录
    logout() {
      this.currentUser = null
      localStorage.removeItem('pcb_current_user')
    },

    // 恢复登录状态
    restoreSession() {
      const stored = localStorage.getItem('pcb_current_user')
      if (stored) {
        this.currentUser = JSON.parse(stored)
        console.log('恢复登录状态:', this.currentUser)
      }
    },

    // 是否为管理员
    isAdmin() {
      return this.currentUser?.role === 'admin'
    }
  }
})