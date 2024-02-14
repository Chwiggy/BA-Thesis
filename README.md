# Multi-Temporal Reach
This project is an attempt at creating a tool to detect gaps in public transit coverage from both a network analysis perspective as well as an intersectional perspective.
It is part of a larger thesis project with a not-yet-started write-up [here](https://github.com/Chwiggy/thesis_bachelor)

## Installation
Clone this repository.
To run the application you might want to change the config parameters in `config.ini`
And run
```
docker build -t thesis .
```
Then run
```
docker run thesis
```


## Questions
~~Can closeness centrality map on to car and public transport differences~~
Can closeness centrality work as an indicator for temporal public transport variabilty within cities? Why?


## TODOs
- [x] population data and lorenz curves
- [x] temporal analysis: many departure times a day, compare results: use case ebay classifieds and friends
- [x] think about equalizing of closeness centrality
- [ ] manual clustering by amplitude of differences
- [ ] final run on server
    - [ ] optimise script for server usage
    - [ ] difference between 10th and 90th percentile as a measure of "turning up and wait"-abilty vs a need to plan
    - [ ] run analysis for heidelberg + surrounding area on server
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
