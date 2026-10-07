export function compactNumber(value) {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}m`
  }

  if (value >= 1000) {
    return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`
  }

  return String(value)
}

export function relativeDate(date) {
  const then = new Date(date).getTime()
  const now = Date.now()
  const days = Math.max(0, Math.floor((now - then) / 86400000))

  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 30) return `${days} days ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`

  return `${Math.floor(days / 365)} years ago`
}
