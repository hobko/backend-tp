import os
import subprocess
from pathlib import Path

from scripts.csvTogeojsonTogpxA import csv_to_gpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from config_loggers.logConfig import setup_logger
from scripts.sendToMapMatching import send_post_request
from starlette.middleware.cors import CORSMiddleware
from services.exceptionMiddleware import ExceptionMiddleware

from starlette.responses import JSONResponse

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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
