import os
import subprocess
from pathlib import Path

import requests
from dotenv import load_dotenv

from scripts.csvTogeojsonTogpxA import csv_to_gpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from config_loggers.logConfig import setup_logger
from scripts.sendToMapMatching import send_post_request
from starlette.middleware.cors import CORSMiddleware
from services.exceptionMiddleware import ExceptionMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from zipfile import ZipFile
from pathlib import Path
import os
from zipfile import ZipFile
from starlette.responses import JSONResponse
import tempfile

app = FastAPI()
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


@app.get("/api/download/{filename}")
async def download_gpx_as_zip(filename: str):
    gpx_file_path = cur / "storage/gpx" / filename
    filename_without_extension = os.path.splitext(filename)[0]
    gpx_matched = filename_without_extension + "_matched.gpx"
    gpx_matched_file_path = cur / "storage/gpx-matched" / gpx_matched

    # Check if files exist
    if not gpx_file_path.exists() or not gpx_matched_file_path.exists():
        raise HTTPException(status_code=404, detail="One or more files not found")

    logger.info(f"Adding {gpx_file_path} to ZIP")
    logger.info(f"Adding {gpx_matched_file_path} to ZIP")
    try:
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(delete=False) as temp_zip_file:
            temp_zip_path = Path(temp_zip_file.name)
            with ZipFile(temp_zip_path, "w") as zipf:
                # Add the first file with the specified filename
                zipf.write(gpx_file_path, os.path.basename(gpx_file_path))

                # Add the second file with a unique name
                zipf.write(gpx_matched_file_path, f"{filename_without_extension}_matched.gpx")

        # Send the zip file as the response
        return FileResponse(temp_zip_path, media_type="application/zip")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/getgpx/{filename}')
async def get_gpx(filename: str):
    try:
        gpx_file_path = cur / "storage/gpx" / filename
        print(gpx_file_path)
        logger.info(f'File was find and returned: {filename}', extra={'file_identifier': filename})
        return FileResponse(gpx_file_path, media_type='application/gpx+xml', filename=filename)
    except FileNotFoundError:
        logger.error(f'File not found: {filename}', extra={'file_identifier': filename})
        raise HTTPException(status_code=404, detail='File not found')


@app.get('/api/getgpx/matched/{filename}')
async def get_gpx(filename: str):
    try:
        gpx_file_path = cur / "storage/gpx-matched" / filename
        logger.info(f'File was find and returned: {filename}', extra={'file_identifier': filename})
        return FileResponse(gpx_file_path, media_type='application/gpx+xml', filename=filename)
    except FileNotFoundError:
        logger.error(f'File not found: {filename}', extra={'file_identifier': filename})
        raise HTTPException(status_code=404, detail='File not found')


@app.get("/api/getfiles")
async def get_files():
    folder_path = cur / "storage/gpx"  # Replace with the actual path to your GPX folder
    try:
        # List all files in the folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        logger.info("Files where succesfully send to site")
        return {"files": files}
    except Exception as e:
        logger.critical(f"Failed to retrieve files. Error: {str(e)}")
        return {"error": f"Failed to retrieve files. Error: {str(e)}"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Path to the uploaded file
    uploaded_file_path = cur / "storage/uploads" / file.filename
    with open(uploaded_file_path, 'wb') as uploaded_file:
        uploaded_file.write(file.file.read())
    csv_to_gpx(file.filename)
    logger.info(f'File uploaded succesfully: {file.filename}')
    return {"message": "File uploaded and processed successfully"}


@app.get("/api/hello")
def hello_world():
    return {"message": "System is up"}


@app.get("/api/graphhopper/status")
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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
