from datetime import datetime
from typing import List

from database.database import ItemCreate, Item
from sqlalchemy.orm import Session

from pydantic import BaseModel
from typing import List


class FileData(BaseModel):
    filename: str
    vehicle_type: str
    inserted_date: datetime


def create_item(item_data: ItemCreate, db: Session):
    db_item = Item(**item_data.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item_by_filename(db: Session, filename: str) -> Item:
    return db.query(Item).filter(Item.name == filename).first()


def get_all_filenames(db: Session) -> List[str]:
    items = db.query(Item).all()
    filenames = [item.name for item in items]
    return filenames


def delete_item_by_filename(db: Session, filename: str):
    try:
        db.query(Item).filter(Item.name == filename).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def get_all_file_data(db: Session) -> List[FileData]:
    items = db.query(Item).all()
    files_data = []
    for item in items:
        file_data = FileData(
            filename=item.name,
            vehicle_type=item.vehicle_type,
            inserted_date=item.inserted_date
        )
        files_data.append(file_data)
    return files_data
