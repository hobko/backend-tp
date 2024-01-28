import json
from xml.dom.minidom import Document
from pathlib import Path
from polyline import polyline
import requests


def send_post_request(filename):
    cur: Path = Path(__file__).parent.parent
    url = "http://graphhopper:8989/match?profile=car&gps_accuracy=20&type=json"
    gpx_file_path = cur / 'storage/gpx' / f'{filename}.gpx'

    with open(gpx_file_path, 'r') as gpx_file:
        gpx_str = gpx_file.read()

    headers = {'Content-Type': 'application/xml'}
    params = {}

    response = requests.post(url, headers=headers, data=gpx_str, params=params)

    if response.status_code == 200:
        json_content = response.json()

        # Call convert_json_to_gpx function with the obtained JSON content
        gpx_xml = convert_json_to_gpx(json_content)

        # Save the matched GPX data to a file in the "storage/jsons" directory
        matched_gpx_filename = cur / 'storage/gpx-matched' / f'{filename}_matched.gpx'
        with open(matched_gpx_filename, 'w') as matched_gpx_file:
            matched_gpx_file.write(gpx_xml)

        return json_content
    else:
        print(f"Error: {response.status_code}")
        return None


def convert_json_to_gpx(json_content):
    doc = Document()
    # Vytvorenie koreňového elementu <gpx>
    gpx = doc.createElement('gpx')
    gpx.setAttribute('xmlns', 'http://www.topografix.com/GPX/1/1')
    gpx.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    gpx.setAttribute('xsi:schemaLocation',
                     'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    gpx.setAttribute('version', '1.1')
    gpx.setAttribute('creator', 'gpx.py -- https://github.com/tkrajina/gpxpy')
    # Vytvorenie elementu <trk>
    trk = doc.createElement('trk')
    # Vytvorenie elementu <trkseg>
    trkseg = doc.createElement('trkseg')
    points = json_content['paths'][0]['points']
    decoded_points = polyline.decode(points)

    for lat, lon in decoded_points:
        # Vytvorenie elementu <trkpt>
        trkpt = doc.createElement('trkpt')
        trkpt.setAttribute('lat', '{:.6f}'.format(lat))
        trkpt.setAttribute('lon', '{:.6f}'.format(lon))

        # Pridanie prázdneho textového uzlu do <trkpt>
        trkpt.appendChild(doc.createTextNode(''))

        # Pridanie <trkpt> do <trkseg>
        trkseg.appendChild(trkpt)

    # Pridanie <trkseg> do <trk>
    trk.appendChild(trkseg)

    # Pridanie <trk> do <gpx>
    gpx.appendChild(trk)

    # Pridanie <gpx> do dokumentu
    doc.appendChild(gpx)

    return doc.toprettyxml(indent='  ')



