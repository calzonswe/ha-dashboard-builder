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

/** A card placed on the dashboard canvas */
export interface DashboardCard {
  id: string
  entity_id: string
  x: number
  y: number
  width: number
  height: number
  config?: CardConfig
}

/** Per-card configuration overrides */
export interface CardConfig {
  type: 'state' | 'gauge' | 'slider' | 'button' | 'list'
  title?: string
  color?: string
  theme?: 'light' | 'dark'
  accentColor?: string
  [key: string]: unknown
}

/** Full dashboard configuration stored on the server */
export interface DashboardConfig {
  id?: string
  title: string
  description?: string
  cards: DashboardCard[]
  layout: LayoutBlock[]
  created_at?: string
  updated_at?: string
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
