from pathlib import Path

import requests


def send_post_request():
    cur: Path = Path(__file__).parent.parent
    url = "http://localhost:8989/match?profile=car&gps_accuracy=20&type=json"
    # Replace 'hesoyam.gpx' with the actual path to your GPX file
    gpx_file_path = cur / 'storage/gpx/hesoyam.gpx'

    with open(gpx_file_path, 'r') as gpx_file:
        # Read the GPX file content as a string
        gpx_str = gpx_file.read()

    headers = {'Content-Type': 'application/xml'}  # Adjust the content type if needed
    params = {}  # Add any additional parameters if needed

    response = requests.post(url, headers=headers, data=gpx_str, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON content
        json_content = response.json()
        # You can now work with the JSON content as needed
        print(json_content)
        return json_content
    else:
        # Print an error message if the request was not successful
        print(f"Error: {response.status_code}")
        return None
