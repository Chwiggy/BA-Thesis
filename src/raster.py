import numpy as np
import geopandas as gpd
import rasterio as rio
import logging as log
from pathlib import Path
from shapely.geometry import mapping
from rasterio.mask import mask
from rasterio.features import shapes

def gdf_to_data_raster(place: gpd.GeoDataFrame, data: Path) -> gpd.GeoDataFrame|None:
    geometry = place.unary_union.convex_hull
    feature = [mapping(geometry)]
    vector_crs = place.crs

    with rio.open(data) as source:
    
        raster_crs = source.crs

        try:
            log.info(msg='Attempting to crop population data')
            image, out_transform = mask(dataset=source, shapes=feature, all_touched=True, crop=True )
        except ValueError:
            log.warn(msg='Could not find raster data matching the location. Continuing without.')
            return None
        
    # randomiser = np.random.uniform(size=image.shape).astype(np.float32)
    # new_image = image + randomiser

    results = ({'properties': {'pop_density': v}, 'geometry': s} for i, (s, v) in enumerate(shapes(source=image.astype(rio.float32), transform=out_transform)))

    geoms = list(results)
    gdf = gpd.GeoDataFrame.from_features(geoms)
    gdf.set_crs(crs="EPSG:4326", inplace=True)
    # gdf['raster_val'] = np.floor(gdf['raster_val'].astype(int))
    return gdf

    

