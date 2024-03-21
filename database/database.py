import sqlalchemy
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = sqlalchemy.orm.declarative_base()


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    upload_path = Column(String)
    gpx_path = Column(String)
    gpx_matched_path = Column(String)
    vehicle_type = Column(String)
    inserted_date = Column(String)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ItemCreate(BaseModel):
    name: str
    upload_path: str
    gpx_path: str
    gpx_matched_path: str
    vehicle_type: str
    inserted_date: str


class ItemResponse(BaseModel):
    id: int
    name: str
    upload_path: str
    gpx_path: str
    gpx_matched_path: str
    vehicle_type: str
    inserted_date: str

