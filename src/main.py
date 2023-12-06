import zipfile
import datetime
import dataclasses
import geopandas as gp
import pandas as pd
import shapely
from typing import Union

def main():

    #TODO read in gtfs feed
    with zipfile.ZipFile('/home/emily/thesis_BA/data/gtfs/2023_rnv_gtfs.zip') as gtfs:
        with gtfs.open('stops.txt') as stops_file:
            gp.GeoDataFrame(stops_file)

    #TODO get bounds from gtfs feed
    #TODO download relevant osm data within those bounds
    #TODO instantiate TravelTimeMatrixComputer object from r5py
    #TODO find pois

if __name__ == "__main__":
    main()


class OSMFile:
    """Class to provide basic properties of an osm.pbf file for transfer"""
    def __init__(self, agency: str, date: datetime.datetime, extent: shapely.Polygon, path: str = None, dir_path: str = None,) -> None:
        self.agency = agency
        self.date = date
        self.extent = extent
        
        if path is not None:
            self.path = path
        elif dir_path is not None:
            self.path = dir_path + f"/{self.agency}_{self.date.strftime('%Y')}.osm.pbf"
        else:
            raise MissingPath(message="Did not provide a filepath for OSMFile")


class OSMIndex:
    def __init__(self, path: str = None ) -> None:
        self.path = path

    def load_osm_fileindex(self) -> None:
        if self.path is None:
            self.gdf = gp.GeoDataFrame(crs="EPSG:4326")
            return
        self.gdf = gp.read_file(self.path)

    def add_file(self, file: OSMFile) -> None:
        new_row = {"agency": file.agency, "date": file.date, "path": file.path, "geometry": file.extent}
        self.gdf = self.gdf.append(new_row)

    def add_files(self, files: list(OSMFile)) -> None:
        osm_file_list = list()
        for file in files:
            new_row = {"agency": file.agency, "date": file.date, "path": file.path, "geometry": file.extent}
            osm_file_list.append(new_row)
        self.gdf = self.gdf.append(osm_file_list)

    def save_osmindex(self) -> None:
        self.gdf.to_file(filename=self.path, driver="GeoJSON", crs="EPSG:4326")

    def find_osm_file(self, gdf: gp.GeoDataFrame) -> OSMFile:
        matching_row = self.gdf.contains(gdf.unary_union)
        coverage = self.gdf[matching_row]["geometry"].area
        smallest = coverage.idxmin()
        matching_file = OSMFile(
            self.gdf.iloc[smallest]["path"]
        )
        return matching_file
    

class MissingPath(Exception):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(*args)
        self.message = message
