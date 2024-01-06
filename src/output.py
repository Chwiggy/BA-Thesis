import geopandas as gpd
from matplotlib import pyplot as plt


def to_png(name: str, county: str, results: gpd.GeoDataFrame):
    results.plot(column="mean", cmap="magma_r", legend=True)
    plt.savefig(f"/home/emily/thesis_BA/data/output/{name}_{county}.png")
    plt.close


# TODO add geojson export
