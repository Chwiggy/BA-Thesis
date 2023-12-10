import zipfile
import datetime
import geopandas as gp
import pandas as pd
import shapely
from sys import argv

def main():
    #TODO argparse?
    gtfs_path = argv[1]
    
    #TODO read in gtfs feed
    with zipfile.ZipFile(gtfs_path) as gtfs:
        with gtfs.open('stops.txt') as stops_file:
            stops_df = pd.read_table(stops_file, sep=",")

    stops_gdf = gp.GeoDataFrame(
        stops_df, geometry=gp.points_from_xy(stops_df.stop_lon, stops_df.stop_lat), crs="EPSG:4326"
    )

    index = OSMIndex(path="data/indices/osm_data.json")
    index.load_osm_fileindex
    index.find_osm_file(gdf=stops_gdf)

    #TODO get bounds from gtfs feed
    #TODO download relevant osm data within those bounds
    #TODO instantiate TravelTimeMatrixComputer object from r5py
    #TODO find pois and create destination enum
    #TODO hexgrids
    #TODO loop over counties with travel time matrix calculations
    #TODO output plots and data files

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
    """Class for index of osm data and associated operations"""
    def __init__(self, path: str = None ) -> None:
        self.path = path
        self.gdf = None

    def load_osm_fileindex(self) -> None:
        """Loads osm indek into memory as a geopandas.GeoDataFrame"""
        if self.path is None:
            self.gdf = gp.GeoDataFrame()
            return
        self.gdf = gp.read_file(self.path)

    def add_file(self, file: OSMFile) -> None:
        """
        Append the currently loaded osm index with data from an OSMFile.
        param: file: OSMFile object to add to the index
        """
        new_row = {"agency": file.agency, "date": file.date, "path": file.path, "geometry": file.extent}
        self.gdf = self.gdf.append(new_row)

    def save_osmindex(self, path: str = None) -> None:
        """
        Saves OSMIndex at specified location
        param: path: save location (optional). If left unspecified overrites existing index.
        """
        if self.path is None:
            self.path = path
        self.gdf.to_file(filename=self.path, driver="GeoJSON", crs="EPSG:4326")
    
    def isempty(self):
        """Tests if currently loaded index is empty"""
        return bool(len(self.gdf))

    def find_osm_file(self, gdf: gp.GeoDataFrame) -> OSMFile:
        """
        Searches smallest available index entry that covers the extent of another GeoDataFrame
        param: gdf: geopandas.GeoDataFrame to cover
        return: matching_file: OSMFile that matches criteria or None if none found
        """
        if self.isempty():
            return None
        
        matching_rows = self.gdf.contains(gdf.unary_union)
        if len(matching_rows) == 0:
            return None
        #TODO output type

        coverage = self.gdf[matching_rows]["geometry"].area
        smallest = coverage.idxmin()
        
        matching_file = OSMFile(
            path=self.gdf.iloc[smallest]["path"],
            extent=self.gdf.iloc[smallest]["geometry"],
            agency=self.gdf.iloc[smallest]["agency"],
            date=self.gdf.iloc[smallest]["date"]
        )
        
        return matching_file
    

class MissingPath(Exception):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(*args)
        self.message = message
