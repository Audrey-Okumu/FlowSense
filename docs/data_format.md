# Data format
Vision output, one JSON record per second of video:
{"timestamp": 12.0, "lanes": {"north": 12, "south": 3, "east": 7, "west": 2}}
- lanes = vehicles currently inside each approach zone (a live queue), not a running total
- Mapping to SUMO: north = N_in, south = S_in, east = E_in, west = W_in