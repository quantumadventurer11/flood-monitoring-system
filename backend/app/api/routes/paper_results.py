from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import PaperResult
from app.services.paper_data import PAPER_RESULTS

router = APIRouter(prefix="/paper-results", tags=["paper-results"])


@router.get("")
def get_paper_results(db: Session = Depends(get_db)) -> dict:
    """Return seeded methodology figures, tables, metrics, and notes from the paper."""

    rows = db.query(PaperResult).all()
    if not rows:
        return PAPER_RESULTS
    return {row.key: row.payload for row in rows}
