import os
import zipfile
import geopandas as gpd
import pandas as pd
import r5py
import pyrosm
import h3pandas as h3
from sys import argv
from osmfile import get_osm_data, OSMFile


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

    matching_file = get_osm_data(geodata=stops_gdf, name=gtfs_name)
    #hexgrids and start locations per county in dataframe
    hexgrids = extract_county_hexgrids(matching_file)

    # TODO find pois and create destination enum

    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )

    # TODO instantiate TravelTimeMatrixComputer object from r5py
    # TODO loop over counties with travel time matrix calculations
    # TODO output plots and data files

def extract_county_hexgrids(matching_file: OSMFile) -> dict:
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)
    admin_boundaries = osm_data.get_boundaries()
    # TODO add admin_levels enum for different countries
    counties = admin_boundaries[admin_boundaries['admin_level'] == '6']

    hexgrid = counties.h3.polyfill_resample(10)
    hexgrid.rename(columns={"id":"county_id", "h3_polyfill":"id"}, inplace=True)
    start_loc_per_county = {}
    for name in counties['name']:
        county_hexgrid = hexgrid.loc[hexgrid['name'] == name]
        county_hexgrid_centroids = county_hexgrid.copy()
        county_hexgrid_centroids['geometry'] = county_hexgrid.centroid
        start_loc_per_county[str(name)] = county_hexgrid_centroids
    return start_loc_per_county
   


if __name__ == "__main__":
    main()
