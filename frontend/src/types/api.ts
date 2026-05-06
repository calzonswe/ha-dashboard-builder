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

export interface DashboardConfig {
  id?: string
  title: string
  description?: string
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
