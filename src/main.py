import os
import zipfile
import geopandas as gpd
import pandas as pd
import pyrosm
import r5py
import osmfile
import h3pandas as h3
from sys import argv


def main():
    # TODO argparse?
    gtfs_path = argv[1]
    gtfs_name = os.path.basename(gtfs_path)

    # TODO read in gtfs feed
    with zipfile.ZipFile(gtfs_path) as gtfs:
        with gtfs.open("stops.txt") as stops_file:
            stops_df = pd.read_table(stops_file, sep=",")

    stops_gdf = gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
        crs="EPSG:4326",
    )
    # TODO config file with save locations

    matching_file = osmfile.get_osm_data(geodata=stops_gdf, name=gtfs_name)
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)

    # hexgrids per county in dataframe
    counties = osmfile.extract_counties(osm_data)
    county_hexgrids = osmfile.counties_to_hexgrids(counties)

    # TODO find pois and create destination enum

    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )
    
    # TODO hexgrid centroids
    # TODO instantiate TravelTimeMatrixComputer object from r5py
    # TODO loop over counties with travel time matrix calculations
    # TODO output plots and data files


if __name__ == "__main__":
    main()
