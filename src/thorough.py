import argparse
import logging as log
import r5py
import geopandas as gpd
import pandas as pd
import h3pandas
from destination import Destination, geocoding
import destination
import gtfs
import osmfile as osm
import centrality

def main(place_name: str, gtfs_path: str):
    
    log.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
    )

    place = geocoding(place_name)
    buffered_place = place.copy()
    buffered_place['geometry'] = place.buffer(distance=0.05)
    
    transit_feed = gtfs.GTFS(path = gtfs_path)
    try:
        transit_feed.crop_gtfs(buffered_place, inplace=True)
    except NotImplementedError:
        pass

    
    matching_osm_file = osm.get_osm_data(geodata=buffered_place, name = place_name)
    
    
    hexgrid = destination.places_to_hexgrids(place)
    
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_osm_file.path, gtfs=transit_feed.path
    )


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