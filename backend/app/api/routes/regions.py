from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Region
from app.schemas import RegionOut

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)) -> list[Region]:
    """Return configured monitoring regions."""

    return db.query(Region).order_by(Region.country.asc()).all()
