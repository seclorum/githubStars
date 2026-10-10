<script>
  import { onMount } from 'svelte'
  import RepoMap from './lib/RepoMap.svelte'
  import { CATEGORIES } from './lib/categories.js'
  import { createMockRepositories } from './data/mockRepos.js'
  import { compactNumber, relativeDate } from './lib/format.js'
  import {
    loadStates,
    saveState,
    loadRepositoryCache,
    saveRepositoryCache
  } from './lib/db.js'
  import {
    fetchGitHubUser,
    fetchStarredRepositories
  } from './lib/github.js'

  const CACHE_MAX_AGE = 15 * 60 * 1000
  const DEMO_REPOSITORIES = createMockRepositories(3247)

  let repositories = DEMO_REPOSITORIES
  let username = 'seclorum'
  let githubUser = null
  let sourceLabel = 'Demo data'
  let loadStatus = 'Showing generated demo repositories'
  let loadError = ''
  let loadingRepos = false
  let loadProgress = { page: 0, count: 0, done: false }

  let states = {}
  let selected = null
  let activeCategory = 'all'
  let search = ''
  let showSettings = false

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
  }

  let loaded = false

  onMount(async () => {
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
  })

  $: categoryCounts = Object.fromEntries(
    CATEGORIES.map((category) => [
      category.id,
      repositories.filter((repo) => repo.category === category.id).length
    ])
  )

  $: filteredCount = repositories.filter((repo) => {
    if (
      activeCategory !== 'all' &&
      repo.category !== activeCategory
    ) return false

    if (!search.trim()) return true

    const query = search.toLowerCase()

    return [
      repo.full_name,
      repo.description,
      repo.language,
      ...(repo.topics || [])
    ]
      .join(' ')
      .toLowerCase()
      .includes(query)
  }).length

  $: pinnedCount = Object.values(states)
    .filter((state) => state.pinned)
    .length

  $: watchingCount = Object.values(states)
    .filter((state) => state.watching)
    .length

  function selectRepo(repo) {
    selected = repo
  }

  async function togglePin(repo) {
    const existing = states[repo.id] || {
      repoId: repo.id
    }

    const next = {
      ...existing,
      repoId: repo.id,
      pinned: !existing.pinned
    }

    states = {
      ...states,
      [repo.id]: next
    }

    await saveState(next)
  }

  async function toggleWatching(repo) {
    const existing = states[repo.id] || {
      repoId: repo.id
    }

    const next = {
      ...existing,
      repoId: repo.id,
      watching: !existing.watching
    }

    states = {
      ...states,
      [repo.id]: next
    }

    await saveState(next)
  }

  function openRepo(repo) {
    window.open(
      repo.html_url,
      '_blank',
      'noopener,noreferrer'
    )
  }

  function clearSearch() {
    search = ''
  }
</script>

<svelte:head>
  <title>Star Map</title>
