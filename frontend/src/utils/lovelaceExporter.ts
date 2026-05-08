import { DashboardConfig, DashboardCard } from '../types/api'

/**
 * Map our internal card types to Home Assistant Lovelace card types.
 */
function mapCardType(card: DashboardCard): string {
  const type = card.config?.type || 'state'
  switch (type) {
    case 'gauge':
      return 'gauge'
    case 'slider':
      return 'button' // HA native button; slider-entity-row is for entity-row, not cards
    case 'list':
      return 'entities'
    default:
      return 'entities'
  }
}

/**
 * Build a single HA Lovelace card from our DashboardCard.
 */
function buildLovelaceCard(card: DashboardCard): Record<string, unknown> {
  const type = mapCardType(card)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const config: any = card.config || {}
  const entityId = card.entity_id || ''

  // Extract domain for icon / entity-specific options
  const parts = entityId.split('.')
  const domain = parts[0] || 'sensor'

  const base: Record<string, unknown> = { type }

  if (type === 'entities') {
    base.entities = [entityId]
    if (config.title) base.name = config.title as string
    // Show state + icon by default
    base.icon = `mdi:${domain}`
  } else if (type === 'gauge') {
    base.entity = entityId
    if (config.title) base.name = config.title as string
    base.min = typeof config.min === 'number' ? config.min : 0
    base.max = typeof config.max === 'number' ? config.max : 100
    base.separator = Array.isArray(config.separator)
      ? config.separator
      : [2, ' ']
    // Map accent color to gauge color if present
    if (config.accentColor) {
      base.color = config.accentColor as string
    }
  } else if (type === 'button') {
    base.type = 'button'
    base.entity = entityId
    if (config.title) base.name = config.title as string
    // Map theme to icon color
    if (config.theme === 'dark') {
      base.icon_color = '#ffffff'
    } else if (config.accentColor) {
      base.icon_color = config.accentColor as string
    }
  }

  return base
}

/**
 * Convert our DashboardConfig to a Home Assistant Lovelace JSON string.
 *
 * The output is a single-view Lovelace configuration that can be imported
 * directly into HA via the UI or configuration.yaml.
 */
export function exportToLovelace(dashboard: DashboardConfig): string {
  // Build cards array
  const lovelaceCards = dashboard.cards.map(buildLovelaceCard)

  // Collect unique entity domains for icon selection
  const domainCounts: Record<string, number> = {}
  for (const card of dashboard.cards) {
    const parts = (card.entity_id || '').split('.')
    const domain = parts[0] || 'sensor'
    domainCounts[domain] = (domainCounts[domain] || 0) + 1
  }

  // Pick the most common domain for the view icon
  let bestDomain = 'sensor'
  let bestCount = 0
  for (const [domain, count] of Object.entries(domainCounts)) {
    if (count > bestCount) {
      bestCount = count
      bestDomain = domain
    }
  }

  const iconMap: Record<string, string> = {
    light: 'lightbulb',
    sensor: 'sensor',
    switch: 'toggle-switch',
    cover: 'window-shade',
    fan: 'fan',
    climate: 'thermostat',
    media_player: 'music-note',
    camera: 'camera',
  }

  const viewConfig: Record<string, unknown> = {
    title: dashboard.name || 'Home Assistant Dashboard',
    path: 'default',
    icon: `mdi:${iconMap[bestDomain] || 'home'}`,
    cards: lovelaceCards,
    badges: [],
  }

  const lovelaceConfig = {
    title: dashboard.name || 'Home Assistant Dashboard',
    views: [viewConfig],
  }

  return JSON.stringify(lovelaceConfig, null, 2)
}

/**
 * Convert a DashboardConfig to Home Assistant Lovelace YAML string.
 */
export function exportToLovelaceYaml(dashboard: DashboardConfig): string {
  const lines: string[] = []
  lines.push(`title: '${dashboard.name}'`)
  lines.push('')
  lines.push('views:')
  lines.push(`  - title: '${dashboard.name}'`)
  lines.push('    path: default')

  // Collect domains for icon
  const domainCounts: Record<string, number> = {}
  for (const card of dashboard.cards) {
    const parts = (card.entity_id || '').split('.')
    const domain = parts[0] || 'sensor'
    domainCounts[domain] = (domainCounts[domain] || 0) + 1
  }

  let bestDomain = 'sensor'
  let bestCount = 0
  for (const [domain, count] of Object.entries(domainCounts)) {
    if (count > bestCount) {
      bestCount = count
      bestDomain = domain
    }
  }

  const iconMap: Record<string, string> = {
    light: 'lightbulb',
    sensor: 'sensor',
    switch: 'toggle-switch',
    cover: 'window-shade',
    fan: 'fan',
    climate: 'thermostat',
    media_player: 'music-note',
    camera: 'camera',
  }

  lines.push(`    icon: mdi:${iconMap[bestDomain] || 'home'}`)
  lines.push('    cards:')

  for (const card of dashboard.cards) {
    const type = mapCardType(card)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const config: any = card.config || {}
    const entityId = card.entity_id || ''

    if (type === 'entities') {
      lines.push(`      - type: entities`)
      lines.push(`        entity: ${entityId}`)
      if (config.title) {
        lines.push(`        name: '${config.title}'`)
      }
      lines.push(`        icon: mdi:${bestDomain}`)
    } else if (type === 'gauge') {
      lines.push(`      - type: gauge`)
      lines.push(`        entity: ${entityId}`)
      if (config.title) {
        lines.push(`        name: '${config.title}'`)
      }
      const min = typeof config.min === 'number' ? config.min : 0
      const max = typeof config.max === 'number' ? config.max : 100
      lines.push(`        min: ${min}`)
      lines.push(`        max: ${max}`)
    } else if (type === 'button') {
      lines.push(`      - type: button`)
      lines.push(`        entity: ${entityId}`)
      if (config.title) {
        lines.push(`        name: '${config.title}'`)
      }
    }

    lines.push('') // blank line between cards
  }

  return lines.join('\n').trim()
}
