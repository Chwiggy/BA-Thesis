import argparse
import logging as log
import osmfile
import pyrosm
import r5py
import geopandas as gpd
import pandas as pd
import h3pandas
from destination import Destination
import gtfs
from osmfile import geocoding
import centrality

def main(place_name: str, gtfs_path: str):
    
    log.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
    )

    transit_feed = gtfs.GTFS(path = gtfs_path)
    gtfs_cropped = gtfs.crop_gtfs(gtfs_path, place)

    place = geocoding(place_name)
    
    matching_osm_file = osmfile.get_osm_data(geodata=place, name = place_name)
    osm_data = pyrosm.pyrosm.OSM(matching_osm_file.path)
    
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_osm_file.path, gtfs=transit_feed.path
    )

    #Making Hexgrids
    hexgrid = place.h3.polyfill_resample(10)
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"h3_polyfill": "id"}, inplace=True)

    for destination in Destination.__members__:
        # TODO clean up processing in batch.py and insert
        centrality.closeness_centrality(
            transport_network=transport_network,
            hexgrid=hexgrid,
            destinations= #TODO process destinations,
            departure= #TODO Departure time processing,
            transport_modes=[r5py.TransportMode.WALK, r5py.TransportMode.TRANSIT],
        )
    
    

def cli_input():
    parser = argparse.ArgumentParser(description="all closeness centrality calculations for one county")
    parser.add_argument("place")
    parser.add_argument("-g", '--gtfs')
    args = parser.parse_args()
    place_name = args.county
    gtfs_path = args.gtfs

    return place_name,gtfs_path


if __name__ == "__main__":
    place_name, gtfs_path = cli_input()
    main(place_name, gtfs_path)