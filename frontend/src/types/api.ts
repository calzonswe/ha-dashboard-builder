export interface HAEntity {
  entity_id: string
  object_id: string
  state: string
  attributes: Record<string, unknown>
  last_changed: string
  last_updated: string
}

export interface HAState {
  entity_id: string
  state: string
  attributes: Record<string, unknown>
  last_changed: string
  last_updated: string
}

export interface HAEvent {
  event_type: string
  data: Record<string, unknown>
  time_fired: string
}

export interface DashboardCard {
  id: string
  entity_id: string
  x: number
  y: number
  width: number
  height: number
  config?: CardConfig
  card_type?: string
  title?: string
}

export interface CardConfig {
  type?: string
  title?: string
  color?: string
  theme?: 'light' | 'dark'
  accentColor?: string
  [key: string]: unknown
}

export interface DashboardConfig {
  id?: string
  name: string
  description?: string
  cards: DashboardCard[]
}

export type LayoutType = 'grid' | 'list' | 'canvas'

export interface LayoutBlock {
  id: string
  type: string
  x?: number
  y?: number
  width?: number
  height?: number
  props?: Record<string, unknown>
}
