import argparse
import shapely
import pyrosm
import r5py
import h3pandas as h3
import destination
import centrality
import osmfile
from output import to_png
from gtfs import departure_time, name_from_path, dataframe_from_stops


def main(gtfs_path: str):
    # TODO clean this up, maybe processing library
    # TODO config file with save locations and destination types
    gtfs_name = name_from_path(gtfs_path)

    stops_gdf = dataframe_from_stops(gtfs_path)

    matching_file = osmfile.get_osm_data(geodata=stops_gdf, name=gtfs_name)
    osm_data = pyrosm.pyrosm.OSM(matching_file.path)

    # hexgrids per county in dataframe
    counties = osmfile.extract_counties(osm_data)
    county_hexgrids = osmfile.counties_to_hexgrids(counties)

    desired_destination = destination.Destination.SCHOOLS
    destinations = destination.find_destinations(osm_data=osm_data, desired_destination=desired_destination, county_hexgrids=county_hexgrids)

    # TODO why on earth are you quietly terminating my script?
    transport_network = r5py.TransportNetwork(
        osm_pbf=matching_file.path, gtfs=gtfs_path
    )

    departure = departure_time(desired_destination, transport_network)

    for county, hexgrid in county_hexgrids.items():

        clipped_destinations = destination.clip_destinations(destinations, hexgrid)

        results = centrality.closeness_centrality(
            transport_network=transport_network,
            hexgrid=hexgrid,
            destinations=clipped_destinations,
            departure= departure
        )

        to_png(gtfs_name, county, results)

def cli_input():
    parser = argparse.ArgumentParser(description="closeness centrality calculations for all counties in one gtfs file")
    parser.add_argument("gtfs")
    args = parser.parse_args()
    gtfs_path = args.gtfs
    return gtfs_path

if __name__ == "__main__":
    gtfs_path = cli_input()
    main(gtfs_path)
