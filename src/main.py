import os
import zipfile
import datetime
import geopandas as gpd
import pandas as pd
import shapely
import pyrosm
import r5py
import osmfile
import h3pandas as h3
from sys import argv
from enum import Enum, auto
from matplotlib import pyplot as plt


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
    # TODO config file with save locations

    matching_file = osmfile.get_osm_data(geodata=stops_gdf, name=gtfs_name)
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)

    # hexgrids per county in dataframe
    counties = osmfile.extract_counties(osm_data)
    county_hexgrids = osmfile.counties_to_hexgrids(counties)

    desired_destination = Destination.SCHOOLS
    if desired_destination == Destination.SELF:
        raise NotImplementedError
        # TODO add way to make it work on itself
    else:
        destinations = find_destinations(osm_data, Destination, desired_destination)

    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )

    for county, hexgrid in county_hexgrids.items():
        hexgrid_centroids = centroids(hexgrid)

        clipped_destinations = clip_destinations(destinations, hexgrid)

        travel_time_matrix_computer = r5py.TravelTimeMatrixComputer(
            transport_network,
            origins=hexgrid_centroids,
            destinations=clipped_destinations,
            departure=datetime.datetime(2023, 12, 5, 6, 30),
            transport_modes=[r5py.TransportMode.WALK, r5py.TransportMode.TRANSIT],
        )

        travel_times = travel_time_matrix_computer.compute_travel_times()

        travel_time_pivot = travel_times.pivot(
            index="from_id", columns="to_id", values="travel_time"
        )
        travel_time_pivot["mean"] = travel_time_pivot.mean(axis=1)
        travel_time_pivot = travel_time_pivot[["mean"]]

        results = hexgrid.join(other=travel_time_pivot, on="id")

        results.plot(column="mean", cmap="magma_r")
        plt.savefig(f"/home/emily/thesis_BA/data/output/{gtfs_name}_{county}.png")
        plt.close

def clip_destinations(destinations, hexgrid):
    boundary = hexgrid.unary_union
    clipping_buffer = boundary.buffer(distance=0.05)
    clipped_destinations = destinations.clip(clipping_buffer)
    return clipped_destinations

class Destination(Enum):
        SCHOOLS = auto()
        SELF = auto()

def centroids(hexgrid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hexgrid_centroids = hexgrid.copy()
    hexgrid_centroids["geometry"] = hexgrid.centroid
    return hexgrid_centroids

def find_destinations(osm_data, desired_destination: Destination.__members__) -> gpd.GeoDataFrame:
    if desired_destination is Destination.SCHOOLS:
        filter = {"amenity": ["school"]}

    destinations = osmfile.extract_destinations(osm_data=osm_data, filter=filter)
    return destinations


if __name__ == "__main__":
    main()
