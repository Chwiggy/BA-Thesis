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
import raster
from dataclasses import dataclass
from pathlib import Path
from shapely.geometry import mapping


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

def buffer(data: gpd.GeoDataFrame, buffer: int) -> gpd.GeoDataFrame:
    """
    Return a buffer from an EPSG:4326 GeoDataFrame.
    param: data: GeoDataFrame in EPSG:4326
    param: buffer: distance for the buffer in meters
    return: utm_place: data frame with buffer applied
    """
    utm_place = data.to_crs(crs=data.estimate_utm_crs(), inplace=False)
    utm_place["geometry"] = utm_place.buffer(distance=buffer)
    utm_place.to_crs(crs="EPSG:4326", inplace=True)

    return utm_place

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
    # TODO resolution = 9 might be a bit coarse for results but brings enormous savings
    
    hexgrid = place.h3.polyfill_resample(9)
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"h3_polyfill": "id"}, inplace=True)
    return hexgrid

def places_to_pop_hexgrids(place: gpd.GeoDataFrame, pop_data: str) -> gpd.GeoDataFrame:
    populated_place = raster.gdf_to_data_raster(place, pop_data)
    # TODO use h3pandas to aggregate population density data
    # TODO use hexgrid areas to get population per cell
    hexgrid = populated_place.h3.polyfill_resample(9)
    hexgrid_with_areas = hexgrid.h3.cell_area()
    hexgrid['population'] = hexgrid_with_areas['h3_cell_area'] * hexgrid_with_areas['pop_density']
    hexgrid.reset_index(inplace=True)
    hexgrid.rename(columns={"h3_polyfill": "id"}, inplace=True)
    hexgrid.clip(mask=place, keep_geom_type=True)
    return hexgrid
    

class DestinationEnum(Enum):
    OSM_SCHOOLS_MORNING = auto()
    OSM_SCHOOLS_NOON = auto()


# TODO add times throughout the day
class TimeEnum(Enum):
    MORNING = datetime.time(hour=12, minute=0)
    NOON = datetime.time(hour=12, minute=0)
    EVENING = datetime.time(hour=18, minute=0)
    NIGHT = datetime.time(hour=0, minute=30)


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


def local_destination_set(
    file: Path, mask: gpd.GeoDataFrame = None
) -> Union[DestinationSet, None]:
    """
    Takes local pre-processed poi geodatasets in geoJSON format and returns destination datasets
    """
    if file.is_dir():
        return None
    if not file.match("*.json"):
        return None

    # processing GeoJSON as destination set
    gdf = gpd.read_file(filename=file, mask=mask)
    if gdf.empty:
        return None
    gdf["geometry"] = gdf.centroid

    name, _ = file.name.split(".")
    time = datetime.time(hour=13, minute=0)

    return DestinationSet(name=name, destinations=gdf, departure_time=time)


def destination_sets_from_dataframe(data: gpd.GeoDataFrame, times: Enum) -> list[DestinationSet]:
    destinations = []
    for time in times:
        destination = DestinationSet(
            name="self" + time.name,
            destinations=centroids(hexgrid=data),
            departure_time=time.value,
        )
        destinations.append(destination)
    return destinations



def extract_destinations(osm_data: pyrosm.pyrosm.OSM, filter: dict) -> gpd.GeoDataFrame:
    # TODO extracting osm destinations seems to just quietly fail if the data set is too large
    log.debug(f"Attempting to extract osm data with pyrosm for {filter}")
    destinations = osm_data.get_data_by_custom_criteria(custom_filter=filter)
    log.info("extracted destinations from osm data")
    destinations_centroids = destinations.copy()
    log.debug("creating centroids")
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



