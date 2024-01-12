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

    travel_time_matrix_computer = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=hexgrid,
        destinations=destinations,
        departure=departure,
        departure_time_window=datetime.timedelta(minutes=60),
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
    log.info(msg="Computing Travel Time Matrix. This might take a while ...")
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
    travel_time_pivot[f"mean_{destination.name}"] = travel_time_pivot.mean(axis=1)
    travel_time_pivot = travel_time_pivot[[f"mean_{destination.name}"]]
    return travel_time_pivot
    

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
