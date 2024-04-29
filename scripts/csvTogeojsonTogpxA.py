import csv
import os
import geopandas as gpd
import gpxpy
import gpxpy.gpx
import json
from datetime import datetime
from geojson import Feature, FeatureCollection, Point
from pathlib import Path
from database.database_operations import create_item
from database.database import ItemCreate
from scripts.sendToMapMatching import send_post_request
from config_loggers.logConfig import setup_logger

logger = setup_logger()

class CSVModel:
    def __init__(self, header):
        self.header = header

    def is_type_1(self):
        required_columns = {'datetime', 'lat', 'lon', 'speed'}
        return required_columns.issubset(self.header)

    def is_type_2(self):
        required_columns = {'DATE', 'TIME', 'LATITUDE N/S', 'LONGITUDE E/W', 'SPEED'}
        return required_columns.issubset(self.header)

def identify_csv_type(header):
    model = CSVModel(header)
    if model.is_type_1():
        return 'type_1'
    elif model.is_type_2():
        return 'type_2'
    else:
        return 'unknown'

def process_csv(input_file_path, output_file_path):
    with open(input_file_path, mode='r', newline='') as input_file:
        csv_reader = csv.reader(input_file)
        header = next(csv_reader)

        csv_type = identify_csv_type(header)
        if csv_type in {'type_1', 'type_2'}:
            make_geojson_from_data(input_file_path, output_file_path, header, csv_type)
        else:
            # Handle unknown CSV type
            print("Wrong CSV file format need header with <...>")
            pass

def make_geojson_from_data(input_file_path, output_file_path, header, file_type):
    features = []

    with open(input_file_path, mode='r', newline='') as input_file:
        csv_reader = csv.reader(input_file)
        next(csv_reader)

        # Type indexes processing for both types
        lat_column_index = header.index('lat') if 'lat' in header else header.index('LATITUDE N/S')
        lon_column_index = header.index('lon') if 'lon' in header else header.index('LONGITUDE E/W')
        speed_column_index = header.index('speed') if 'speed' in header else header.index('SPEED')

        for row in csv_reader:
            lat_str = row[lat_column_index]
            lon_str = row[lon_column_index]
            speed = float(row[speed_column_index])

            # Parse latitude and longitude from strings
            lat_dir = lat_str[-1]
            lon_dir = lon_str[-1]
            lat_str = lat_str[:-1] if lat_dir in ['N', 'S'] else lat_str
            lon_str = lon_str[:-1] if lon_dir in ['E', 'W'] else lon_str
            lat = float(lat_str)
            lon = float(lon_str)

            # Ak je smer 'N' alebo 'E', nezmení sa znamienko
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon

            point = Point((lon, lat))

            if file_type == 'type_1':
                # Prevziať dátum a čas zo stĺpca 'datetime' a rozdeliť ich na dátum a čas
                date_time = row[header.index('datetime')]
                date_parts = date_time.split()[0].split('-')  # Rozdelenie dátumu na časti
                time_parts = date_time.split()[1].split(':')  # Rozdelenie času na časti

                # Vytvorenie reťazca pre dátum v požadovanom formáte "YYMMDD"
                date = f"{date_parts[0][2:]}{date_parts[1]}{date_parts[2]}"

                # Vytvorenie reťazca pre čas v požadovanom formáte "HHMMSS"
                time = ''.join(time_parts)

                properties = {
                    'date': date,
                    'time': time,
                    'speed': speed
                }
            elif file_type == 'type_2':
                properties = {
                    'date': row[header.index('DATE')],
                    'time': row[header.index('TIME')],
                    'speed': speed
                }

            feature = Feature(geometry=point, properties=properties)
            features.append(feature)

    feature_collection = FeatureCollection(features)

    with open(output_file_path, 'w') as output_file:
        output_file.write(str(feature_collection))

def get_header(csv_file):
    with open(csv_file, "r") as file:
        file = csv.reader(file, delimiter=',', quotechar='"')
        header = next(file, None)
        return header

