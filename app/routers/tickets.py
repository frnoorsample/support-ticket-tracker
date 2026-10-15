from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.categorise import categorise
from app.database import get_db
from app.schemas import Priority, Status, StatusUpdate, TicketCreate, TicketOut, TicketUpdate
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_ticket_or_404(db, ticket_id: int, user: dict) -> dict:
    row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None or (user["role"] != "admin" and row["created_by"] != user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return dict(row)


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, db=Depends(get_db), user: dict = Depends(get_current_user)):
    cursor = db.execute(
        "INSERT INTO tickets (title, description, category, priority, created_by) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            ticket.title,
            ticket.description,
            categorise(ticket.title, ticket.description),
            ticket.priority,
            user["id"],
        ),
    )
    db.commit()
    return get_ticket_or_404(db, cursor.lastrowid, user)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_filter: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    category: str | None = None,
    db=Depends(get_db),
    user: dict = Depends(get_current_user),
):
    conditions, params = [], []
    if user["role"] != "admin":
        conditions.append("created_by = ?")
        params.append(user["id"])
    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)
    if priority:
        conditions.append("priority = ?")
        params.append(priority)
    if category:
        conditions.append("category = ?")
        params.append(category)

    query = "SELECT * FROM tickets"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"

    return [dict(row) for row in db.execute(query, params).fetchall()]


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db=Depends(get_db), user: dict = Depends(get_current_user)):
    return get_ticket_or_404(db, ticket_id, user)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    changes: TicketUpdate,
    db=Depends(get_db),
    user: dict = Depends(get_current_user),
):
    ticket = get_ticket_or_404(db, ticket_id, user)
    if ticket["status"] == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Closed tickets cannot be edited")

    updates = changes.model_dump(exclude_none=True)
    if not updates:
        return ticket

    title = updates.get("title", ticket["title"])
    description = updates.get("description", ticket["description"])
    db.execute(
        "UPDATE tickets SET title = ?, description = ?, priority = ?, category = ?, "
        "updated_at = datetime('now') WHERE id = ?",
        (
            title,
            description,
            updates.get("priority", ticket["priority"]),
            categorise(title, description),
            ticket_id,
        ),
    )
    db.commit()
    return get_ticket_or_404(db, ticket_id, user)


@router.patch("/{ticket_id}/status", response_model=TicketOut)
def update_status(
    ticket_id: int,
    change: StatusUpdate,
    db=Depends(get_db),
    admin: dict = Depends(require_admin),
):
    get_ticket_or_404(db, ticket_id, admin)
    db.execute(
        "UPDATE tickets SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (change.status, ticket_id),
    )
    db.commit()
    return get_ticket_or_404(db, ticket_id, admin)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db=Depends(get_db), admin: dict = Depends(require_admin)):
    get_ticket_or_404(db, ticket_id, admin)
    db.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)