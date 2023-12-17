import datetime
import geopandas as gpd
import r5py
from destination import centroids

def closeness_centrality(
    transport_network: r5py.TransportNetwork,
    hexgrid: gpd.GeoDataFrame,
    destinations: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    # TODO add way to automaticall set departure
    hexgrid_centroids = centroids(hexgrid)

    travel_time_matrix_computer = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=hexgrid_centroids,
        destinations=destinations,
        departure=datetime.datetime(2023, 12, 5, 6, 30),
        transport_modes=[r5py.TransportMode.WALK, r5py.TransportMode.TRANSIT],
    )

    travel_times = travel_time_matrix_computer.compute_travel_times()

    travel_time_pivot = travel_times.pivot(
        index="from_id", columns="to_id", values="travel_time"
    )
    travel_time_pivot["mean"] = travel_time_pivot.mean(axis=1)
    travel_time_pivot = travel_time_pivot[["mean"]]

    results = hexgrid.join(other=travel_time_pivot, on="id")
    return results