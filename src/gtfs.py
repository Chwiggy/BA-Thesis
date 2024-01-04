import datetime
import os
import geopandas as gpd
import pandas as pd


import zipfile

import destination

def crop_gtfs(gtfs: str, place: gpd.GeoDataFrame) -> str:
    raise NotImplementedError
    #TODO crop gtfs to file 

def dataframe_from_stops(gtfs_path: str) -> gpd.GeoDataFrame:
    with zipfile.ZipFile(gtfs_path) as gtfs:
        with gtfs.open("stops.txt") as stops_file:
            stops_df = pd.read_table(stops_file, sep=",")

    stops_gdf = gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
        crs="EPSG:4326",
    )

    return stops_gdf


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


def name_from_path(gtfs_path):
    gtfs_name, _ = os.path.basename(gtfs_path).split(sep=".")
    return gtfs_name