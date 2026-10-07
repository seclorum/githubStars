export const CATEGORIES = [
  {
    id: 'ai',
    name: 'AI / Machine Learning',
    short: 'AI / ML',
    color: '#1597ff',
    keywords: [
      'ai', 'artificial-intelligence', 'machine-learning', 'ml',
      'deep-learning', 'llm', 'gpt', 'nlp', 'neural', 'transformer',
      'agents', 'agent', 'computer-vision', 'speech', 'embedding'
    ]
  },
  {
    id: 'web',
    name: 'Web Development',
    short: 'Web',
    color: '#18b968',
    keywords: [
      'web', 'frontend', 'backend', 'javascript', 'typescript',
      'react', 'vue', 'svelte', 'nextjs', 'node', 'html', 'css'
    ]
  },
  {
    id: 'tools',
    name: 'Developer Tools',
    short: 'Tools',
    color: '#8746e8',
    keywords: [
      'developer-tools', 'devtools', 'cli', 'terminal', 'git',
      'editor', 'vim', 'neovim', 'debugging', 'compiler', 'build',
      'sdk', 'library', 'productivity'
    ]
  },
  {
    id: 'data',
    name: 'Data & Analytics',
    short: 'Data',
    color: '#f5a900',
    keywords: [
      'data', 'database', 'analytics', 'sql', 'postgres', 'mysql',
      'data-science', 'visualization', 'etl', 'scraping', 'crawler'
    ]
  },
  {
    id: 'systems',
    name: 'Systems & DevOps',
    short: 'Systems',
    color: '#f05a3c',
    keywords: [
      'linux', 'system', 'systems', 'docker', 'kubernetes', 'devops',
      'cloud', 'distributed', 'networking', 'infrastructure', 'server'
    ]
  },
  {
    id: 'security',
    name: 'Security',
    short: 'Security',
    color: '#10c4c9',
    keywords: [
      'security', 'cybersecurity', 'crypto', 'cryptography', 'privacy',
      'authentication', 'vulnerability', 'pentest', 'malware'
    ]
  },
  {
    id: 'games',
    name: 'Games',
    short: 'Games',
    color: '#ed3f8d',
    keywords: [
      'game', 'games', 'gaming', 'unity', 'godot', 'unreal',
      'emulator', 'graphics'
    ]
  },
  {
    id: 'mobile',
    name: 'Mobile',
    short: 'Mobile',
    color: '#7650d8',
    keywords: [
      'mobile', 'android', 'ios', 'iphone', 'swift', 'kotlin',
      'flutter', 'react-native'
    ]
  },
  {
    id: 'other',
    name: 'Other',
    short: 'Other',
    color: '#718096',
    keywords: []
  }
]

export function categorizeRepository(repo) {
  const text = [
    repo.name,
    repo.full_name,
    repo.description,
    ...(repo.topics || []),
    repo.language
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()

  let best = CATEGORIES[CATEGORIES.length - 1]
  let bestScore = 0

  for (const category of CATEGORIES) {
    if (category.id === 'other') continue

    let score = 0

    for (const keyword of category.keywords) {
      if (text.includes(keyword)) {
        score += keyword.length > 5 ? 2 : 1
      }
    }

    if (repo.language) {
      const language = repo.language.toLowerCase()

      if (
        category.id === 'web' &&
        ['javascript', 'typescript', 'html', 'css'].includes(language)
      ) score += 3

      if (
        category.id === 'ai' &&
        ['python', 'jupyter notebook'].includes(language) &&
        /model|ml|llm|ai|neural|vision|nlp/.test(text)
      ) score += 3

      if (
        category.id === 'systems' &&
        ['rust', 'c', 'c++', 'go'].includes(language)
      ) score += 1
    }

    if (score > bestScore) {
      bestScore = score
      best = category
    }
  }

  return best
}
