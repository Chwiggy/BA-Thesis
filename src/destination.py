import sys
import logging as log
import geopandas as gpd
import osmnx as ox
import pandas as pd
import pyrosm
from enum import Enum, auto
from typing import Union
import gtfs

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
            log.critical(msg="This operation needs a network connection. Terminating application")
            sys.exit()
        except ox._errors.InsufficientResponseError:
            log.error("Couldn't find a location matching the location selected. Please try again! Or type quit to exit.")
            place_name = input("location: ")

            if place_name == "quit":
                sys.exit()
            else: continue

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
class Destination(Enum):
    OSM_SCHOOLS = auto()
    SELF = auto()
    POPULATION = auto()


def extract_destinations(osm_data: pyrosm.pyrosm.OSM, filter: dict) -> gpd.GeoDataFrame:
    destinations = osm_data.get_data_by_custom_criteria(custom_filter=filter)
    destinations_centroids = destinations.copy()
    destinations_centroids['geometry']= destinations.centroid
    return destinations_centroids


def destinations_from_osm(
    osm_data: pyrosm.pyrosm.OSM, desired_destination: Destination.__members__
) -> gpd.GeoDataFrame:
    if desired_destination is Destination.SCHOOLS:
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
    desired_destination: Destination.__members__,
    county_hexgrids: gpd.GeoDataFrame = None,
) -> gpd.GeoDataFrame:
    if desired_destination == Destination.SELF:
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


def find_destinations(
    osm_data: pyrosm.pyrosm.OSM,
    desired_destination: Destination.__members__,
    location: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    match desired_destination:
        case Destination.SCHOOLS:
            name = "osm_schools"
            destination = None # TODO needs work,
            departure_time = gtfs.departure_time()
        case Destination.SELF:
            raise NotImplementedError
    
    
    
    return name, destination, departure_time
            


def clip_destinations(destinations, hexgrid):
    boundary = hexgrid.unary_union
    clipping_buffer = boundary.buffer(distance=0.05)
    clipped_destinations = destinations.clip(clipping_buffer)
    return clipped_destinations












