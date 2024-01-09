import sys
import logging as log
import geopandas as gpd
import osmnx as ox
import pandas as pd
import pyrosm
import datetime
from enum import Enum, auto
from typing import Union
import gtfs
import osmfile as osm
from dataclasses import dataclass
from pathlib import Path


def geocoding(place_name: Union[str, list]) -> gpd.GeoDataFrame:
    """
    Nominatim place name lookup via osmnx. Returns first result.
    Retries with user input if no result found.
    param: place_name: string or list of strings with placenames to geocode
    return: gpd.GeoDataFrame
    """
    while True:
        try:
            return ox.geocode_to_gdf(query=place_name)
        except ConnectionError:
            log.critical(
                msg="This operation needs a network connection. Terminating application"
            )
            sys.exit()
        except ox._errors.InsufficientResponseError:
            log.error(
                "Couldn't find a location matching the location selected. Please try again! Or type quit to exit."
            )
            place_name = input("location: ")

            if place_name == "quit":
                sys.exit()
            else:
                continue


def extract_counties(osm_data: pyrosm.pyrosm.OSM) -> gpd.GeoDataFrame:
    """
    Extracts boundaries of admin level 6 from pyrosm data
    """
    admin_boundaries = osm_data.get_boundaries()
    # TODO add admin_levels enum for different countries
    counties = admin_boundaries[admin_boundaries["admin_level"] == "6"]
    return counties


def counties_to_hexgrids(counties: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Extracts counties from pyrosm admin boundary dataframe and overlays h3 hexgrid.
    ## Parameters
    counties: GeoDataFrame with counties extracted by pyrosm
    ## Return
    hexgrid: gpd.GeoDataFrame with hexgrids
    """
    hexgrid = counties.h3.polyfill_resample(10)
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"id": "county_id", "h3_polyfill": "id"}, inplace=True)
    return hexgrid


def places_to_hexgrids(place: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Extracts counties from osmnx query dataframe and overlays h3 hexgrid.
    ## Parameters
    place: GeoDataFrame with places geocoded with osmnx
    ## Return
    hexgrid: gpd.GeoDataFrame with hexgrids
    """
    hexgrid = place.h3.polyfill_resample(10)
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"h3_polyfill": "id"}, inplace=True)
    return hexgrid


# TODO rework this as a dict?
class DestinationEnum(Enum):
    OSM_SCHOOLS_MORNING = auto()
    OSM_SCHOOLS_NOON = auto()


@dataclass
class DestinationSet:
    name: str
    destinations: gpd.GeoDataFrame
    departure_time: datetime.time
    reversed: bool = False


def osm_destination_set(
    osm_file: osm.OSMFile, desired_destination: DestinationEnum
) -> DestinationSet:
    """
    Extracts predefined destinations from OSM data.
    param: osm_file: OSMFile loaded with osmfile module.
    param: desired_destination: destination entry from DestinationEnum
    return: DestinationSet
    """
    name = osm_file.name + desired_destination.name
    osm_data = osm_file.load_osm_data()

    match desired_destination:
        case DestinationEnum.OSM_SCHOOLS_MORNING:
            time = datetime.time(hour=6, minute=30)
            custom_filter = {"amenity": ["school"]}
            reversed = False

        case DestinationEnum.OSM_SCHOOLS_NOON:
            time = datetime.time(hour=13, minute=0)
            custom_filter = {"amenity": ["school"]}
            reversed = True

    gdf = extract_destinations(osm_data=osm_data, filter=custom_filter)

    return DestinationSet(
        name=name, destinations=gdf, departure_time=time, reversed=reversed
    )


def local_destination_set(file: Path, mask: gpd.GeoDataFrame = None) -> Union [DestinationSet, None]:
    if file.is_dir():
        return None
    if not file.match("*.json"):
        return None
       
    #processing GeoJSON as destination set
    gdf = gpd.read_file(filename=file, mask=mask)
    if gdf.empty() or gdf is None:
        return None
    gdf['geometry'] = gdf.centroid
    
    name, _ = file.name.split(".")
    time = datetime.time(hour=13, minute=0)

    return DestinationSet(
        name=name, destinations=gdf, departure_time=time
    )

    


def extract_destinations(osm_data: pyrosm.pyrosm.OSM, filter: dict) -> gpd.GeoDataFrame:
    destinations = osm_data.get_data_by_custom_criteria(custom_filter=filter)
    destinations_centroids = destinations.copy()
    destinations_centroids["geometry"] = destinations.centroid
    return destinations_centroids


def destinations_from_osm(
    osm_data: pyrosm.pyrosm.OSM, desired_destination: DestinationEnum.__members__
) -> gpd.GeoDataFrame:
    if desired_destination is DestinationEnum.SCHOOLS:
        filter = {"amenity": ["school"]}
    else:
        raise NotImplementedError

    destinations = extract_destinations(osm_data=osm_data, filter=filter)
    return destinations


def centroids(hexgrid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hexgrid_centroids = hexgrid.copy()
    hexgrid_centroids["geometry"] = hexgrid.centroid
    return hexgrid_centroids


# TODO sort this out to be less reliant on pyrosm for the cases where pyrosm data is not available or sufficient.


def find_batch_destinations(
    osm_data: pyrosm.pyrosm.OSM,
    desired_destination: DestinationEnum.__members__,
    county_hexgrids: gpd.GeoDataFrame = None,
) -> gpd.GeoDataFrame:
    if desired_destination == DestinationEnum.SELF:
        if county_hexgrids is None:
            raise ValueError
        centroid_list = []
        for _, hexgrid in county_hexgrids.items():
            centroids_gdf = centroids(hexgrid=hexgrid)
            centroid_list.append(centroids_gdf)
        destinations = pd.concat(centroid_list, ignore_index=True)
        return destinations

    destinations = destinations_from_osm(osm_data, desired_destination)
    return destinations


def clip_destinations(destinations, hexgrid):
    boundary = hexgrid.unary_union
    clipping_buffer = boundary.buffer(distance=0.05)
    clipped_destinations = destinations.clip(clipping_buffer)
    return clipped_destinations
