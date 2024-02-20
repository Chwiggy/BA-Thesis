# Multi-Temporal Reach
This project is an attempt at creating a tool to detect gaps in public transit coverage from both a network analysis perspective as well as an intersectional perspective.
It is part of a larger thesis project with a not-yet-started write-up [here](https://github.com/Chwiggy/thesis_bachelor)

## Installation
Clone this repository. Move into the folder 
And run
```
docker build -t thesis .
```

## Usage
### Setup
Create a folder with the following contents
|folder|contents|
|------|--------|
|`gtfs`  | gtfs data either as subdirectory or as zip archive|
|`population`| population data from the [Global Human Settlement Layer](https://ghsl.jrc.ec.europa.eu/download.php?ds=pop)|
|`output`| output will be saved here as a GeoJSON|

### Execution
Run the following docker command with
```bash
docker run -v $DATAFOLDER$:/data thesis -g $GTFSPATH$ place
```
- `DATAFOLDER` needs to be an absolute path to a data folder.
- `GTFSPATH` needs to be `/data/` + the relative path to the desired gtfs file within your `DATAFOLDER`.
- `place` is a location string that will be passed to the nominatim API.

For example:
```bash
docker run -v /home/emily/thesis_BA/data/:/data -g /data/gtfs/2023_rnv_gtfs.zip thesis Wiesloch
```
```bash
docker run -v $HOME/data:/data --rm --security-opt=seccomp=unconfined --workdir=/ thesis2 -g /data/gtfs/2024-02-19_Germany.zip Heidelberg
```
## Things to keep in mind
### Esoteric WSL 2 and VPN shit

```powershell
Get-NetAdapter | Where-Object {$_.InterfaceDescription -Match "Cisco AnyConnect"} | Set-NetIPInterface -InterfaceMetric 4000
```
```powershell
Get-NetIPInterface -InterfaceAlias "vEthernet (WSL)" | Set-NetIPInterface -InterfaceMetric 1
```


## Requirements
Needs a recent `Docker` installation

## Questions
~~Can closeness centrality map on to car and public transport differences~~
Can closeness centrality work as an indicator for temporal public transport variabilty within cities? Why?


## TODOs
- [x] population data and lorenz curves
- [x] temporal analysis: many departure times a day, compare results: use case ebay classifieds and friends
- [x] think about equalizing of closeness centrality
- [ ] final run on server
    - [x] optimise script for server usage
    - [ ] difference between 10th and 90th percentile as a measure of "turning up and wait"-abilty vs a need to plan
    - [ ] run analysis for heidelberg + surrounding area on server
### New repository
- [ ] create new repo for analysis
- [ ] compare different profiles: use classification?
- [ ] pick different representative cells with detailed analysis
    - [ ] from one cell to any cell over time
    - [ ] detailed routing for outlier connections
- [ ] group by neighbourhoods
### Optionals
- [ ] compare different cities
- [ ] compare to car but with added door to door delays for cars
- [ ] compare methods for schools closeness centrality and isochrone
- [ ] open questions!
- [ ] compare cities with different layouts
