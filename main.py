import time
from io import BytesIO
from typing import List
import requests
from dotenv import load_dotenv
from starlette import status
from starlette.responses import StreamingResponse

from database.database import SessionLocal, ItemResponse, ItemCreate, Item
from database.database_operations import *
from models.modelsResponse import *
from scripts.csvTogeojsonTogpxA import csv_to_gpx
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from config_loggers.logConfig import setup_logger
from starlette.middleware.cors import CORSMiddleware
from services.exceptionMiddleware import ExceptionMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os
from zipfile import ZipFile
import tempfile

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

from swagger.swag_metadata import tags_metadata

app = FastAPI(openapi_tags=tags_metadata)

logger = setup_logger()

cur: Path = Path(__file__).parent
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ExceptionMiddleware)  # Add the custom exception middleware

load_dotenv()
GRAPHHOPPER_URL = os.environ.get('GRAPHHOPPER_URL')


# *************************************************************************
#               DATABASE VECI
# *************************************************************************

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/testing/items/", tags=["Test-DB"], response_model=ItemResponse)
async def ep_create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = create_item(item, db)
    return db_item


# API endpoint to read an item by ID
@app.get("/testing/id/{item_id}", tags=["Test-DB"], response_model=ItemResponse)
async def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.get("/testing/name/{filename}", tags=["Test-DB"], response_model=ItemResponse)
async def read_item_by_name(filename: str, db: Session = Depends(get_db)):
    db_item = get_item_by_filename(db, filename)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.get("/testing/all", tags=["Test-DB"], response_model=List[ItemResponse])
async def dump_db(db: Session = Depends(get_db)):
    db_items = db.query(Item).all()  # Retrieve all items from the database
    if not db_items:  # If there are no items in the database
        raise HTTPException(status_code=404, detail="No items found in the database")
    return db_items


# *************************************************************************
# *************************************************************************
# *************************************************************************


@app.get('/api/autoconvert', tags=["API"])
async def covert_uploads(db: Session = Depends(get_db)):
    files_in_db = get_all_filenames(db)

    upload_dir = cur / "storage/uploads"

    # Get a list of CSV files in the upload directory
    csv_files = [file for file in upload_dir.glob("*.[cC][sS][vV]") if file.is_file()]
    print(csv_files)
    for csv_file in csv_files:
        if csv_file.name not in files_in_db:
            csv_to_gpx(csv_file.name, "foot", db)
            logger.info(f'File converted successfullly: {csv_file.name}')

    return {"message": "CSV files auto-converted to GPX"}


