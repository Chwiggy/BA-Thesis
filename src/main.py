import argparse
import logging as log
import r5py
import geopandas as gpd
import pandas as pd
import h3pandas
import utils.destination as dst
import utils.gtfs as gtfs
import utils.osmfile as osm
import utils.centrality as centrality
import utils.centrality as centrality
import datetime
from enum import Enum

# TODO adapt this for temporal analysis, or make yet anouther script...

def main(place_name: str, gtfs_path: str):
    log.debug(msg="testing")

    place = dst.geocoding(place_name)
    buffer = 1000
    buffered_place = dst.buffer(data = place, buffer = buffer)

    transit_feed = gtfs.GTFS(path=gtfs_path)
    # Check if gtfs file actually covers the extent of the place
    if not transit_feed.covers_location(other=place):
        log.warning(
            f"specified gtfs feed at {transit_feed.path} doesn't have stop locations in specified area. Calculations for WALKING only."
        )
    try:
        transit_feed.crop_gtfs(buffered_place, inplace=True)
    except NotImplementedError:
        pass

    matching_osm_file = osm.get_osm_data(geodata=buffered_place, name=place_name)
    # TODO crop osm data to buffered place anyhow?

    hexgrid = dst.places_to_pop_hexgrids(place=buffered_place, pop_data='/data/population/GHS_POP_E2030_GLOBE_R2023A_4326_3ss_V1_0_R4_C19.tif')
    # TODO exclude non populated areas

    log.info(f"creating transport network for {place_name}")
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_osm_file.path, gtfs=transit_feed.path
    )
    log.info(f"created transport network for {place_name}")
    
    #creating enum with every time of day
    time = datetime.time(hour=0)
    hour_step = 0
    times_of_day = []
    while hour_step < 24:
        time = time.replace(hour=hour_step)
        times_of_day.append((str(time.hour),time))
        hour_step += 1
    times = Enum("Times", times_of_day)

    # Processing destination data for every time of day
    destinations = dst.destination_sets_from_dataframe(data=hexgrid, times=times)

    # Computing and matching up results
    results = hexgrid
    for destination in destinations:
        result = centrality.closeness_new(
            transit=transport_network,
            hexgrid=dst.centroids(hexgrid),
            destination=destination,
        )
        results = results.join(other=result, on="id")
        # TODO why does this randomly fail here sometimes
    
    results.to_file(f"/data/output/{place_name}.json")
    


def cli_input():
    parser = argparse.ArgumentParser(
        description="all closeness centrality calculations for one county"
    )
    parser.add_argument("place", help="specify place")
    parser.add_argument("-g", "--gtfs", help="specify gtfs file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    place_name = args.place
    config_path = args.gtfs
    verbosity = args.verbose
    if verbosity:
        log.basicConfig(
            format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.DEBUG
        )
    else:
        log.basicConfig(
            format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
        )

    return place_name, config_path


if __name__ == "__main__":
    place_name, gtfs_path = cli_input()
    main(place_name, gtfs_path)
