import csv
import os

from geojson import Feature, FeatureCollection, Point
from pathlib import Path
import re
import geopandas as gpd
import gpxpy
import gpxpy.gpx
import json

from scripts.sendToMapMatching import send_post_request
from config_loggers.logConfig import setup_logger

logger = setup_logger()


def make_geojson_from_data(input_file_path, output_file_path):
    features = []

    with open(input_file_path, mode='r', newline='') as input_file:
        csv_reader = csv.reader(input_file)
        header = next(csv_reader)

        lat_column_index = 4
        lon_column_index = 5

        for row in csv_reader:
            lat_format = re.sub(r'.$', '', row[lat_column_index])
            lon_format = re.sub(r'.$', '', row[lon_column_index])
            lat = float(lat_format)
            lon = float(lon_format)

            point = Point((lon, lat))

            properties = {
                'date': row[2],
                'time': row[3],
                'speed': row[7]
            }
            feature = Feature(geometry=point, properties=properties)
            features.append(feature)

    feature_collection = FeatureCollection(features)

    with open(output_file_path, 'w') as output_file:
        output_file.write(str(feature_collection))


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
            lat, lon = coordinates[1], coordinates[0]  # GeoJSON uses [lon, lat] order
            segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        elif geometry_type == 'LineString':
            for point in coordinates:
                lat, lon = point[1], point[0]  # GeoJSON uses [lon, lat] order
                segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))
        elif geometry_type == 'MultiLineString':
            for line_string in coordinates:
                for point in line_string:
                    lat, lon = point[1], point[0]  # GeoJSON uses [lon, lat] order
                    segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    track.segments.append(segment)
    gpx.tracks.append(track)

    with open(output_gpx, 'w') as gpx_file:
        gpx_file.write(gpx.to_xml())


def remove_file_extension(filename):
    root, extension = os.path.splitext(filename)
    return root


def csv_to_gpx(input_file_name, vehicle_type):
    cur: Path = Path(__file__).parent.parent
    input_file_name_wo_extension = remove_file_extension(input_file_name)
    intermediate_file_name = input_file_name_wo_extension + ".geojson"
    input_csv_file = cur / "storage/uploads" / input_file_name
    intermediate_geojson_file = cur / "storage/geojson" / intermediate_file_name
    output_cleaned_geojson_file = cur / "storage/geojson-cleaned" / intermediate_file_name
    output_gpx_file = input_file_name_wo_extension + ".gpx"
    output_gpx = cur / "storage/gpx" / output_gpx_file

    try:
        # Step 1: Generate GeoJSON from CSV
        make_geojson_from_data(input_csv_file, intermediate_geojson_file)
        logger.info(
            f'CSV file "{input_csv_file}" has been converted to GeoJSON and saved as "{intermediate_file_name}".')

        # Step 2: Validate and clean the GeoJSON
        validate_and_clean_geojson(intermediate_geojson_file, output_cleaned_geojson_file)
        logger.info(
            f'GeoJSON file "{intermediate_geojson_file}" has been validated and cleaned, saved as "{output_cleaned_geojson_file}".')

        # Step 3: Transform Geojson to GPX
        geojson_to_gpx(output_cleaned_geojson_file, output_gpx)
        logger.info(
            f'GeoJSON file "{output_cleaned_geojson_file}" has been successfully transformed to GPX and saved as "{output_gpx_file}".')

        # Step 4: Get from graphhopper Matched gpx
        response_data = send_post_request(input_file_name_wo_extension, vehicle_type)
        logger.info(f'Matched GPX file has been stored as json succesfully')


    except Exception as e:
        # Log an error if any exception occurs during the process
        logger.error(f'Failed to convert CSV to GPX. Error: {str(e)}')
        # Optionally, raise the exception again to propagate it
        raise e
