import { categorizeRepository } from './categories.js'

const API_ROOT = 'https://api.github.com'

const HEADERS = {
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28'
}

async function request(url, { signal } = {}) {
  const response = await fetch(url, {
    headers: HEADERS,
    signal
  })

  if (!response.ok) {
    let detail = ''

    try {
      const body = await response.json()
      if (body.message) detail = `: ${body.message}`
    } catch {
      // The response may not contain JSON.
    }

    throw new Error(
      `GitHub API ${response.status} ${response.statusText}${detail}`
    )
  }

  return response
}

function getNextPage(response) {
  const link = response.headers.get('Link')
  if (!link) return null

  const match = link.match(/<([^>]+)>;\s*rel="next"/)
  return match ? match[1] : null
}

function cleanUsername(username) {
  const clean = String(username ?? '').trim().replace(/^@/, '')

  if (!clean) {
    throw new Error('Enter a GitHub username.')
  }

  return clean
}

export async function fetchGitHubUser(username, { signal } = {}) {
  const clean = cleanUsername(username)
  const response = await request(
    `${API_ROOT}/users/${encodeURIComponent(clean)}`,
    { signal }
  )

  return response.json()
}

function normalizeRepository(repo) {
  const normalized = {
    ...repo,
    topics: Array.isArray(repo.topics) ? repo.topics : [],
    owner: {
      login: repo.owner?.login || '',
      avatar_url: repo.owner?.avatar_url || ''
    }
  }

  normalized.category = categorizeRepository(normalized).id
  return normalized
}

export async function fetchStarredRepositories(
  username,
  { onProgress, signal } = {}
) {
  const clean = cleanUsername(username)

  let url =
    `${API_ROOT}/users/${encodeURIComponent(clean)}/starred` +
    '?per_page=100&sort=created&direction=desc'

  const repositories = []
  let page = 0

  while (url) {
    const response = await request(url, { signal })
    const pageRepositories = await response.json()

    repositories.push(...pageRepositories.map(normalizeRepository))
    page += 1

    url = getNextPage(response)

    onProgress?.({
      page,
      count: repositories.length,
      done: !url
    })
  }

  return repositories
}
