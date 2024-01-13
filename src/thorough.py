import argparse
import logging as log
import r5py
import geopandas as gpd
import pandas as pd
import h3pandas
import destination as dst
import gtfs
import osmfile as osm
import centrality
from pathlib import Path


def main(place_name: str, gtfs_path: str):
    log.debug(msg="testing")
    # TODO config file

    place = dst.geocoding(place_name)
    # TODO make buffer more sensible
    buffered_place = place.copy()
    buffered_place["geometry"] = place.buffer(distance=0.05)

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

    hexgrid = dst.places_to_hexgrids(place)
    # TODO exclude non populated areas

    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_osm_file.path, gtfs=transit_feed.path
    )

    # Processing all available destination data
    destinations = []
    # TODO osm data extraction with pyrosm seems to be annoying -> alternatives?
    # for entry in dst.DestinationEnum:
    #    destination = dst.osm_destination_set(
    #        osm_file=matching_osm_file, desired_destination=entry
    #    )
    #    destinations.append(destination)
    data_dir = Path("/home/emily/thesis_BA/data/destinations")
    for child in data_dir.iterdir():
        destination = dst.local_destination_set(file=child, mask=buffered_place)
        if destination is None:
            continue
        destinations.append(destination)
    # Adding Self Destinations
    destinations.extend(dst.destination_sets_from_dataframe(data=hexgrid))

    # Computing and matching up results
    results = hexgrid.copy()
    for destination in destinations:
        result = centrality.closeness_new(
            transit=transport_network,
            hexgrid=dst.centroids(hexgrid),
            destination=destination,
        )
        results = results.join(other=result, on="id")
        # TODO see if this actually works
    results.to_file(
        filename=f"{place_name}.json"
    )  # TODO add actual file path for results...

    # TODO analyse results


def cli_input():
    parser = argparse.ArgumentParser(
        description="all closeness centrality calculations for one county"
    )
    parser.add_argument("place")
    parser.add_argument("-g", "--gtfs")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    place_name = args.place
    gtfs_path = args.gtfs
    verbosity = args.verbose
    if verbosity:
        log.basicConfig(
            format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.DEBUG
        )
    else:
        log.basicConfig(
            format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
        )


    return place_name, gtfs_path


if __name__ == "__main__":
    place_name, gtfs_path = cli_input()
    main(place_name, gtfs_path)
