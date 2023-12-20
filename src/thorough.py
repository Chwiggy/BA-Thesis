import argparse
import osmfile
from destination import Destination

def main(place_name: str, gtfs_path: str):

    place = place_input(place_name) # TODO flesh that out
    gtfs_cropped = crop_gtfs(gtfs_path)
    osm_data = osmfile.get_osm_data(geodata=place, name = place_name)
    

    for destination in Destination.__members__:
        # TODO clean up processing and insert
        raise NotImplementedError

def cli_input():
    parser = argparse.ArgumentParser(description="all closeness centrality calculations for one county")
    parser.add_argument("county")
    parser.add_argument("-g", '--gtfs')
    args = parser.parse_args()
    place_name = args.county
    gtfs_path = args.gtfs
    return place_name,gtfs_path



if __name__ == "__main__":
    place_name, gtfs_path = cli_input()
    main(place_name, gtfs_path)