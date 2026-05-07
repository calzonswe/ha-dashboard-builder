"""Dashboard and widget CRUD API routes (Phase 4).

Provides endpoints for creating, listing, and managing dashboards
and their associated widgets/cards.
"""

from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, Page, Card
from .schemas import (
    DashboardCreateRequest,
    DashboardUpdateRequest,
    DashboardResponse,
    DashboardListResponse,
    WidgetCreateRequest,
    CardUpdateRequest,
    WidgetResponse,
    WidgetListResponse,
    FullDashboardResponse,
    CardsBulkUpdateRequest,
    CardsBulkUpdateResponse,
)

router = APIRouter()


# ------------------------------------------------------------------
# Dashboard (Page) CRUD
# ------------------------------------------------------------------


@router.get("/dashboards", response_model=DashboardListResponse)
def list_dashboards(db: Session = Depends(get_db)):
    """Return all dashboards.

    GET /api/v1/dashboards -> 200 { "dashboards": [...], "count": N }
    """
    pages = db.query(Page).order_by(Page.created_at.desc()).all()
    dashboards = [
        DashboardResponse(
            id=page.id,
            name=page.name or "",
            description=None,  # Page model doesn't have a description field yet
        )
        for page in pages
    ]
    return DashboardListResponse(dashboards=dashboards, count=len(dashboards))


@router.post("/dashboards", response_model=DashboardResponse, status_code=201)
def create_dashboard(req: DashboardCreateRequest, db: Session = Depends(get_db)):
    """Create a new dashboard.

    POST /api/v1/dashboards -> 201 { "id": N, "name": "...", ... }
    """
    page = Page(name=req.name, description=req.description or "")
    db.add(page)
    db.commit()
    db.refresh(page)
    return DashboardResponse(id=page.id, name=page.name or "", description=page.description if page.description != "" else None)