def validate_and_clean_geojson(input_file, output_file):
    gdf = gpd.read_file(input_file)

    # Filter out invalid geometries
    gdf = gdf[gdf.geometry.is_valid]

    # Filter out rows with missing or invalid properties
    valid_properties = ["date", "time", "speed"]
    gdf = gdf[gdf.apply(lambda row: all(prop in row for prop in valid_properties), axis=1)]

    # Save the cleaned data to a new GeoJSON file
    if output_file:
        gdf.to_file(output_file, driver='GeoJSON')

    return gdf

'''
Tu som upravoval funkciu, lebo to robilo zaporne hodnoty v gpx a preto to nechcelo convertovat na <nazov>_matched.gpx.
Cize boli pridane iba ify na konverziu zapornych hodnot suradnic na kladne.
'''
def geojson_to_gpx(input_geojson, output_gpx):
    with open(input_geojson, 'r') as geojson_file:
        data = json.load(geojson_file)

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    segment = gpxpy.gpx.GPXTrackSegment()

    for feature in data['features']:
        geometry_type = feature['geometry']['type']
        coordinates = feature['geometry']['coordinates']

        if geometry_type == 'Point':
            lon, lat = coordinates  # GeoJSON uses [lon, lat] order

            segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        elif geometry_type == 'LineString':
            for point in coordinates:
                lon, lat = point  # GeoJSON uses [lon, lat] order

                segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        elif geometry_type == 'MultiLineString':
            for line_string in coordinates:
                for point in line_string:
                    lon, lat = point  # GeoJSON uses [lon, lat] order

                    segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    track.segments.append(segment)
    gpx.tracks.append(track)

    with open(output_gpx, 'w') as gpx_file:
        gpx_file.write(gpx.to_xml())


def remove_file_extension(filename):
    root, extension = os.path.splitext(filename)
    return root


def csv_to_gpx(input_file_name, vehicle_type, db):
    cur: Path = Path(__file__).parent.parent
    input_file_name_wo_extension = remove_file_extension(input_file_name)
    intermediate_file_name = input_file_name_wo_extension + ".geojson"
    input_csv_file = cur / "storage/uploads" / input_file_name
    intermediate_geojson_file = cur / "storage/geojson" / intermediate_file_name
    output_cleaned_geojson_file = cur / "storage/geojson-cleaned" / intermediate_file_name
    output_gpx_file = input_file_name_wo_extension + ".gpx"
    output_gpx = cur / "storage/gpx" / output_gpx_file
    matched_gpx_filename = cur / 'storage/gpx-matched' / f'{input_file_name_wo_extension}_matched.gpx'

    header = get_header(input_csv_file)
    if header:
        process_csv(input_csv_file, intermediate_geojson_file)
    else:
        print("No header found in the CSV file.")
        return  # terminate function if header not found

    try:
        # Step 2: Validate and clean the GeoJSON
        validate_and_clean_geojson(intermediate_geojson_file, output_cleaned_geojson_file)
        logger.info(
            f'GeoJSON file "{intermediate_geojson_file}" has been validated and cleaned, saved as "{output_cleaned_geojson_file}".')

        # Step 3: Transform Geojson to GPX
        geojson_to_gpx(output_cleaned_geojson_file, output_gpx)
        logger.info(
            f'GeoJSON file "{output_cleaned_geojson_file}" has been successfully transformed to GPX and saved as "{output_gpx_file}".')

        # Step 4: Get from graphhopper Matched gpx
        send_post_request(input_file_name_wo_extension, vehicle_type)
        logger.info(f'Matched GPX file has been stored as json succesfully')

        current_datetime = datetime.now()
        new_item = ItemCreate(
            name=input_file_name,
            upload_path=str(input_csv_file),
            gpx_path=str(output_gpx),
            gpx_matched_path=str(matched_gpx_filename),  # You may adjust this accordingly
            vehicle_type=str(vehicle_type),
            inserted_date=str(current_datetime)  # You may adjust this accordingly
        )
        # Add the item to the database
        create_item(new_item, db=db)  # Assuming you have a function to create items

    except Exception as e:
        # Log an error if any exception occurs during the process
        logger.error(f'Failed to convert CSV to GPX. Error: {str(e)}')
        # Optionally, raise the exception again to propagate it
        raise e