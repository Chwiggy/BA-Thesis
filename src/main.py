import zipfile
import geopandas as gp

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
    