"""SkyTrain station reference data for commute estimation.

Home is Commercial-Broadway (the Expo/Millennium interchange), so each station
carries a precomputed ``stops_to_home`` — the number of stops to Commercial-
Broadway along the fastest route. Baking that in avoids modelling the branch
topology at runtime. Coordinates are approximate (±~100 m), which is plenty for
nearest-station matching and a rough commute estimate.

Only Expo and Millennium line stations are listed — those are the lines Ricky
considers acceptable. Add Canada Line etc. here if that ever changes.
"""
from __future__ import annotations

# name: (lat, lng, [lines], stops_to_home)
# stops_to_home = stops to Commercial-Broadway via the fastest route.
STATIONS: dict[str, tuple[float, float, list[str], int]] = {
    # ── Expo, west of the interchange (toward Waterfront) ──
    "Waterfront":                 (49.2859, -123.1118, ["Expo"], 5),
    "Burrard":                    (49.2856, -123.1201, ["Expo"], 4),
    "Granville":                  (49.2838, -123.1162, ["Expo"], 3),
    "Stadium-Chinatown":          (49.2796, -123.1094, ["Expo"], 2),
    "Main Street-Science World":  (49.2730, -123.1003, ["Expo"], 1),
    # ── The interchange / home ──
    "Commercial-Broadway":        (49.2625, -123.0691, ["Expo", "Millennium"], 0),
    # ── Expo, east toward Surrey ──
    "Nanaimo":                    (49.2484, -123.0560, ["Expo"], 1),
    "29th Avenue":                (49.2445, -123.0461, ["Expo"], 2),
    "Joyce-Collingwood":          (49.2382, -123.0319, ["Expo"], 3),
    "Patterson":                  (49.2295, -123.0114, ["Expo"], 4),
    "Metrotown":                  (49.2257, -123.0040, ["Expo"], 5),
    "Royal Oak":                  (49.2192, -122.9882, ["Expo"], 6),
    "Edmonds":                    (49.2127, -122.9586, ["Expo"], 7),
    "22nd Street":                (49.2010, -122.9490, ["Expo"], 8),
    "New Westminster":            (49.2013, -122.9123, ["Expo"], 9),
    "Columbia":                   (49.2046, -122.9061, ["Expo"], 10),
    # Expo, King George branch (after Columbia)
    "Scott Road":                 (49.1969, -122.8744, ["Expo"], 11),
    "Gateway":                    (49.1907, -122.8508, ["Expo"], 12),
    "Surrey Central":             (49.1894, -122.8480, ["Expo"], 13),
    "King George":                (49.1828, -122.8453, ["Expo"], 14),
    # Expo, Production Way branch (after Columbia)
    "Sapperton":                  (49.2191, -122.8889, ["Expo"], 11),
    "Braid":                      (49.2271, -122.8835, ["Expo"], 12),
    # ── Millennium, east of the interchange ──
    "VCC-Clark":                  (49.2657, -123.0788, ["Millennium"], 1),
    "Renfrew":                    (49.2591, -123.0455, ["Millennium"], 1),
    "Rupert":                     (49.2606, -123.0337, ["Millennium"], 2),
    "Gilmore":                    (49.2655, -123.0166, ["Millennium"], 3),
    "Brentwood Town Centre":      (49.2665, -123.0024, ["Millennium"], 4),
    "Holdom":                     (49.2647, -122.9897, ["Millennium"], 5),
    "Sperling-Burnaby Lake":      (49.2533, -122.9645, ["Millennium"], 6),
    "Lake City Way":              (49.2520, -122.9468, ["Millennium"], 7),
    "Production Way-University":  (49.2526, -122.9176, ["Expo", "Millennium"], 8),
    "Lougheed Town Centre":       (49.2485, -122.8964, ["Expo", "Millennium"], 9),
    "Burquitlam":                 (49.2615, -122.8893, ["Millennium"], 10),
    "Moody Centre":               (49.2790, -122.8420, ["Millennium"], 11),
    "Inlet Centre":               (49.2787, -122.8210, ["Millennium"], 12),
    "Coquitlam Central":          (49.2799, -122.7993, ["Millennium"], 13),
    "Lincoln":                    (49.2789, -122.7935, ["Millennium"], 14),
    "Lafarge Lake-Douglas":       (49.2855, -122.7935, ["Millennium"], 15),
}