@router.put("/dashboards/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(dashboard_id: int, req: DashboardUpdateRequest, db: Session = Depends(get_db)):
    """Update an existing dashboard.

    PUT /api/v1/dashboards/1 -> 200 { "id": 1, "name": "...", ... }
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    if req.name is not None:
        page.name = req.name
    if req.description is not None:
        page.description = req.description
    db.commit()
    db.refresh(page)
    return DashboardResponse(id=page.id, name=page.name or "", description=page.description if page.description != "" else None)


@router.get("/dashboards/{dashboard_id}", response_model=FullDashboardResponse)
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Return a single dashboard with all its widgets.

    GET /api/v1/dashboards/1 -> 200 { "id": 1, "name": "...", "cards": [...] }
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    cards = (
        db.query(Card)
        .filter(Card.page_id == dashboard_id)
        .order_by(Card.y, Card.x)
        .all()
    )
    widgets = [
        WidgetResponse(
            id=card.id,
            page_id=card.page_id or 0,
            card_type=card.card_type or "",
            entity_id=card.entity_id if card.entity_id != "" else None,
            title=card.title if card.title != "" else None,
            config=card.config or {},
            x=card.x or 0,
            y=card.y or 0,
            width=card.width or 1,
            height=card.height or 1,
        )
        for card in cards
    ]

    return FullDashboardResponse(
        id=page.id,
        name=page.name or "",
        description=None,
        cards=widgets,
    )


# ------------------------------------------------------------------
# Widget (Card) CRUD
# ------------------------------------------------------------------


@router.get("/dashboards/{dashboard_id}/widgets", response_model=WidgetListResponse)
def list_widgets(dashboard_id: int, db: Session = Depends(get_db)):
    """Return all widgets on a dashboard.

    GET /api/v1/dashboards/1/widgets -> 200 { "widgets": [...], "count": N }
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    cards = (
        db.query(Card)
        .filter(Card.page_id == dashboard_id)
        .order_by(Card.y, Card.x)
        .all()
    )
    widgets = [
        WidgetResponse(
            id=card.id,
            page_id=card.page_id or 0,
            card_type=card.card_type or "",
            entity_id=card.entity_id if card.entity_id != "" else None,
            title=card.title if card.title != "" else None,
            config=card.config or {},
            x=card.x or 0,
            y=card.y or 0,
            width=card.width or 1,
            height=card.height or 1,
        )
        for card in cards
    ]
    return WidgetListResponse(widgets=widgets, count=len(widgets))


@router.post("/dashboards/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=201)
def create_widget(dashboard_id: int, req: WidgetCreateRequest, db: Session = Depends(get_db)):
    """Add a widget to a dashboard.

    POST /api/v1/dashboards/1/widgets -> 201 { "id": N, ... }
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    card = Card(
        page_id=dashboard_id,
        card_type=req.card_type,
        entity_id=req.entity_id or "",
        title=req.title or "",
        config=req.config or {},
        x=req.x,
        y=req.y,
        width=req.width,
        height=req.height,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return WidgetResponse(
        id=card.id,
        page_id=card.page_id or 0,
        card_type=card.card_type or "",
        entity_id=card.entity_id if card.entity_id != "" else None,
        title=card.title if card.title != "" else None,
        config=card.config or {},
        x=card.x or 0,
        y=card.y or 0,
        width=card.width or 1,
        height=card.height or 1,
    )


@router.put("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
def update_widget(
    dashboard_id: int, widget_id: int, req: CardUpdateRequest, db: Session = Depends(get_db)
):
    """Update an existing widget (partial update — only provided fields change).

    PUT /api/v1/dashboards/1/widgets/1 -> 200 { ... }
    """
    card = (
        db.query(Card)
        .filter(Card.id == widget_id, Card.page_id == dashboard_id)
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Only update fields that were provided (not None)
    if req.card_type is not None:
        card.card_type = req.card_type
    if req.entity_id is not None:
        card.entity_id = req.entity_id or ""
    if req.title is not None:
        card.title = req.title or ""
    if req.config is not None:
        card.config = req.config or {}
    if req.x is not None:
        card.x = req.x
    if req.y is not None:
        card.y = req.y
    if req.width is not None:
        card.width = req.width
    if req.height is not None:
        card.height = req.height
    db.commit()
    db.refresh(card)

    return WidgetResponse(
        id=card.id,
        page_id=card.page_id or 0,
        card_type=card.card_type or "",
        entity_id=card.entity_id if card.entity_id != "" else None,
        title=card.title if card.title != "" else None,
        config=card.config or {},
        x=card.x or 0,
        y=card.y or 0,
        width=card.width or 1,
        height=card.height or 1,
    )


@router.put("/dashboards/{dashboard_id}/cards", response_model=CardsBulkUpdateResponse)
def bulk_update_cards(dashboard_id: int, req: CardsBulkUpdateRequest, db: Session = Depends(get_db)):
    """Replace all cards (widgets) on a dashboard atomically.

    This is the primary save endpoint used by the frontend drag-and-drop builder.
    Existing cards with matching IDs are updated; new cards (no ID) are created;
    cards not in the request are deleted.

    PUT /api/v1/dashboards/1/cards -> 200 { "cards": [...] }
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Collect IDs of cards in the request for deletion logic
    incoming_ids = {c.id for c in req.cards if c.id is not None}

    # Delete cards that are no longer in the request (and have an ID)
    existing_cards = db.query(Card).filter(Card.page_id == dashboard_id).all()
    for card in existing_cards:
        if card.id not in incoming_ids:
            db.delete(card)

    # Process each card in the request — update or create
    result_widgets = []
    for card_req in req.cards:
        if card_req.id is not None:
            # Update existing card
            card = (
                db.query(Card)
                .filter(Card.id == card_req.id, Card.page_id == dashboard_id)
                .first()
            )
            if card:
                card.card_type = card_req.card_type
                card.entity_id = card_req.entity_id or ""
                card.title = card_req.title or ""
                card.config = card_req.config or {}
                card.x = card_req.x
                card.y = card_req.y
                card.width = card_req.width
                card.height = card_req.height
            else:
                # Card ID doesn't belong to this dashboard — create new
                card = Card(
                    page_id=dashboard_id,
                    card_type=card_req.card_type,
                    entity_id=card_req.entity_id or "",
                    title=card_req.title or "",
                    config=card_req.config or {},
                    x=card_req.x,
                    y=card_req.y,
                    width=card_req.width,
                    height=card_req.height,
                )
                db.add(card)
        else:
            # New card — create it
            card = Card(
                page_id=dashboard_id,
                card_type=card_req.card_type,
                entity_id=card_req.entity_id or "",
                title=card_req.title or "",
                config=card_req.config or {},
                x=card_req.x,
                y=card_req.y,
                width=card_req.width,
                height=card_req.height,
            )
            db.add(card)

    db.commit()

    # Fetch and return all cards for this dashboard (ordered by position)
    cards = (
        db.query(Card)
        .filter(Card.page_id == dashboard_id)
        .order_by(Card.y, Card.x)
        .all()
    )
    result_widgets = [
        WidgetResponse(
            id=card.id,
            page_id=card.page_id or 0,
            card_type=card.card_type or "",
            entity_id=card.entity_id if card.entity_id != "" else None,
            title=card.title if card.title != "" else None,
            config=card.config or {},
            x=card.x or 0,
            y=card.y or 0,
            width=card.width or 1,
            height=card.height or 1,
        )
        for card in cards
    ]

    return CardsBulkUpdateResponse(cards=result_widgets)


@router.delete("/dashboards/{dashboard_id}/widgets/{widget_id}", status_code=204)
def delete_widget(dashboard_id: int, widget_id: int, db: Session = Depends(get_db)):
    """Remove a single widget from a dashboard.

    DELETE /api/v1/dashboards/1/widgets/1 -> 204 (no content)
    """
    card = (
        db.query(Card)
        .filter(Card.id == widget_id, Card.page_id == dashboard_id)
        .first()
    )
    if not card:
        raise HTTPException(status_code=404, detail="Widget not found")

    try:
        db.delete(card)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to delete widget"
        )


@router.delete("/dashboards/{dashboard_id}", status_code=204)
def delete_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Delete a dashboard and all its widgets atomically.

    DELETE /api/v1/dashboards/1 -> 204 (no content)

    Uses SQLAlchemy cascade (Page.cards relationship with cascade="all, delete-orphan")
    to atomically delete the page and all associated cards in a single operation.
    Wrapped in try/except with rollback for full transaction safety.
    """
    page = db.query(Page).filter(Page.id == dashboard_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # SQLAlchemy cascade on Page.cards (cascade="all, delete-orphan") handles
    # deleting all associated cards automatically. No manual card deletion needed.
    try:
        db.delete(page)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to delete dashboard and its widgets"
        )