</svelte:head>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">★</div>

      <div>
        <div class="brand-name">Star Map</div>
        <div class="brand-subtitle">
          Explore your GitHub starred repositories
        </div>
      </div>
    </div>

    <div class="search">
      <span class="search-icon">⌕</span>

      <input
        bind:value={search}
        placeholder="Search repositories...  (⌘K)"
        aria-label="Search repositories"
      />

      {#if search}
        <button
          class="search-clear"
          on:click={clearSearch}
          aria-label="Clear search"
        >
          ×
        </button>
      {/if}
    </div>

    <div class="account">
      <div class="github-mark">●</div>
      <span>{username}</span>
      <button
        class="icon-button"
        on:click={() => (showSettings = !showSettings)}
        aria-label="Settings"
      >
        ⚙
      </button>
    </div>
  </header>

  <main class="layout">
    <aside class="sidebar">
      <section>
        <div class="section-label">CATEGORIES</div>

        <button
          class:active={activeCategory === 'all'}
          class="category-row"
          on:click={() => (activeCategory = 'all')}
        >
          <span class="category-dot all"></span>
          <span class="category-name">All repositories</span>
          <span class="category-count">
            {repositories.length.toLocaleString()}
          </span>
        </button>

        {#each CATEGORIES as category}
          <button
            class:active={activeCategory === category.id}
            class="category-row"
            on:click={() => (activeCategory = category.id)}
          >
            <span
              class="category-dot"
              style={`background:${category.color}`}
            ></span>

            <span class="category-name">{category.name}</span>

            <span class="category-count">
              {categoryCounts[category.id]}
            </span>
          </button>
        {/each}
      </section>

      <div class="sidebar-divider"></div>

      <section>
        <div class="section-label">STATUS</div>

        <button class="status-row">
          <span class="status-symbol starred">★</span>
          <span>Starred</span>
          <span class="status-count">
            {repositories.length.toLocaleString()}
          </span>
        </button>

        <button class="status-row">
          <span class="status-symbol watching">◉</span>
          <span>Watching</span>
          <span class="status-count">{watchingCount}</span>
        </button>

        <button class="status-row">
          <span class="status-symbol pinned">⚑</span>
          <span>Pinned</span>
          <span class="status-count">{pinnedCount}</span>
        </button>
      </section>

      <div class="sidebar-footer">
        <div>{repositories.length.toLocaleString()} repositories</div>

        <div class="progress-track">
          <div
            class="progress"
            style={`width:${Math.min(
              100,
              (filteredCount / repositories.length) * 100
            )}%`}
          ></div>
        </div>
      </div>
    </aside>

    <section class="workspace">
      <div class="workspace-header">
        <div>
          <h1>Semantic Repository Map</h1>
          <p>
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
          {/if}
        </div>

        <div class="view-toggle">
          <button class="selected">Categories</button>
          <button disabled title="Coming in a later version">
            Semantic
          </button>
        </div>
      </div>

      <div class="map-container">
        <RepoMap
          {repositories}
          {states}
          {search}
          {activeCategory}
          selectedId={selected?.id}
          onSelect={selectRepo}
          onTogglePin={togglePin}
        />
      </div>
    </section>

    {#if selected}
      <aside class="inspector">
        <div class="inspector-header">
          <button
            class="close-button"
            on:click={() => (selected = null)}
            aria-label="Close repository inspector"
          >
            ×
          </button>
        </div>

        <div class="repo-heading">
          <div
            class="repo-avatar"
            style={`--repo-color:${
              CATEGORIES.find(
                (category) => category.id === selected.category
              )?.color || '#718096'
            }`}
          >
            {selected.owner.login.charAt(0).toUpperCase()}
          </div>

          <div class="repo-title">
            <h2>{selected.full_name}</h2>
            <p>{selected.description}</p>
          </div>
        </div>

        <div class="tags">
          <span class="tag">
            {CATEGORIES.find(
              (category) => category.id === selected.category
            )?.short}
          </span>

          {#if selected.language}
            <span class="tag">{selected.language}</span>
          {/if}

          {#each selected.topics.slice(0, 3) as topic}
            <span class="tag">{topic}</span>
          {/each}
        </div>

        <div class="stats">
          <div class="stat">
            <strong>★ {compactNumber(selected.stargazers_count)}</strong>
            <span>stars</span>
          </div>

          <div class="stat">
            <strong>⑂ {compactNumber(selected.forks_count)}</strong>
            <span>forks</span>
          </div>

          <div class="stat">
            <strong>{selected.language || '—'}</strong>
            <span>language</span>
          </div>
        </div>

        <div class="updated">
          ◷ Updated {relativeDate(selected.pushed_at)}
        </div>

        <div class="actions primary-actions">
          <button
            class:pinned={states[selected.id]?.pinned}
            on:click={() => togglePin(selected)}
          >
            ⚑
            {states[selected.id]?.pinned ? 'Pinned' : 'Pin'}
          </button>

          <button
            class:watching={states[selected.id]?.watching}
            on:click={() => toggleWatching(selected)}
          >
            ◉
            {states[selected.id]?.watching ? 'Watching' : 'Watch'}
          </button>
        </div>

        <div class="actions">
          <button on:click={() => openRepo(selected)}>
            ↗ Open
          </button>

          <button disabled title="GitHub API integration arrives in v0.2">
            ◉ Watch
          </button>

          <button disabled title="GitHub API integration arrives in v0.3">
            ♧ Subscribe
          </button>

          <button disabled title="More actions arrive in later versions">
            ···
          </button>
        </div>

        <section class="detail-section">
          <h3>Categories</h3>

          <div class="tags">
            <span class="tag highlighted">
              {CATEGORIES.find(
                (category) => category.id === selected.category
              )?.name}
            </span>
          </div>
        </section>

        <section class="detail-section">
          <h3>Description</h3>

          <p class="description">
            {selected.description}
          </p>
        </section>

        <section class="detail-section">
          <h3>Topics</h3>

          <div class="tags">
            {#if selected.topics.length}
              {#each selected.topics as topic}
                <span class="tag">{topic}</span>
              {/each}
            {:else}
              <span class="muted">No topics</span>
            {/if}
          </div>
        </section>

        <section class="detail-section">
          <h3>Links</h3>

          <button
            class="link-row"
            on:click={() => openRepo(selected)}
          >
            <span>◉ GitHub repository</span>
            <span>↗</span>
          </button>
        </section>

        <section class="detail-section">
          <h3>Personal notes</h3>

          <textarea
            placeholder="Add your notes..."
            aria-label="Personal notes"
          ></textarea>
        </section>
      </aside>
    {:else}
      <aside class="inspector empty-inspector">
        <div class="empty-content">
          <div class="empty-icon">✦</div>
          <h2>Select a repository</h2>
          <p>
            Click a repository in the map to inspect it,
            pin it, or open it on GitHub.
          </p>
        </div>
      </aside>
    {/if}
  </main>

  {#if showSettings}
    <div class="settings-popover">
      <strong>Star Map v0.2</strong>
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
      </div>
    </div>
  {/if}

  {#if !loaded}
    <div class="loading">
      <div class="loading-spinner"></div>
      <span>Loading Star Map…</span>
    </div>
  {/if}
</div>
