-- Foot profile

api_version = 2

Set = require('lib/set')
Sequence = require('lib/sequence')
Handlers = require("lib/way_handlers")
find_access_tag = require("lib/access").find_access_tag

function setup()
    local walking_speed = 5
	 pollution = require ('lib/pollution')
    return {
        properties = {
            weight_name = 'duration',
            max_speed_for_map_matching = 40 / 3.6, -- kmph -> m/s
            call_tagless_node_function = false,
            traffic_light_penalty = 2,
            u_turn_penalty = 2,
            continue_straight_at_waypoint = false,
            use_turn_restrictions = false,
        },
        default_mode = mode.walking,
        default_speed = walking_speed,
        oneway_handling = 'specific', -- respect 'oneway:foot' but not 'oneway'

        barrier_blacklist = Set {
            'yes',
            'wall',
            'fence'
        },
        access_tag_whitelist = Set {
            'yes',
            'foot',
            'permissive',
            'designated'
        },
        access_tag_blacklist = Set {
            'no',
            'agricultural',
            'forestry',
            'private',
            'delivery',
        },
        restricted_access_tag_list = Set {},
        restricted_highway_whitelist = Set {},
        construction_whitelist = Set {},
        access_tags_hierarchy = Sequence {
            'foot',
            'access'
        },

        -- tags disallow access to in combination with highway=service
        service_access_tag_blacklist = Set {},
        restrictions = Sequence {
            'foot'
        },

        -- list of suffixes to suppress in name change instructions
        suffix_list = Set {
            'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'North', 'South', 'West', 'East'
        },
        avoid = Set {
            'impassable'
        },
        speeds = Sequence {
            highway = {
                primary = walking_speed,
                primary_link = walking_speed,
                secondary = walking_speed,
                secondary_link = walking_speed,
                tertiary = walking_speed,
                tertiary_link = walking_speed,
                unclassified = walking_speed,
                residential = walking_speed,
                road = walking_speed,
                living_street = walking_speed,
                service = walking_speed,
                track = walking_speed,
                path = walking_speed,
                steps = walking_speed,
                pedestrian = walking_speed,
                footway = walking_speed,
                pier = walking_speed,
            },
            railway = {
                platform = walking_speed
            },
            amenity = {
                parking = walking_speed,
                parking_entrance = walking_speed
            },
            man_made = {
                pier = walking_speed
            },
            leisure = {
                track = walking_speed
            }
        },
        route_speeds = {
            ferry = 5
        },
        bridge_speeds = {},
        surface_speeds = {
            fine_gravel = walking_speed * 0.75,
            gravel = walking_speed * 0.75,
            pebblestone = walking_speed * 0.75,
            mud = walking_speed * 0.5,
            sand = walking_speed * 0.5
        },
        tracktype_speeds = {},
        smoothness_speeds = {},
    }
end

function process_node(profile, node, result)
    -- parse access and barrier tags
    local access = find_access_tag(node, profile.access_tags_hierarchy)
    if access then
        if profile.access_tag_blacklist[access] then
            result.barrier = true
        end
    else
        local barrier = node:get_value_by_key("barrier")
        if barrier then
            --  make an exception for rising bollard barriers
            local bollard = node:get_value_by_key("bollard")
            local rising_bollard = bollard and "rising" == bollard

            if profile.barrier_blacklist[barrier] and not rising_bollard then
                result.barrier = true
            end
        end
    end

    -- check if node is a traffic light
    local tag = node:get_value_by_key("highway")
    if "traffic_signals" == tag then
        result.traffic_lights = true
    end
end

