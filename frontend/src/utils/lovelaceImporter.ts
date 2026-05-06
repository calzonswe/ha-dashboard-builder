import { DashboardConfig, DashboardCard, CardConfig } from '../types/api'

/**
 * Validate that a string looks like a valid HA entity_id.
 * Pattern: domain.object_id (e.g., "sensor.temperature")
 */
function isValidEntityId(entityId: string): boolean {
  return /^[a-z_]+\.[a-z0-9_-]+$/.test(entityId)
}

/**
 * Map HA Lovelace card types back to our internal card types.
 */
function mapCardType(haCardType: string, entityDomain?: string): CardConfig['type'] {
  switch (haCardType) {
    case 'gauge':
      return 'gauge'
    case 'button':
      // Could be button or slider — use domain hint if available
      if (entityDomain === 'input_number' || entityDomain === 'number') {
        return 'slider'
      }
      return 'button'
    case 'entities':
      return 'list'
    default:
      return 'state'
  }
}

/**
 * Extract the domain from a HA entity_id.
 */
function extractDomain(entityId: string): string {
  const parts = entityId.split('.')
  return parts[0] || ''
}

/**
 * Convert an array of HA Lovelace cards to our DashboardCard format.
 */
function convertHACardsToCards(cards: Record<string, unknown>[]): DashboardCard[] {
  return cards.map((haCard, index) => {
    const entityId = (haCard.entity as string) || ''
    const entityIds = Array.isArray(haCard.entities) ? haCard.entities : []
    const primaryEntityId = entityId || (entityIds[0] as string) || ''

    if (!primaryEntityId || !isValidEntityId(primaryEntityId)) {
      // Skip cards with invalid entity IDs
      return null as unknown as DashboardCard
    }

    const domain = extractDomain(primaryEntityId)
    const cardType = mapCardType(
      (haCard.type as string) || 'entities',
      domain,
    )

    const config: Partial<CardConfig> = {
      type: cardType,
    }

    if (haCard.name && typeof haCard.name === 'string') {
      config.title = haCard.name
    }

    // Extract numeric options for gauge cards
    if (cardType === 'gauge' || haCard.type === 'gauge') {
      if (typeof haCard.min === 'number') config.min = haCard.min
      if (typeof haCard.max === 'number') config.max = haCard.max
      if (haCard.color && typeof haCard.color === 'string') config.accentColor = haCard.color
    }

    // Extract color for button cards
    if (cardType === 'button' || haCard.type === 'button') {
      if (haCard.icon_color && typeof haCard.icon_color === 'string') {
        config.accentColor = haCard.icon_color
      }
    }

    return {
      id: `imported-${index}`,
      entity_id: primaryEntityId,
      x: 0,
      y: index * 120,
      width: 300,
      height: 150,
      config,
    } as DashboardCard
  }).filter((card): card is DashboardCard => {
    // Filter out cards with invalid entity IDs (we return null for those)
    return isValidEntityId(card.entity_id)
  })
}

/**
 * Validate a HA Lovelace JSON string and return parsed structure.
 */
function validateLovelaceJson(jsonString: string): { valid: boolean; error?: string } {
  try {
    const parsed = JSON.parse(jsonString)

    if (!parsed || typeof parsed !== 'object') {
      return { valid: false, error: 'Invalid JSON: root must be an object' }
    }

    // Check for views array (standard HA format) or top-level cards
    const hasViews = Array.isArray(parsed.views) && parsed.views.length > 0
    const hasCards = Array.isArray(parsed.cards) && parsed.cards.length > 0

    if (!hasViews && !hasCards) {
      return { valid: false, error: 'Invalid Lovelace config: missing "views" or "cards" array' }
    }

    // Validate cards within views
    const allCards = hasViews ? parsed.views.flatMap((v: Record<string, unknown>) => v.cards || []) : parsed.cards
    for (const card of allCards) {
      if (!card || typeof card !== 'object') continue
      const entityId = card.entity || ''
      const entityIds = Array.isArray(card.entities) ? card.entities : []
      const primaryEntityId = entityId || (entityIds[0] as string) || ''

      if (primaryEntityId && !isValidEntityId(primaryEntityId)) {
        return { valid: false, error: `Invalid entity_id in card: "${String(primaryEntityId)}"` }
      }
    }

    return { valid: true }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to parse JSON'
    return { valid: false, error: `Invalid JSON: ${message}` }
  }
}

/**
 * Import a Home Assistant Lovelace JSON string into our DashboardConfig format.
 *
 * Returns the dashboard config ready for editing in the builder.
 */
export function importFromLovelace(jsonString: string): {
  dashboard: DashboardConfig | null
  error?: string
} {
  const validation = validateLovelaceJson(jsonString)

  if (!validation.valid) {
    return { dashboard: null, error: validation.error }
  }

  try {
    const parsed = JSON.parse(jsonString) as Record<string, unknown>

    // Extract cards from views or top-level
    let cards: DashboardCard[] = []
    let title = 'Imported Dashboard'

    if (Array.isArray(parsed.views)) {
      // Use the first view's title if available
      const firstView = parsed.views[0] as Record<string, unknown>
      if (firstView && typeof firstView === 'object') {
        title = (firstView.title as string) || (parsed.title as string) || 'Imported Dashboard'
      }

      // Collect cards from all views
      for (const view of parsed.views) {
        const viewObj = view as Record<string, unknown>
        if (viewObj && Array.isArray(viewObj.cards)) {
          cards = cards.concat(convertHACardsToCards(viewObj.cards))
        }
      }
    } else if (Array.isArray(parsed.cards)) {
      // Top-level cards format (less common)
      title = (parsed.title as string) || 'Imported Dashboard'
      cards = convertHACardsToCards(parsed.cards)
    }

    return {
      dashboard: {
        id: undefined,
        title,
        description: 'Imported from Home Assistant Lovelace configuration',
        cards,
        layout: [],
      },
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to parse dashboard'
    return { dashboard: null, error: `Parse error: ${message}` }
  }
}
