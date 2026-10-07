<script>
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

  let simulation
  let nodes = []
  let transform = d3.zoomIdentity
  let hoveredId = null

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

  function setup() {
    if (!canvas || !container) return

    const rect = container.getBoundingClientRect()
    width = rect.width
    height = rect.height

    canvas.width = width * devicePixelRatio
    canvas.height = height * devicePixelRatio
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`

    const context = canvas.getContext('2d')
    context.scale(devicePixelRatio, devicePixelRatio)

    nodes = visibleRepositories().map((repo) => {
      const category = categoryById[repo.category] || categoryById.other

      return {
        ...repo,
        radius: Math.max(
          2,
          Math.min(
            13,
            2 + Math.sqrt(repo.stargazers_count) / 42
          )
        ),
        color: category.color,
        x: width / 2 + (Math.random() - 0.5) * width * 0.5,
        y: height / 2 + (Math.random() - 0.5) * height * 0.5
      }
    })

    const categoryPositions = getCategoryPositions()

    simulation?.stop()

    simulation = d3
      .forceSimulation(nodes)
      .force(
        'x',
        d3.forceX((d) => categoryPositions[d.category]?.x ?? width / 2)
          .strength(0.08)
      )
      .force(
        'y',
        d3.forceY((d) => categoryPositions[d.category]?.y ?? height / 2)
          .strength(0.08)
      )
      .force(
        'collide',
        d3.forceCollide((d) => d.radius + 1.5)
          .iterations(2)
      )
      .alphaDecay(0.035)
      .on('tick', draw)

    setupZoom()
    draw()
  }

  function getCategoryPositions() {
    const categories = CATEGORIES.filter((category) =>
      visibleRepositories().some((repo) => repo.category === category.id)
    )

    const cols = Math.max(2, Math.ceil(Math.sqrt(categories.length)))
    const rows = Math.ceil(categories.length / cols)

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

  function setupZoom() {
    const selection = d3.select(canvas)

    selection.call(
      d3.zoom()
        .scaleExtent([0.35, 5])
        .on('zoom', (event) => {
          transform = event.transform
          draw()
        })
    )
  }

  function draw() {
    if (!canvas) return

    const context = canvas.getContext('2d')

    context.save()
    context.clearRect(0, 0, width, height)

    context.translate(transform.x, transform.y)
    context.scale(transform.k, transform.k)

    drawCategoryLabels(context)

    for (const node of nodes) {
      const state = states[node.id]
      const selected = node.id === selectedId
      const hovered = node.id === hoveredId
      const pinned = state?.pinned

      context.globalAlpha =
        search || activeCategory !== 'all'
          ? 0.92
          : 0.78

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
        context.strokeStyle = pinned
          ? '#f6c945'
          : '#ffffff'
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
        const metrics = context.measureText(label)
        const boxWidth = metrics.width + padding * 2
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
        context.fillText(
          label,
          node.x + 12 + padding,
          node.y - 4
        )
      }
    }

    context.restore()
  }

  function drawCategoryLabels(context) {
    const positions = getCategoryPositions()

    context.textAlign = 'center'
    context.font = '600 12px Inter, system-ui, sans-serif'

    for (const category of CATEGORIES) {
      const position = positions[category.id]

      if (!position) continue

      const count = visibleRepositories()
        .filter((repo) => repo.category === category.id)
        .length

      if (!count) continue

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
      context.fillText(
        label,
        position.x,
        position.y - 96
      )
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
      const distance = Math.sqrt(dx * dx + dy * dy)

      if (distance <= Math.max(node.radius + 5, 8)) {
        return node
      }
    }

    return null
  }

  function handleMove(event) {
    const node = hitTest(event)
    hoveredId = node?.id ?? null
    canvas.style.cursor = node ? 'pointer' : 'default'
    draw()
  }

  function handleClick(event) {
    const node = hitTest(event)

    if (!node) return

    onSelect?.(node)
  }

  function resize() {
    setup()
  }

  $: if (
    repositories &&
    repositories.length &&
    canvas &&
    container
  ) {
    setup()
  }

  onMount(() => {
    window.addEventListener('resize', resize)
    setup()
  })

  onDestroy(() => {
    window.removeEventListener('resize', resize)
    simulation?.stop()
  })
</script>

<div class="map" bind:this={container}>
  <canvas
    bind:this={canvas}
    on:mousemove={handleMove}
    on:mouseleave={() => {
      hoveredId = null
      draw()
    }}
    on:click={handleClick}
  ></canvas>

  <div class="map-hint">
    <span>Scroll to zoom</span>
    <span>Drag to move</span>
    <span>Click a repository</span>
  </div>

  <div class="size-legend">
    <span class="legend-dot small"></span>
    <span class="legend-dot medium"></span>
    <span class="legend-dot large"></span>
    <span>= more stars</span>
  </div>
</div>

<style>
  .map {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 600px;
    overflow: hidden;
    background:
      radial-gradient(
        circle at 50% 45%,
        rgba(25, 64, 105, 0.11),
        transparent 52%
      );
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }

  .map-hint,
  .size-legend {
    position: absolute;
    bottom: 16px;
    padding: 8px 11px;
    border: 1px solid #1e3047;
    border-radius: 8px;
    background: rgba(7, 17, 31, 0.86);
    color: #708198;
    font-size: 10px;
    pointer-events: none;
    backdrop-filter: blur(10px);
  }

  .map-hint {
    left: 16px;
    display: flex;
    gap: 14px;
  }

  .size-legend {
    right: 16px;
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .legend-dot {
    display: inline-block;
    border-radius: 50%;
    border: 1px solid #60748c;
  }

  .small {
    width: 5px;
    height: 5px;
  }

  .medium {
    width: 9px;
    height: 9px;
  }

  .large {
    width: 14px;
    height: 14px;
  }
</style>
