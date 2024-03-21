from typing import List

from database.database import ItemCreate, Item
from sqlalchemy.orm import Session


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
