import argparse
import logging as log
import osmfile
import pyrosm
import r5py
import geopandas as gpd
import pandas as pd
import h3pandas
from destination import Destination
from gtfs import crop_gtfs
from osmfile import geocoding

def main(place_name: str, gtfs_path: str):
    
    log.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
    )


    place = geocoding(place_name)
    
    osm_file = osmfile.get_osm_data(geodata=place, name = place_name)
    osm_data = pyrosm.pyrosm.OSM(osm_file.path)
    
    gtfs_cropped = crop_gtfs(gtfs_path, place)
    
    transport_network = r5py.TransportNetwork(
        osm_pbf=osm_file.path, gtfs=gtfs_cropped
    )

    #TODO Hexgrids
    hexgrid = place.h3.polyfill_resample(10)
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"h3_polyfill": "id"}, inplace=True)

        

    for destination in Destination.__members__:
        # TODO clean up processing in batch.py and insert
        raise NotImplementedError
    
    

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