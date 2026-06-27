import { openDB } from 'idb'
import { useUserStore } from './user'

const DB_NAME = 'PCBHistoryDB'
const STORE_NAME = 'detections'

export async function initDB() {
  return openDB(DB_NAME, 2, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true })
        store.createIndex('userId', 'userId')
      }
    }
  })
}

export async function saveDetection(record) {
  const db = await initDB()
  const userStore = useUserStore()
  const user = userStore.currentUser

  const detectionRecord = {
    filename: record.filename,
    timestamp: new Date().toISOString(),
    defect_count: record.defect_count || 0,
    defects: record.defects || [],
    userId: user?.id || 1,
    username: user?.username || 'unknown'
  }

  return db.add(STORE_NAME, detectionRecord)
}

export async function getAllDetections() {
  const db = await initDB()
  const userStore = useUserStore()
  const isAdmin = userStore.isAdmin()
  const currentUserId = userStore.currentUser?.id

  const all = await db.getAll(STORE_NAME)

  if (isAdmin) {
    return all.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  } else {
    return all
      .filter(r => r.userId === currentUserId)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  }
}

export async function clearHistory() {
  const db = await initDB()
  const tx = db.transaction(STORE_NAME, 'readwrite')
  await tx.objectStore(STORE_NAME).clear()
  await tx.done
}

// 删除指定用户的所有检测记录
export async function clearHistoryByUserId(userId) {
  const db = await initDB()
  const allRecords = await db.getAll(STORE_NAME)
  const tx = db.transaction(STORE_NAME, 'readwrite')
  const store = tx.objectStore(STORE_NAME)

  for (const record of allRecords) {
    if (record.userId === userId) {
      await store.delete(record.id)
    }
  }

  await tx.done
}

export async function getStatsByUser() {
  const db = await initDB()
  const all = await db.getAll(STORE_NAME)
  const map = new Map()

  for (const r of all) {
    const name = r.username || `用户${r.userId}`
    if (!map.has(name)) {
      map.set(name, { username: name, userId: r.userId, totalDetections: 0, totalDefects: 0 })
    }
    const stat = map.get(name)
    stat.totalDetections++
    stat.totalDefects += r.defect_count || 0
  }

  return Array.from(map.values())
}