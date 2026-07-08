from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import PaperResult
from app.services.paper_data import PAPER_RESULTS

router = APIRouter(prefix="/paper-results", tags=["paper-results"])


@router.get("")
def get_paper_results(db: Session = Depends(get_db)) -> dict:
    """Return paper/validation figures with explicit real-vs-simulated status fields."""

    rows = db.query(PaperResult).all()
    if not rows:
        return PAPER_RESULTS
    return {row.key: row.payload for row in rows}
