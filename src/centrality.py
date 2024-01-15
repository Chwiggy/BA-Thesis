import datetime
import logging as log
import pandas as pd
import geopandas as gpd
import r5py
import destination as dst


def closeness_centrality(
    transport_network: r5py.TransportNetwork,
    hexgrid: gpd.GeoDataFrame,
    destinations: gpd.GeoDataFrame,
    departure: datetime.datetime,
) -> gpd.GeoDataFrame:
    # TODO add way to automatically set departure
    # TODO deprecate in batch.py
    log.warn(msg="This function is deprecated")

    # TODO departure time window is narrow but for testing this might help reduce load 
    travel_time_matrix_computer = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=hexgrid,
        destinations=destinations,
        departure=departure,
        departure_time_window=datetime.timedelta(minutes=20),
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


def closeness_new(
    transit: r5py.TransportNetwork,
    hexgrid: gpd.GeoDataFrame,
    destination=dst.DestinationSet,
) -> gpd.GeoDataFrame:
    log.info(msg=f"Instantiating TravelTimeMatrixComputer for {destination.name}")
    travel_time_matrix_computer = r5py.TravelTimeMatrixComputer(
        transport_network=transit,
        origins=hexgrid,
        destinations=destination.destinations,
        departure=departure_time(transit, destination),
        departure_time_window=datetime.timedelta(minutes=60),
        transport_modes=[r5py.TransportMode.WALK, r5py.TransportMode.TRANSIT],
    )
    log.info(
        msg=f"Computing Travel Time Matrix for {destination.name}. This might take a while ..."
    )
    travel_times = travel_time_matrix_computer.compute_travel_times()
    log.info(msg="Finished calculating travel times")

    if destination.reversed:
        travel_time_pivot = travel_times.pivot(
            index="to_id", columns="from_id", values="travel_time"
        )
    else:
        travel_time_pivot = travel_times.pivot(
            index="from_id", columns="to_id", values="travel_time"
        )
    
    result = travel_time_pivot.copy()
    result[f"mean_{destination.name}"] = travel_time_pivot.mean(axis=1)
    # TODO pass up limit for config
    result[f"reach_{destination.name}"] = reachable_destinations(pivot_table=travel_time_pivot, limit=45)
    result[f"reach_{destination.name}"] = result[f"reach_{destination.name}"].astype(int)
    result = result[[f"mean_{destination.name}", f"reach_{destination.name}"]]
    return result

def reachable_destinations(pivot_table:gpd.GeoDataFrame, limit: int) -> pd.Series:
    """
    Check for destinations reachable within a set limit
    param: pivot_table: pivoted gpd.GeoDataFrame from r5py.TravelTimeMatrixComputor
    returns: pandas series with number of reachable destinations.
    """
    bool_limit_table = pivot_table.map(func=lambda x: __within_limit(value=x, limit=limit), na_action='ignore')
    reach_limit_sum = bool_limit_table.sum(axis=1, skipna=True)
    return reach_limit_sum

def __within_limit(value, limit: int) -> bool:
    """Simple callable for reachable_destination pandas.DataFrame.map call"""
    if type(value) is not float:
        return False
    elif value > limit:
        return False
    return True


def departure_time(
    transit: r5py.TransportNetwork, destination: dst.DestinationSet
) -> datetime.datetime:
    start_date = transit.transit_layer.start_date
    end_date = transit.transit_layer.end_date
    delta = (end_date - start_date) / 2
    center = start_date + delta
    departure_time = center.replace(
        hour=destination.departure_time.hour, minute=destination.departure_time.minute
    )
    return departure_time
