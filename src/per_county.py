import argparse
import osmfile
from destination import Destination

def main():
    # user input
    parser = argparse.ArgumentParser(description="all closeness centrality calculations for one county")
    parser.add_argument("county")
    parser.add_argument("-g", '--gtfs')
    args = parser.parse_args()
    place_name = args.county
    gtfs_path = args.gtfs


    place = place_input(place_name) # TODO flesh that out
    gtfs_cropped = crop_gtfs()
    osm_data = osmfile.get_osm_data(geodata=place, name = place_name)
    

    for destination in Destination.__members__:
        # TODO clean up processing and insert
        raise NotImplementedError



if __name__ == "__main__":
    main()