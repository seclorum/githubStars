
from pathlib import Path

path = Path("src/App.svelte")
source = path.read_text()
original = source

replacements = [
    (
        "  import { loadStates, saveState } from './lib/db.js'",
        """  import {
    loadStates,
    saveState,
    loadRepositoryCache,
    saveRepositoryCache
  } from './lib/db.js'
  import {
    fetchGitHubUser,
    fetchStarredRepositories
  } from './lib/github.js'"""
    ),
    (
        "  const repositories = createMockRepositories(3247)",
        """  const CACHE_MAX_AGE = 15 * 60 * 1000
  const DEMO_REPOSITORIES = createMockRepositories(3247)

  let repositories = DEMO_REPOSITORIES
  let username = 'seclorum'
  let githubUser = null
  let sourceLabel = 'Demo data'
  let loadStatus = 'Showing generated demo repositories'
  let loadError = ''
  let loadingRepos = false
  let loadProgress = { page: 0, count: 0, done: false }"""
    ),
    (
        "  let showSettings = false",
        """  let showSettings = false

  async function loadGitHubStars({ force = false } = {}) {
    const clean = String(username || '').trim().replace(/^@/, '')

    if (!clean) {
      loadError = 'Enter a GitHub username.'
      return
    }

    username = clean
    loadError = ''
    loadingRepos = true
    loadProgress = { page: 0, count: 0, done: false }
    loadStatus = `Checking cached stars for ${clean}…`

    let cache = null

    try {
      cache = await loadRepositoryCache(clean.toLowerCase())
    } catch (error) {
      console.warn('Could not read repository cache:', error)
    }

    const hasCache = Array.isArray(cache?.repositories)
    const cacheIsFresh = hasCache &&
      Date.now() - cache.fetchedAt < CACHE_MAX_AGE

    if (hasCache) {
      repositories = cache.repositories
      githubUser = cache.user || null
      sourceLabel = cacheIsFresh ? 'Cached GitHub stars' : 'Stale cache'
      selected = null
      loadStatus = `Showing ${repositories.length.toLocaleString()} cached repositories`
    }

    if (cacheIsFresh && !force) {
      loadingRepos = false
      return
    }

    loadStatus = `Loading public stars for ${clean}…`

    try {
      const user = await fetchGitHubUser(clean)
      const fetched = await fetchStarredRepositories(clean, {
        onProgress(progress) {
          loadProgress = progress
          loadStatus =
            `Fetched ${progress.count.toLocaleString()} repositories ` +
            `(page ${progress.page})…`
        }
      })

      repositories = fetched
      githubUser = user
      selected = null
      sourceLabel = 'GitHub'
      loadStatus =
        `Loaded ${fetched.length.toLocaleString()} public starred repositories`

      try {
        await saveRepositoryCache(clean.toLowerCase(), fetched, user)
      } catch (error) {
        console.warn('Could not save repository cache:', error)
      }
    } catch (error) {
      loadError = error instanceof Error ? error.message : String(error)

      if (hasCache) {
        sourceLabel = 'Stale cache'
        loadStatus = 'GitHub refresh failed; showing cached repositories'
      } else {
        repositories = DEMO_REPOSITORIES
        githubUser = null
        sourceLabel = 'Demo data'
        loadStatus = 'GitHub could not be loaded; showing demo data'
      }
    } finally {
      loadingRepos = false
    }
  }"""
    ),
    (
        """  onMount(async () => {
    try {
      states = await loadStates()
    } catch (error) {
      console.warn('Could not load IndexedDB state:', error)
    }

    loaded = true
  })""",
        """  onMount(async () => {
    try {
      states = await loadStates()
    } catch (error) {
      console.warn('Could not load IndexedDB state:', error)
    }

    loaded = true

    if (new URLSearchParams(window.location.search).get('demo') === '1') {
      loadStatus = 'Showing generated demo repositories (?demo=1)'
      return
    }

    await loadGitHubStars()
  })"""
    ),
    (
        "<span>seclorum</span>",
        "<span>{username}</span>"
    ),
    (
        """          <p>
            Repositories grouped by category and similarity
            {#if search}
              · {filteredCount.toLocaleString()} matches
            {/if}
          </p>""",
        """          <p>
            Repositories grouped by category and similarity
            · {sourceLabel}
            {#if search}
              · {filteredCount.toLocaleString()} matches
            {/if}
          </p>
          {#if loadingRepos}
            <p role="status">
              {loadStatus}
              {#if loadProgress.count}
                ({loadProgress.count.toLocaleString()} loaded)
              {/if}
            </p>
          {/if}
          {#if loadError}
            <p role="alert">{loadError}</p>
          {/if}"""
    ),
    (
        """      <strong>Star Map v0.1</strong>
      <p>
        This version uses generated repository data.
        GitHub connection arrives in v0.2.
      </p>

      <button on:click={() => (showSettings = false)}>
        Close
      </button>""",
        """      <strong>Star Map v0.2</strong>
      <p>Load public starred repositories from GitHub.</p>

      <label for="github-username">GitHub username</label>
      <input
        id="github-username"
        bind:value={username}
        placeholder="GitHub username"
        autocomplete="off"
        disabled={loadingRepos}
      />

      <p role="status">{loadStatus}</p>
      {#if loadError}
        <p role="alert">{loadError}</p>
      {/if}

      <div class="settings-actions">
        <button
          on:click={() => loadGitHubStars({ force: true })}
          disabled={loadingRepos}
        >
          {loadingRepos ? 'Loading…' : 'Load / refresh stars'}
        </button>
        <button
          on:click={() => window.open(
            `https://github.com/${encodeURIComponent(username)}`,
            '_blank',
            'noopener,noreferrer'
          )}
        >
          Open profile
        </button>
        <button on:click={() => (showSettings = false)}>Close</button>
      </div>"""
    )
]

# Validate all source fragments before writing anything.
for index, (old, new) in enumerate(replacements, 1):
    count = source.count(old)
    if count != 1:
        raise SystemExit(
            f"Replacement {index}: expected one match, found {count}. "
            "No source file was written."
        )
    source = source.replace(old, new, 1)

if source == original:
    raise SystemExit("No changes produced; source file left untouched.")

path.write_text(source)
print(f"Updated {path} with {len(replacements)} verified replacements.")
