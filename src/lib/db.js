const DB_NAME = 'star-map'
const STORE_NAME = 'repo-state'
const CACHE_STORE_NAME = 'repo-cache'
const DB_VERSION = 2

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result

      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, {
          keyPath: 'repoId'
        })
      }

      if (!db.objectStoreNames.contains(CACHE_STORE_NAME)) {
        db.createObjectStore(CACHE_STORE_NAME, {
          keyPath: 'username'
        })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export async function loadStates() {
  if (!('indexedDB' in window)) return {}

  const db = await openDb()

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, 'readonly')
    const request = transaction.objectStore(STORE_NAME).getAll()

    request.onsuccess = () => {
      const result = {}

      for (const state of request.result) {
        result[state.repoId] = state
      }

      resolve(result)
    }

    request.onerror = () => reject(request.error)
  })
}

export async function saveState(state) {
  if (!('indexedDB' in window)) return

  const db = await openDb()

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, 'readwrite')

    transaction.objectStore(STORE_NAME).put(state)

    transaction.oncomplete = () => resolve()
    transaction.onerror = () => reject(transaction.error)
    transaction.onabort = () => reject(transaction.error)
  })
}

export async function loadRepositoryCache(username) {
  if (!('indexedDB' in window)) return null

  const db = await openDb()

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(CACHE_STORE_NAME, 'readonly')
    const request = transaction.objectStore(CACHE_STORE_NAME).get(username)

    request.onsuccess = () => resolve(request.result ?? null)
    request.onerror = () => reject(request.error)
  })
}

export async function saveRepositoryCache(username, repositories, user) {
  if (!('indexedDB' in window)) return

  const db = await openDb()

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(CACHE_STORE_NAME, 'readwrite')

    transaction.objectStore(CACHE_STORE_NAME).put({
      username,
      repositories,
      user,
      fetchedAt: Date.now()
    })

    transaction.oncomplete = () => resolve()
    transaction.onerror = () => reject(transaction.error)
    transaction.onabort = () => reject(transaction.error)
  })
}
