from pathlib import Path

path = Path("src/lib/RepoMap.svelte")
source = path.read_text()

if source.count("<script>") != 1 or source.count("</script>") != 1:
    raise SystemExit("Unexpected script block structure; no changes made.")

start = source.index("<script>")
end = source.index("</script>") + len("</script>")
old_script = source[start:end]

new_script = r'''<script>
  import { onMount, onDestroy } from 'svelte'
  import * as d3 from 'd3'
  import { CATEGORIES } from './categories.js'

  export let repositories = []
  export let selectedId = null
  export let activeCategory = 'all'
  export let search = ''
  export let states = {}

  export let onSelect
  export let onTogglePin

  let canvas
  let container
  let width = 800
  let height = 800
  let pixelRatio = 1

  let simulation
  let nodes = []
  let transform = d3.zoomIdentity
  let hoveredId = null
  let zoomBehavior

  let visible = []
  let categoryPositions = {}
  let categoryCounts = {}

  const categoryById = Object.fromEntries(
    CATEGORIES.map((category) => [category.id, category])
  )

  function visibleRepositories() {
    const query = search.trim().toLowerCase()

    return repositories.filter((repo) => {
      if (
        activeCategory !== 'all' &&
        repo.category !== activeCategory
      ) {
        return false
      }

      if (!query) return true

      const haystack = [
        repo.full_name,
        repo.description,
        repo.language,
        ...(repo.topics || [])
      ]
        .join(' ')
        .toLowerCase()

      return haystack.includes(query)
    })
  }

  function configureCanvas() {
    if (!canvas || !container) return

    const rect = container.getBoundingClientRect()
    width = rect.width
    height = rect.height
    pixelRatio = window.devicePixelRatio || 1

    canvas.width = Math.round(width * pixelRatio)
    canvas.height = Math.round(height * pixelRatio)
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`

    const context = canvas.getContext('2d')
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
  }

  function getCategoryPositions(repos) {
    const categories = CATEGORIES.filter((category) =>
      repos.some((repo) => repo.category === category.id)
    )

    const cols = Math.max(2, Math.ceil(Math.sqrt(categories.length)))
    const rows = Math.max(1, Math.ceil(categories.length / cols))
    const result = {}

    categories.forEach((category, index) => {
      const col = index % cols
      const row = Math.floor(index / cols)

      result[category.id] = {
        x: width * ((col + 0.5) / cols),
        y: height * ((row + 0.5) / rows)
      }
    })

    return result
  }

  function rebuildLayout() {
    if (!canvas || !container) return

    configureCanvas()

    visible = visibleRepositories()
    categoryPositions = getCategoryPositions(visible)
    categoryCounts = Object.fromEntries(
      CATEGORIES.map((category) => [
        category.id,
        visible.filter((repo) => repo.category === category.id).length
      ])
    )

    const previousPositions = new Map(
      nodes.map((node) => [node.id, { x: node.x, y: node.y }])
    )

    nodes = visible.map((repo) => {
      const previous = previousPositions.get(repo.id)
      const category = categoryById[repo.category] || categoryById.other

      return {
        ...repo,
        radius: Math.max(
          2,
          Math.min(13, 2 + Math.sqrt(repo.stargazers_count || 0) / 42)
        ),
        color: category.color,
        x: previous?.x ?? (
          categoryPositions[repo.category]?.x ??
          width / 2
        ) + (Math.random() - 0.5) * width * 0.12,
        y: previous?.y ?? (
          categoryPositions[repo.category]?.y ??
          height / 2
        ) + (Math.random() - 0.5) * height * 0.12
      }
    })

    if (hoveredId && !nodes.some((node) => node.id === hoveredId)) {
      hoveredId = null
    }

    simulation?.stop()

    simulation = d3.forceSimulation(nodes)
      .force(
        'x',
        d3.forceX((node) =>
          categoryPositions[node.category]?.x ?? width / 2
        ).strength(0.08)
      )
      .force(
        'y',
        d3.forceY((node) =>
          categoryPositions[node.category]?.y ?? height / 2
        ).strength(0.08)
      )
      .force(
        'collide',
        d3.forceCollide((node) => node.radius + 1.5).iterations(2)
      )
      .alphaDecay(0.035)
      .on('tick', draw)

    draw()
  }

  function setupZoom() {
    if (!canvas || zoomBehavior) return

    zoomBehavior = d3.zoom()
      .scaleExtent([0.35, 5])
      .on('zoom', (event) => {
        transform = event.transform
        draw()
      })

    d3.select(canvas).call(zoomBehavior)
  }

  function draw() {
    if (!canvas) return

    const context = canvas.getContext('2d')
    context.save()
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
    context.clearRect(0, 0, width, height)

    context.translate(transform.x, transform.y)
    context.scale(transform.k, transform.k)

    drawCategoryLabels(context)

    for (const node of nodes) {
      const state = states[node.id]
      const selected = node.id === selectedId
      const hovered = node.id === hoveredId
      const pinned = state?.pinned

      context.globalAlpha = search || activeCategory !== 'all' ? 0.92 : 0.78
      context.beginPath()
      context.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
      context.fillStyle = node.color
      context.fill()

      if (pinned || selected || hovered) {
        context.globalAlpha = 1
        context.beginPath()
        context.arc(
          node.x,
          node.y,
          node.radius + (selected ? 6 : 4),
          0,
          Math.PI * 2
        )
        context.strokeStyle = pinned ? '#f6c945' : '#ffffff'
        context.lineWidth = selected ? 2 : 1
        context.stroke()
      }
    }

    if (hoveredId) {
      const node = nodes.find((item) => item.id === hoveredId)

      if (node) {
        context.globalAlpha = 1
        context.font = '600 12px Inter, system-ui, sans-serif'

        const label = node.full_name
        const padding = 8
        const boxWidth = context.measureText(label).width + padding * 2
        const boxHeight = 28

        context.fillStyle = '#0b1524'
        context.beginPath()
        context.roundRect(
          node.x + 12,
          node.y - 22,
          boxWidth,
          boxHeight,
          6
        )
        context.fill()

        context.strokeStyle = '#26384f'
        context.stroke()

        context.fillStyle = '#f4f7fb'
        context.fillText(label, node.x + 12 + padding, node.y - 4)
      }
    }

    context.restore()
  }

  function drawCategoryLabels(context) {
    context.textAlign = 'center'
    context.font = '600 12px Inter, system-ui, sans-serif'

    for (const category of CATEGORIES) {
      const position = categoryPositions[category.id]
      const count = categoryCounts[category.id] || 0

      if (!position || !count) continue

      const label = `${category.name}  ${count}`
      const metrics = context.measureText(label)

      context.fillStyle = category.color
      context.globalAlpha = 0.16
      context.beginPath()
      context.roundRect(
        position.x - metrics.width / 2 - 14,
        position.y - 115,
        metrics.width + 28,
        28,
        14
      )
      context.fill()

      context.globalAlpha = 0.9
      context.fillStyle = category.color
      context.fillText(label, position.x, position.y - 96)
    }
  }

  function pointerPosition(event) {
    const rect = canvas.getBoundingClientRect()

    return {
      x: (event.clientX - rect.left - transform.x) / transform.k,
      y: (event.clientY - rect.top - transform.y) / transform.k
    }
  }

  function hitTest(event) {
    const point = pointerPosition(event)

    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i]
      const dx = point.x - node.x
      const dy = point.y - node.y

      if (Math.sqrt(dx * dx + dy * dy) <= Math.max(node.radius + 5, 8)) {
        return node
      }
    }

    return null
  }

  function handleMove(event) {
    const node = hitTest(event)
    const nextHoveredId = node?.id ?? null

    if (nextHoveredId === hoveredId) return

    hoveredId = nextHoveredId
    canvas.style.cursor = node ? 'pointer' : 'default'
    draw()
  }

  function handleClick(event) {
    const node = hitTest(event)
    if (node) onSelect?.(node)
  }

  function resize() {
    if (!canvas || !container) return

    configureCanvas()

    categoryPositions = getCategoryPositions(visible)

    simulation
      ?.force(
        'x',
        d3.forceX((node) =>
          categoryPositions[node.category]?.x ?? width / 2
        ).strength(0.08)
      )
      .force(
        'y',
        d3.forceY((node) =>
          categoryPositions[node.category]?.y ?? height / 2
        ).strength(0.08)
      )
      .alpha(0.2)
      .restart()

    draw()
  }

  // Rebuild the node layout only when the repository set or filters change.
  $: if (
    canvas &&
    container &&
    repositories &&
    activeCategory !== undefined &&
    search !== undefined
  ) {
    rebuildLayout()
  }

  // State and selection changes only need a redraw, not a new simulation.
  $: if (
    canvas &&
    nodes &&
    selectedId !== undefined &&
    states !== undefined
  ) {
    draw()
  }

  onMount(() => {
    setupZoom()
    window.addEventListener('resize', resize)
  })

  onDestroy(() => {
    window.removeEventListener('resize', resize)
    simulation?.stop()
    if (canvas) d3.select(canvas).on('.zoom', null)
  })
</script>'''

path.write_text(source[:start] + new_script + source[end:])
print(f"Updated {path}")