-- main entry point for processing a way
function process_way(profile, way, result)
    -- the initial filtering of ways based on presence of tags
    -- affects processing times significantly, because all ways
    -- have to be checked.
    -- to increase performance, pre-fetching and initial tag checking
    -- is done in directly instead of via a handler.

    -- in general we should  try to abort as soon as
    -- possible if the way is not routable, to avoid doing
    -- unnecessary work. this implies we should check things that
    -- commonly forbids access early, and handle edge cases later.

    -- data table for storing intermediate values during processing
    local data = {
        -- prefetch tags
        highway = way:get_value_by_key('highway'),
        bridge = way:get_value_by_key('bridge'),
        route = way:get_value_by_key('route'),
        leisure = way:get_value_by_key('leisure'),
        man_made = way:get_value_by_key('man_made'),
        railway = way:get_value_by_key('railway'),
        platform = way:get_value_by_key('platform'),
        amenity = way:get_value_by_key('amenity'),
        public_transport = way:get_value_by_key('public_transport')
    }

    -- perform an quick initial check and abort if the way is
    -- obviously not routable. here we require at least one
    -- of the prefetched tags to be present, ie. the data table
    -- cannot be empty
    if next(data) == nil then
        -- is the data table empty?
        return
    end

    local handlers = Sequence {
        -- set the default mode for this profile. if can be changed later
        -- in case it turns we're e.g. on a ferry
        WayHandlers.default_mode,

        -- check various tags that could indicate that the way is not
        -- routable. this includes things like status=impassable,
        -- toll=yes and oneway=reversible
        WayHandlers.blocked_ways,

        -- determine access status by checking our hierarchy of
        -- access tags, e.g: motorcar, motor_vehicle, vehicle
        WayHandlers.access,

        -- check whether forward/backward directions are routable
        WayHandlers.oneway,

        -- check whether forward/backward directions are routable
        WayHandlers.destinations,

        -- check whether we're using a special transport mode
        WayHandlers.ferries,
        WayHandlers.movables,

        -- compute speed taking into account way type, maxspeed tags, etc.
        WayHandlers.speed,
        WayHandlers.surface,

        -- handle turn lanes and road classification, used for guidance
        WayHandlers.classification,

        -- handle various other flags
        WayHandlers.roundabouts,
        WayHandlers.startpoint,

        -- set name, ref and pronunciation
        WayHandlers.names,

        -- set weight properties of the way
        WayHandlers.weights
    }

    WayHandlers.run(profile, way, result, data, handlers)
end

function process_turn(profile, turn)
    turn.duration = 0.

    if turn.direction_modifier == direction_modifier.u_turn then
        turn.duration = turn.duration + profile.properties.u_turn_penalty
    end

    if turn.has_traffic_light then
        turn.duration = profile.properties.traffic_light_penalty
    end
    if profile.properties.weight_name == 'routability' then
        -- penalize turns from non-local access only segments onto local access only tags
        if not turn.source_restricted and turn.target_restricted then
            turn.weight = turn.weight + 3000
        end
    end
end

function process_segment(profile, segment)
    local step = 10 / 6371008.8
    local pollution_value = 0
    local distance = math.sqrt((segment.source.lon - segment.target.lon) ^ 2 +
            (segment.source.lat - segment.target.lat) ^ 2)
    local delta_lon = (segment.target.lon - segment.source.lon) / distance * step
    local delta_lat = (segment.target.lat - segment.source.lat) / distance * step
    local cd = 0
    repeat
        local current_lon = segment.source.lon + delta_lon * cd
        local current_lat = segment.source.lat + delta_lat * cd
        if current_lon >= pollution.min_longitude and current_lon <= pollution.max_longitude
                and current_lat >= pollution.min_latitude and current_lat <= pollution.max_latitude then
            pollution_value = pollution_value + raster:query(pollution.raster_data, current_lon, current_lat).datum
        end
        cd = cd + 1
    until cd > distance / step
    local old_weight = segment.weight
    segment.weight = (old_weight * pollution.weight_osrm + pollution_value * pollution.weight_pollution) / (pollution.weight_osrm + pollution.weight_pollution)
end

return {
    setup = setup,
    process_way = process_way,
    process_node = process_node,
    process_turn = process_turn,
    process_segment = process_segment
}

