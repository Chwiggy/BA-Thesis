import os
import zipfile
import geopandas as gpd
import pandas as pd
import shapely
import pyrosm
import r5py
import h3pandas as h3
import destination
import centrality
import osmfile
from sys import argv
from output import to_png


def main():
    # TODO argparse?
    gtfs_path = argv[1]
    gtfs_name, _ = os.path.basename(gtfs_path).split(sep=".")

    # TODO read in gtfs feed
    with zipfile.ZipFile(gtfs_path) as gtfs:
        with gtfs.open("stops.txt") as stops_file:
            stops_df = pd.read_table(stops_file, sep=",")

    stops_gdf = gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
        crs="EPSG:4326",
    )
    # TODO config file with save locations and destination types

    matching_file = osmfile.get_osm_data(geodata=stops_gdf, name=gtfs_name)
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)

    # hexgrids per county in dataframe
    counties = osmfile.extract_counties(osm_data)
    county_hexgrids = osmfile.counties_to_hexgrids(counties)

    desired_destination = destination.Destination.SCHOOLS
    destinations = destination.find_destinations(osm_data, county_hexgrids, desired_destination)

    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )

    for county, hexgrid in county_hexgrids.items():

        clipped_destinations = destination.clip_destinations(destinations, hexgrid)

        results = centrality.closeness_centrality(
            transport_network, hexgrid, clipped_destinations
        )

        to_png(gtfs_name, county, results)


if __name__ == "__main__":
    main()
