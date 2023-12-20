import argparse
import osmfile
from destination import Destination

def main():
    # TODO argparse
    place = place_input(place_name) # TODO flesh that out
    gtfs_cropped = crop_gtfs()
    osm_data = osmfile.get_osm_data(geodata=place, name = place_name)
    

    for destination in Destination.__members__:
        # TODO clean up processing and insert
        raise NotImplementedError



if __name__ == "__main__":
    main()