import os
import zipfile
import datetime
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
    # TODO config file with save locations and destination types
    # TODO argparse?
    gtfs_path = argv[1]
    gtfs_name, _ = os.path.basename(gtfs_path).split(sep=".")

    stops_gdf = stops_from_gtfs(gtfs_path)

    matching_file = osmfile.get_osm_data(geodata=stops_gdf, name=gtfs_name)
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)

    # hexgrids per county in dataframe
    counties = osmfile.extract_counties(osm_data)
    county_hexgrids = osmfile.counties_to_hexgrids(counties)

    desired_destination = destination.Destination.SCHOOLS
    destinations = destination.find_destinations(osm_data=osm_data, desired_destination=desired_destination, county_hexgrids=county_hexgrids)

    # TODO why on earth are you quietly terminating my script?
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )

    departure = departure_time(desired_destination, transport_network)

    for county, hexgrid in county_hexgrids.items():

        clipped_destinations = destination.clip_destinations(destinations, hexgrid)

        results = centrality.closeness_centrality(
            transport_network=transport_network,
            hexgrid=hexgrid,
            destinations=clipped_destinations,
            departure= departure
        )

        to_png(gtfs_name, county, results)

def departure_time(desired_destination, transport_network):
    start_date = transport_network.transit_layer.start_date
    end_date = transport_network.transit_layer.end_date
    delta = (end_date - start_date) / 2
    date = start_date + delta
    if desired_destination == destination.Destination.SCHOOLS:
        if date.weekday in (5, 6):
            date = date - datetime.timedelta(days=2)
        date = date.replace(hour=6, minute=30, second=0, microsecond=0)
    elif desired_destination == destination.Destination.SELF:
        date = date.replace(hour=8, minute=0, second=0, microsecond=0)
    
    return date

def stops_from_gtfs(gtfs_path: str) -> gpd.GeoDataFrame:
    with zipfile.ZipFile(gtfs_path) as gtfs:
        with gtfs.open("stops.txt") as stops_file:
            stops_df = pd.read_table(stops_file, sep=",")

    stops_gdf = gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
        crs="EPSG:4326",
    )
    
    return stops_gdf


if __name__ == "__main__":
    main()
