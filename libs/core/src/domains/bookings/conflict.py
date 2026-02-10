from sqlalchemy import text
from typing import Any

def has_conflict(db: Any, master_id: Any, start: Any, end: Any) -> bool:
    """
    Checks for overlapping bookings for a specific master.
    Uses PostgreSQL tstzrange and the overlapping operator (&&).
    """
    query = text("""
        SELECT 1 FROM booking
        WHERE master_id = :mid
        AND tstzrange(start_time, end_time) && tstzrange(:start, :end)
        AND status NOT IN ('canceled')
    """)
    result = db.execute(query, {"mid": master_id, "start": start, "end": end}).first()
    return result is not None
