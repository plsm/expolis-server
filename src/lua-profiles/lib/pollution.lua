Config = {}

Config.min_longitude = -9.258299
Config.max_longitude = -8.895191
Config.min_latitude = 8.397111
Config.max_latitude = 38.703961
Config.raster_data = raster:load(
        '/var/lib/expolis/osrm/pollution.raster',
        Config.min_longitude,
        Config.max_longitude,
        Config.min_latitude,
        Config.max_latitude,
        551, -- num rows
        651  -- num cols
)
Config.weight_osrm = 0.5
Config.weight_pollution = 0.5

return Config
