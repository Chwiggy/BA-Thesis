

import os
import pandas as pd
import geopandas as gpd
import pyrosm
import shapely
import fiona


import subprocess



class ErrorMissingPath(Exception):
    """Error if no file path could be found."""

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(*args)
        self.message = message


class OSMFile:
    """Class to provide basic properties of an osm.pbf file for transfer"""

    def __init__(
        self,
        extent: shapely.Polygon,
        path: str = None,
        dir_path: str = None,
        name: str = "test",
    ) -> None:
        self.extent = extent
        self.name = name

        if path is not None:
            self.path = path
        elif dir_path is not None:
            self.path = dir_path + f"/{self.name}.osm.pbf"
        else:
            raise ErrorMissingPath(message="Did not provide a filepath for OSMFile")

    def crop(self, geodata: gpd.GeoDataFrame, name: str = None, inplace: bool = False):
        """
        Crops the OSM data to a new file at data/osm_data/.
        param: geodata: gpd.GeoDataFrame sets bounds to which the OSM file will be cropped.
        param: name: (Optional) sets the name of the cropped file.
        param: inplace: (Optional) If inplace is True the method returns nothing, else it returns a new OSMFile object.
        return: Cropped OSMFile ob
        """
        stop_bounds = geodata.total_bounds
        left, bottom, right, top = stop_bounds
        stops_extent = shapely.Polygon(
            shell=((left, bottom), (right, bottom), (right, top), (left, top))
        )

        if name is None:
            name = self.name + "_cropped"

        save_path = f"src/data/osm_data/{name}.osm.pbf"

        # cropping pbf to bounding box with osmosis
        subprocess.run(
            [
                "osmosis",
                "--read-pbf",
                f"file={self.path}",
                "--bounding-box",
                f"top={top}",
                f"left={left}",
                f"bottom={bottom}",
                f"right={right}",
                "completeWays=yes",
                "--write-pbf",
                f"file={save_path}",
            ]
        )

        if not inplace:
            cropped_set = OSMFile(extent=stops_extent, path=save_path, name=name)
            return cropped_set

        self.name = name
        self.path = save_path
        self.extent = stops_extent


class OSMIndex:
    """Class for index of osm data and associated operations"""

    def __init__(self, path: str = None) -> None:
        self.path = path
        self.gdf = None
        self.loaded = False

    def load_osm_fileindex(self) -> None:
        """Loads osm index into memory as a geopandas.GeoDataFrame"""
        if self.path is None:
            self.gdf = gpd.GeoDataFrame(columns=['name', 'path', 'geometry'], geometry='geometry', crs='EPSG:4326')
            self.loaded = True
            return
        try:
            self.gdf = gpd.read_file(self.path)
        except fiona.errors.DriverError:
            self.gdf = gpd.GeoDataFrame(columns=['name', 'path', 'geometry'], geometry='geometry', crs='EPSG:4326')
        self.loaded = True

    def add_file(self, file: OSMFile) -> None:
        """
        Append the currently loaded osm index with data from an OSMFile.
        param: file: OSMFile object to add to the index
        """
        if not self.loaded:
            self.load_osm_fileindex()

        new_row = gpd.GeoDataFrame({"name": [file.name], "path": [file.path], "geometry": [file.extent]}, crs='EPSG:4326')
        self.gdf = pd.concat([self.gdf, new_row], ignore_index= True)

    def save_osmindex(self, path: str = None) -> None:
        """
        Saves OSMIndex at specified location
        param: path: save location (optional). If left unspecified overrites existing index.
        """
        if not self.loaded:
            self.load_osm_fileindex()

        if self.path is None:
            if path is None:
                raise ErrorMissingPath(
                    message="Please, provide a file path to save to!"
                )
            self.path = path
        self.gdf.to_file(filename=self.path, driver="GeoJSON", crs="EPSG:4326")

    def find_osm_file(self, gdf: gpd.GeoDataFrame) -> OSMFile:
        """
        Searches smallest available index entry that covers the extent of another GeoDataFrame
        param: gdf: geopandas.GeoDataFrame to cover
        return: matching_file: OSMFile that matches criteria or None if none found
        """
        if self.gdf.empty:
            return None

        matching_rows = self.gdf.contains(gdf.unary_union)
        if len(matching_rows) == 0:
            return None
        # TODO output type

        coverage = self.gdf[matching_rows]["geometry"].area
        smallest = coverage.idxmin()

        matching_file = OSMFile(
            name=self.gdf.iloc[smallest]["name"],
            path=self.gdf.iloc[smallest]["path"],
            extent=self.gdf.iloc[smallest]["geometry"],
        )

        return matching_file


def download_osm_data(geodata: gpd.GeoDataFrame) -> OSMFile:
    """
    Downloads an OSM dataset from geofabrik that covers the extent of the provided GeoDataFrame
    param: geodata: gpd.GeoDataFrame
    return: return_data: OSMFile object
    """

    geofabrik_available = gpd.read_file("src/data/indices/geofabrik_downloadindex.json")

    # finding smallest available set covering gtfs feed
    matching_datasets = geofabrik_available.contains(geodata.unary_union)
    coverage = geofabrik_available[matching_datasets]["geometry"].area
    smallest = coverage.idxmin()
    preferred_set = geofabrik_available.iloc[smallest]["id"]
    preferred_set_extent = geofabrik_available.iloc[smallest]["geometry"]

    osm_path = pyrosm.get_data(dataset=preferred_set, directory="src/data/osm_data")

    # add set to index
    return_data = OSMFile(
        path=osm_path, extent=preferred_set_extent, name=preferred_set
    )

    return return_data


def get_osm_data(geodata: gpd.GeoDataFrame, name: str) -> OSMFile:
    """
    Acquires OSMdata either from local storage, or if no matching dataset is available by download from Geofabrik.
    If the filesize is too large for easy processing, the dataset is cropped to match the bounds of the geodata.
    param: geodata: gpd.GeoDataFrame to whoose bounds the OSM data is matched.
    param: name: name under which a potentially cropped OSM data file is stored.
    return: matching_file: file matching the extent of the provided GeoDataFrame.
    """
    index = OSMIndex(path="src/data/indices/osm_data.json")
    index.load_osm_fileindex()
    matching_file = index.find_osm_file(gdf=geodata)

    if matching_file is None:
        matching_file = download_osm_data(geodata=geodata)
        index.add_file(matching_file)

    if os.path.getsize(matching_file.path) > 500000000:
        matching_file.crop(geodata, name, inplace=True)
        index.add_file(matching_file)

    index.save_osmindex(path="src/data/indices/osm_data.json")
    return matching_file