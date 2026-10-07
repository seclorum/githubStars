import { CATEGORIES, categorizeRepository } from '../lib/categories.js'

const OWNERS = [
  'openai',
  'anthropic',
  'google',
  'microsoft',
  'facebook',
  'vercel',
  'sveltejs',
  'github',
  'rust-lang',
  'torvalds',
  'huggingface',
  'home-assistant',
  'denoland',
  'ollama',
  'supabase',
  'langchain-ai',
  'astral-sh',
  'docker',
  'kubernetes',
  'mozilla'
]

const NAMES = {
  ai: [
    'whisper', 'transformers', 'llama', 'agents', 'diffusion',
    'embeddings', 'vision', 'inference', 'semantic-search',
    'neural-engine', 'rag-toolkit', 'voice-ai'
  ],
  web: [
    'svelte', 'next', 'react', 'astro', 'vite', 'web-components',
    'frontend-kit', 'server', 'web-framework', 'edge-runtime'
  ],
  tools: [
    'ripgrep', 'starship', 'terminal', 'devtools', 'code-search',
    'editor', 'cli', 'dotfiles', 'git-tools', 'task-runner'
  ],
  data: [
    'duckdb', 'polars', 'analytics', 'dataframes', 'sqlite',
    'vector-db', 'data-viz', 'crawler', 'dataset-tools'
  ],
  systems: [
    'docker', 'kubernetes', 'linux', 'containerd', 'distributed',
    'proxy', 'network', 'runtime', 'orchestrator'
  ],
  security: [
    'vault', 'scanner', 'secrets', 'auth', 'cryptography',
    'security-tools', 'sandbox', 'firewall'
  ],
  games: [
    'godot', 'game-engine', 'emulator', 'pixel-engine',
    'graphics', 'raycaster'
  ],
  mobile: [
    'swift-ui', 'android-kit', 'flutter', 'mobile-ui',
    'ios-tools', 'kotlin-utils'
  ],
  other: [
    'awesome-project', 'notes', 'research', 'experiments',
    'documentation', 'misc-tools'
  ]
}

const LANGUAGES = {
  ai: ['Python', 'Python', 'Rust', 'C++', 'Jupyter Notebook'],
  web: ['TypeScript', 'JavaScript', 'Svelte', 'TypeScript'],
  tools: ['Rust', 'Go', 'Python', 'C++'],
  data: ['Python', 'Rust', 'SQL', 'TypeScript'],
  systems: ['Rust', 'Go', 'C', 'C++'],
  security: ['Rust', 'Go', 'Python', 'C'],
  games: ['C++', 'C#', 'Rust', 'GDScript'],
  mobile: ['Swift', 'Kotlin', 'Dart'],
  other: ['Python', 'Rust', 'JavaScript', 'Go']
}

function seeded(seed) {
  const x = Math.sin(seed * 12.9898) * 43758.5453
  return x - Math.floor(x)
}

export function createMockRepositories(count = 3247) {
  const categoryIds = CATEGORIES.map((c) => c.id)

  return Array.from({ length: count }, (_, index) => {
    const categoryId = categoryIds[index % categoryIds.length]
    const category = CATEGORIES.find((c) => c.id === categoryId)
    const names = NAMES[categoryId]
    const owner = OWNERS[Math.floor(seeded(index + 3) * OWNERS.length)]
    const name = names[index % names.length]
    const suffix = Math.floor(index / names.length)

    const fullName = `${owner}/${name}${suffix > 0 ? `-${suffix}` : ''}`

    const stars = Math.max(
      12,
      Math.floor(
        Math.pow(seeded(index + 19), 2.2) * 125000
      )
    )

    const forks = Math.floor(stars * (0.02 + seeded(index + 31) * 0.35))

    const languageList = LANGUAGES[categoryId]
    const language = languageList[index % languageList.length]

    const topicWords = category.keywords.length
      ? category.keywords
          .slice(0, 3)
          .filter((_, i) => seeded(index + i * 17) > 0.25)
      : []

    const repo = {
      id: index + 1,
      full_name: fullName,
      name,
      owner: {
        login: owner,
        avatar_url: ''
      },
      html_url: `https://github.com/${fullName}`,
      description: `${category.name} project exploring ${name.replaceAll('-', ' ')} and related ideas.`,
      topics: topicWords,
      language,
      stargazers_count: stars,
      forks_count: forks,
      archived: seeded(index + 41) > 0.97,
      fork: seeded(index + 43) > 0.93,
      pushed_at: new Date(
        Date.now() - seeded(index + 52) * 1000 * 60 * 60 * 24 * 900
      ).toISOString()
    }

    repo.category = categorizeRepository(repo).id

    return repo
  })
}
