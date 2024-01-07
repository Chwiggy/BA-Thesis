import argparse
import r5py
import h3pandas as h3
import destination
import centrality
import osmfile
import gtfs
import logging as log
from output import to_png
from gtfs import departure_time


def main(gtfs_path: str):
    log.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log.INFO
    )

    # TODO clean this up, maybe processing library
    # TODO config file with save locations and destination types
    transit_feed = gtfs.GTFS(path=gtfs_path)
    stops_gdf = transit_feed.dataframe_from_stops()

    matching_osm_file = osmfile.get_osm_data(geodata=stops_gdf, name=transit_feed.name)
    osm_data = matching_osm_file.load_osm_data()

    # hexgrids per county in dataframe
    counties = destination.extract_counties(osm_data)
    county_hexgrids = destination.counties_to_hexgrids(counties)

    # TODO rework this with destination dataclass
    desired_destination = destination.DestinationEnum.SCHOOLS
    destinations = destination.find_batch_destinations(
        osm_data=osm_data,
        desired_destination=desired_destination,
        county_hexgrids=county_hexgrids,
    )

    # TODO why on earth are you quietly terminating my script?
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_osm_file.path, gtfs=transit_feed.path
    )

    departure = departure_time(desired_destination, transport_network)

    for name in counties["name"]:
        county_hexgrid = county_hexgrids.loc[county_hexgrids["name"] == name]

        clipped_destinations = destination.clip_destinations(
            destinations, county_hexgrid
        )

        results = centrality.closeness_centrality(
            transport_network=transport_network,
            hexgrid=destination.centroids(county_hexgrid),
            destinations=clipped_destinations,
            departure=departure,
        )

        to_png(transit_feed.name, name=name, results=results)


def cli_input():
    parser = argparse.ArgumentParser(
        description="closeness centrality calculations for all counties in one gtfs file"
    )
    parser.add_argument("gtfs")
    args = parser.parse_args()
    gtfs_path = args.gtfs
    return gtfs_path


if __name__ == "__main__":
    gtfs_path = cli_input()
    main(gtfs_path)
