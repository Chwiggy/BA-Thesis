import geopandas as gpd
import pandas as pd
import pyrosm
import osmfile
from enum import Enum, auto


class Destination(Enum):
    SCHOOLS = auto()
    SELF = auto()


def destinations_from_osm(
    osm_data, desired_destination: Destination.__members__
) -> gpd.GeoDataFrame:
    if desired_destination is Destination.SCHOOLS:
        filter = {"amenity": ["school"]}

    destinations = osmfile.extract_destinations(osm_data=osm_data, filter=filter)
    return destinations


def centroids(hexgrid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hexgrid_centroids = hexgrid.copy()
    hexgrid_centroids["geometry"] = hexgrid.centroid
    return hexgrid_centroids


def find_destinations(osm_data: pyrosm.pyrosm.OSM, desired_destination: Destination.__members__, county_hexgrids: gpd.GeoDataFrame = None) -> gpd.GeoDataFrame:
    if desired_destination == Destination.SELF:
        if county_hexgrids is None:
            raise ValueError
        centroid_list = []
        for _, hexgrid in county_hexgrids.items():
            centroids_gdf = centroids(hexgrid=hexgrid)
            centroid_list.append(centroids_gdf)
        destinations = pd.concat(centroid_list, ignore_index=True)
        return destinations

    destinations = destinations_from_osm(osm_data, Destination, desired_destination)
    return destinations


def clip_destinations(destinations, hexgrid):
    boundary = hexgrid.unary_union
    clipping_buffer = boundary.buffer(distance=0.05)
    clipped_destinations = destinations.clip(clipping_buffer)
    return clipped_destinations