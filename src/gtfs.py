import datetime
import os
import geopandas as gpd
import pandas as pd
import zipfile
import destination
from pathlib import Path


class GTFS:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if self.path.is_dir:
            self.name = self.path.name
            self.archived = False
        elif self.path.is_file:
            self.name, _ = self.path.name.split(sep=".")
            self.archived = True

    def crop_gtfs(self, place: gpd.GeoDataFrame, inplace: bool = False):
        raise NotImplementedError
        # TODO crop gtfs to file

    def dataframe_from_stops(self) -> gpd.GeoDataFrame:
        """
        Returns a gpd.GeoDataFrame with all stop locations in ESPG:4326
        """
        if self.archived:
            with zipfile.ZipFile(self.path) as gtfs:
                with gtfs.open("stops.txt") as stops_file:
                    stops_df = pd.read_table(stops_file, sep=",")
        elif not self.archived:
            with open(Path(self.path, "stops.txt")) as stops_file:
                stops_df = pd.read_table(stops_file, sep=",")

        stops_gdf = gpd.GeoDataFrame(
            stops_df,
            geometry=gpd.points_from_xy(stops_df.stop_lon, stops_df.stop_lat),
            crs="EPSG:4326",
        )

        return stops_gdf


def departure_time(desired_destination, transport_network):
    # TODO how to make this work for more destinations and types
    start_date = transport_network.transit_layer.start_date
    end_date = transport_network.transit_layer.end_date
    delta = (end_date - start_date) / 2
    date = start_date + delta
    if desired_destination == destination.DestinationEnum.SCHOOLS:
        if date.weekday in (5, 6):
            date = date - datetime.timedelta(days=2)
        date = date.replace(hour=6, minute=30, second=0, microsecond=0)
    elif desired_destination == destination.DestinationEnum.SELF:
        date = date.replace(hour=8, minute=0, second=0, microsecond=0)

    return date
