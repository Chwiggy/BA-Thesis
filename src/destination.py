import geopandas as gpd
import pandas as pd
import pyrosm
import osmfile
from enum import Enum, auto
import gtfs


class Destination(Enum):
    SCHOOLS = auto()
    SELF = auto()


def destinations_from_osm(
    osm_data, desired_destination: Destination.__members__
) -> gpd.GeoDataFrame:
    if desired_destination is Destination.SCHOOLS:
        filter = {"amenity": ["school"]}
    else:
        raise NotImplementedError

    destinations = osmfile.extract_destinations(osm_data=osm_data, filter=filter)
    return destinations


def centroids(hexgrid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hexgrid_centroids = hexgrid.copy()
    hexgrid_centroids["geometry"] = hexgrid.centroid
    return hexgrid_centroids


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
            destination = #TODO NEEDS work,
            departure_time = gtfs.departure_time()
        case Destination.SELF:
            raise NotImplementedError
    
    
    
    return name, destination, departure_time
            


def clip_destinations(destinations, hexgrid):
    boundary = hexgrid.unary_union
    clipping_buffer = boundary.buffer(distance=0.05)
    clipped_destinations = destinations.clip(clipping_buffer)
    return clipped_destinations
