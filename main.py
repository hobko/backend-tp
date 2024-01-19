import os
import subprocess
from pathlib import Path

from scripts.csvTogeojsonTogpxA import csv_to_gpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

app = FastAPI()

origins = ["http://localhost:4200"]
cur: Path = Path(__file__).parent
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/api/getgpx/{filename}')
async def get_gpx(filename: str):
    try:
        # Replace this with the path to your GPX files directory
        gpx_file_path = cur / "storage/gpx" / filename

        # Send the GPX file as a response
        print("Ahoj hobo")
        return FileResponse(gpx_file_path, media_type='application/gpx+xml', filename=filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='File not found')

@app.get("/api/getfiles")
async def get_files():
    folder_path = cur / "storage/gpx"  # Replace with the actual path to your GPX folder

    try:
        # List all files in the folder
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return {"files": files}
    except Exception as e:
        return {"error": f"Failed to retrieve files. Error: {str(e)}"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Path to the uploaded file
    uploaded_file_path = cur / "storage/uploads" / file.filename
    with open(uploaded_file_path, 'wb') as uploaded_file:
        uploaded_file.write(file.file.read())
    csv_to_gpx(file.filename)
    return {"message": "File uploaded and processed successfully"}


@app.get("/api/hello")
def hello_world():
    return {"message": "Hello, Worssssld!"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