@app.get("/api/download/{filename}", tags=["API"])
async def download_gpx_as_zip(filename: str, db: Session = Depends(get_db)):
    # Retrieve the item from the database based on the filename
    filename = "chodza4.CSV"
    item = get_item_by_filename(db, filename)
    if not item:
        raise HTTPException(status_code=404, detail=f"No files matching '{filename}' found for download")

    # Construct paths for the GPX files
    gpx_file_path = Path(item.gpx_path)
    gpx_matched_file_path = Path(item.gpx_matched_path)
    filename_without_extension = os.path.splitext(filename)[0]

    # Check if the GPX files exist
    if not gpx_file_path.exists() or not gpx_matched_file_path.exists():
        raise HTTPException(status_code=404, detail="One or more files not found")

    try:
        # Create an in-memory buffer for the ZIP file
        zip_buffer = BytesIO()

        # Create a new ZIP file in memory
        with ZipFile(zip_buffer, "w") as zipf:
            # Add the GPX files to the ZIP archive
            zipf.write(gpx_file_path, os.path.basename(gpx_file_path))
            zipf.write(gpx_matched_file_path, f"{filename_without_extension}_matched.gpx")

        # Move the buffer position to the beginning
        zip_buffer.seek(0)

        # Send the ZIP file as the response
        return StreamingResponse(iter([zip_buffer.getvalue()]), media_type="application/zip", headers={
            "Content-Disposition": f"attachment; filename={filename_without_extension}.zip"})
    except Exception as e:
        logger.error(f"Error occurred while creating or sending ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get('/api/getgpx/{filename}', tags=["API"])
async def get_gpx(filename: str, db: Session = Depends(get_db)):
    item = get_item_by_filename(db, filename)
    if not item:
        raise HTTPException(status_code=404, detail=f"No files matching '{filename}' found for deletion")

    try:
        gpx_file_path = Path(item.gpx_path)
        logger.info(f'File was find and returned getgpx: {filename}', extra={'file_identifier': filename})
        return FileResponse(gpx_file_path, media_type='application/gpx+xml', filename=filename)
    except FileNotFoundError:
        logger.error(f'File not found: {filename}', extra={'file_identifier': filename})
        raise HTTPException(status_code=404, detail='File not found')


@app.get('/api/getgpx/matched/{filename}', tags=["API"])
async def get_gpx(filename: str, db: Session = Depends(get_db)):
    item = get_item_by_filename(db, filename)
    if not item:
        raise HTTPException(status_code=404, detail=f"No files matching '{filename}' found for deletion")

    try:
        gpx_file_path = Path(item.gpx_matched_path)
        logger.info(f'File was find and returned: {filename}', extra={'file_identifier': filename})
        return FileResponse(gpx_file_path, media_type='application/gpx+xml', filename=filename)
    except FileNotFoundError:
        logger.error(f'File not found: {filename}', extra={'file_identifier': filename})
        raise HTTPException(status_code=404, detail='File not found')


@app.get("/api/getfiles", tags=["API"], response_model=List[FileData])
async def get_files(db: Session = Depends(get_db)):
    try:
        files_data = get_all_file_data(db)
        logger.info("Files data were successfully retrieved from the database")
        return files_data
    except Exception as e:
        logger.critical(f"Failed to retrieve files data from the database. Error: {str(e)}")
        return {"error": f"Failed to retrieve files data from the database. Error: {str(e)}"}

@app.post("/api/upload", tags=["API"])
async def upload_file_with_vehicle(file: UploadFile = File(...), vehicle_type: str = Form(...),
                                   db: Session = Depends(get_db)):
    # Path to the uploaded file
    uploaded_file_path = cur / "storage/uploads" / file.filename
    with open(uploaded_file_path, 'wb') as uploaded_file:
        uploaded_file.write(file.file.read())

    # Process the file and vehicle type as needed
    csv_to_gpx(file.filename, vehicle_type, db)
    logger.info(f'File uploaded successfully: {file.filename}, Vehicle Type: {vehicle_type}')

    return {"message": "File uploaded and processed successfully", "vehicle_type": vehicle_type,
            "file": uploaded_file_path}


@app.get("/api/hello", tags=["health"], response_model=HelloResponse)
def hello_world():
    return {"message": "System is up"}


@app.get("/api/graphhopper/status", tags=["health"], response_model=GraphResponse)
def graphhopper_check():
    try:
        url = f"{GRAPHHOPPER_URL}/health"
        response = requests.get(url)
        if response.status_code == 200:
            return {"message": "OK"}
        else:
            return {"message": "Error"}
    except requests.RequestException as e:
        return {"message": f"Error: {e}"}


@app.delete("/api/delete/storage/{file_name}", tags=["API"])
def delete_files_from_storage(file_name: str, db: Session = Depends(get_db)):
    item = get_item_by_filename(db, file_name)
    if not item:
        raise HTTPException(status_code=404, detail=f"No files matching '{file_name}' found for deletion")

    paths_to_delete = [item.upload_path, item.gpx_path, item.gpx_matched_path]
    deleted_files = []
    for file_path in paths_to_delete:
        if file_path and os.path.exists(file_path):
            path = Path(file_path)
            path.unlink()
            deleted_files.append(file_path)

    if not delete_item_by_filename(db, file_name):
        raise HTTPException(status_code=500, detail=f"Failed to delete files from the database")

    return {"message": f"Files {', '.join(deleted_files)} and corresponding database row deleted successfully"}


@app.delete("/api/delete/uploads/storage/", tags=["API"])
def delete_files_from_storage(selected_files: List[str]):
    storage_path = cur / "storage/uploads"
    deleted_files = []
    for file_name in selected_files:
        file_path = storage_path / file_name
        if file_path.exists():
            file_path.unlink()
            deleted_files.append(file_name)

    if not deleted_files:
        raise HTTPException(status_code=404, detail="Files not found")
    else:
        return {"message": f"Files {', '.join(deleted_files)} deleted successfully"}


@app.post("/api/convert/uploads/storage/", tags=["API"])
def convert_of_upload_folder(selected_files: List[str], db: Session = Depends(get_db)):
    storage_path = cur / "storage/uploads"
    convert_uploads = []
    for file_name in selected_files:
        file_path = storage_path / file_name
        if file_path.exists():
            csv_to_gpx(file_name, "foot", db)
            convert_uploads.append(file_name)

    if not convert_uploads:
        raise HTTPException(status_code=404, detail="Files not found")
    else:
        return {"message": f"Files {', '.join(convert_uploads)} converted successfully"}


@app.get("/api/uploads/getfiles", tags=["API"])
async def get_uploads_for_table(db: Session = Depends(get_db)):
    files_in_db = get_all_filenames(db)
    upload_dir = cur / "storage/uploads"
    missing_gpx_files = []
    csv_files = [file for file in upload_dir.glob("*.[cC][sS][vV]") if file.is_file()]
    logger.info(files_in_db)
    logger.info(csv_files)

    for csv_file in csv_files:
        if csv_file.name not in files_in_db:
            missing_gpx_files.append(csv_file.name)

    if missing_gpx_files:
        return {"message": "CSV files auto-converted to GPX", "files": missing_gpx_files}
    else:
        return {"files": missing_gpx_files}


@app.get("/", tags=["default"])
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}", tags=["default"])
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
