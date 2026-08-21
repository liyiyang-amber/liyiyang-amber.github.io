#!/usr/bin/env ruby
# frozen_string_literal: true

# Builds the checked-in, geometry-only journey route from temporary source
# responses. The source responses are deliberately not retained in the site.
#
# Inputs expected in CACHE_DIR:
#   transit-*.json   Transitous/MOTIS public-transport responses
#   valhalla-*.json  Valhalla responses based on OpenStreetMap
#   *-aerialways.json and *-footways.json  Overpass responses
#
# Usage:
#   ruby scripts/build-swiss-dolomites-routes.rb CACHE_DIR OUTPUT.geojson

require "json"
require "pathname"

EARTH_RADIUS_METERS = 6_371_000.0
RAIL_MODES = %w[REGIONAL_RAIL LONG_DISTANCE HIGHSPEED_RAIL SUBURBAN FUNICULAR].freeze

def usage!
  warn "Usage: ruby scripts/build-swiss-dolomites-routes.rb CACHE_DIR OUTPUT.geojson"
  exit 2
end

def read_json(path)
  JSON.parse(path.read)
rescue JSON::ParserError => error
  abort "Invalid JSON in #{path}: #{error.message}"
end

def decode_polyline(value, precision = 6)
  index = 0
  latitude = 0
  longitude = 0
  scale = 10**precision
  coordinates = []

  while index < value.length
    deltas = 2.times.map do
      result = 0
      shift = 0
      loop do
        abort "Invalid encoded polyline" if index >= value.length

        byte = value.getbyte(index) - 63
        index += 1
        result |= (byte & 0x1f) << shift
        shift += 5
        break if byte < 0x20
      end
      (result & 1).positive? ? ~(result >> 1) : (result >> 1)
    end

    latitude += deltas[0]
    longitude += deltas[1]
    coordinates << [latitude.fdiv(scale), longitude.fdiv(scale)]
  end

  coordinates
end

def projected(point, reference_latitude)
  latitude, longitude = point
  radians = Math::PI / 180.0
  [
    EARTH_RADIUS_METERS * longitude * radians * Math.cos(reference_latitude * radians),
    EARTH_RADIUS_METERS * latitude * radians
  ]
end

def distance_to_segment(point, start_point, end_point)
  reference_latitude = (start_point[0] + end_point[0] + point[0]) / 3.0
  px, py = projected(point, reference_latitude)
  ax, ay = projected(start_point, reference_latitude)
  bx, by = projected(end_point, reference_latitude)
  dx = bx - ax
  dy = by - ay
  return Math.hypot(px - ax, py - ay) if dx.zero? && dy.zero?

  fraction = [[((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0.0].max, 1.0].min
  Math.hypot(px - (ax + fraction * dx), py - (ay + fraction * dy))
end

def simplify(points, tolerance)
  return points if points.length <= 2 || tolerance.zero?

  keep = Array.new(points.length, false)
  keep[0] = true
  keep[-1] = true
  stack = [[0, points.length - 1]]

  until stack.empty?
    start_index, end_index = stack.pop
    maximum_distance = 0.0
    split_index = nil
    ((start_index + 1)...end_index).each do |index|
      distance = distance_to_segment(points[index], points[start_index], points[end_index])
      next unless distance > maximum_distance

      maximum_distance = distance
      split_index = index
    end
    next unless split_index && maximum_distance > tolerance

    keep[split_index] = true
    stack << [start_index, split_index]
    stack << [split_index, end_index]
  end

  points.each_with_index.filter_map { |point, index| point if keep[index] }
end

def transit_lines(cache, name, itinerary_index = 0)
  data = read_json(cache.join("transit-#{name}.json"))
  itinerary = data.fetch("itineraries").fetch(itinerary_index)
  lines = itinerary.fetch("legs").filter_map do |leg|
    next unless RAIL_MODES.include?(leg["mode"])

    encoded = leg.dig("legGeometry", "points")
    decode_polyline(encoded) if encoded && !encoded.empty?
  end
  abort "No railway geometry found for #{name}" if lines.empty?

  lines
end

def valhalla_lines(cache, name)
  data = read_json(cache.join("valhalla-#{name}.json"))
  lines = data.dig("trip", "legs").to_a.filter_map do |leg|
    encoded = leg["shape"]
    decode_polyline(encoded) if encoded && !encoded.empty?
  end
  abort "No routed geometry found for #{name}" if lines.empty?

  lines
end

def overpass_way(cache, filename, way_ids)
  data = read_json(cache.join(filename))
  ways = data.fetch("elements").select { |element| element["type"] == "way" }.to_h { |way| [way["id"], way] }
  way_ids.map do |way_id|
    way = ways[way_id] || abort("Missing OpenStreetMap way #{way_id} in #{filename}")
    way.fetch("geometry").map { |point| [point.fetch("lat"), point.fetch("lon")] }
  end
end

def haversine(first, second)
  radians = Math::PI / 180.0
  lat1, lon1 = first.map { |value| value * radians }
  lat2, lon2 = second.map { |value| value * radians }
  delta_latitude = lat2 - lat1
  delta_longitude = lon2 - lon1
  value = Math.sin(delta_latitude / 2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(delta_longitude / 2)**2
  2 * EARTH_RADIUS_METERS * Math.asin(Math.sqrt(value))
end

def footway_graph(cache, filename)
  data = read_json(cache.join(filename))
  nodes = data.fetch("elements").select { |element| element["type"] == "node" }.to_h do |node|
    [node.fetch("id"), [node.fetch("lat"), node.fetch("lon")]]
  end
  graph = Hash.new { |hash, key| hash[key] = [] }

  data.fetch("elements").each do |element|
    next unless element["type"] == "way" && element.dig("tags", "highway")

    element.fetch("nodes").each_cons(2) do |first_id, second_id|
      next unless nodes[first_id] && nodes[second_id]

      distance = haversine(nodes[first_id], nodes[second_id])
      graph[first_id] << [second_id, distance]
      graph[second_id] << [first_id, distance]
    end
  end

  [nodes, graph]
end

def nearest_node(nodes, point)
  nodes.min_by { |_id, coordinate| haversine(coordinate, point) }.first
end

def edge_key(first_id, second_id)
  first_id < second_id ? [first_id, second_id] : [second_id, first_id]
end

def shortest_path(graph, start_id, finish_id, penalized_edges = {})
  distances = Hash.new(Float::INFINITY)
  previous = {}
  unvisited = graph.keys.to_h { |id| [id, true] }
  distances[start_id] = 0.0

  until unvisited.empty?
    current = unvisited.keys.min_by { |id| distances[id] }
    break if current.nil? || distances[current].infinite?
    break if current == finish_id

    unvisited.delete(current)
    graph[current].each do |neighbor, distance|
      next unless unvisited[neighbor]

      multiplier = penalized_edges.fetch(edge_key(current, neighbor), 1.0)
      candidate = distances[current] + distance * multiplier
      next unless candidate < distances[neighbor]

      distances[neighbor] = candidate
      previous[neighbor] = current
    end
  end

  abort "No OpenStreetMap footpath between route waypoints" unless distances[finish_id].finite?

  path = [finish_id]
  path.unshift(previous.fetch(path.first)) until path.first == start_id
  path
end

def footway_path(cache, filename, waypoint_coordinates)
  nodes, graph = footway_graph(cache, filename)
  waypoints = waypoint_coordinates.map { |point| nearest_node(nodes, point) }

  node_ids = []
  waypoints.each_cons(2) do |start_id, finish_id|
    segment = shortest_path(graph, start_id, finish_id)
    node_ids.concat(node_ids.empty? ? segment : segment.drop(1))
  end

  [node_ids.map { |node_id| nodes.fetch(node_id) }]
end

def footway_loop(cache, filename, waypoint_coordinates, return_penalty: 8.0)
  nodes, graph = footway_graph(cache, filename)
  waypoints = waypoint_coordinates.map { |point| nearest_node(nodes, point) }

  outbound = []
  waypoints.each_cons(2) do |start_id, finish_id|
    segment = shortest_path(graph, start_id, finish_id)
    outbound.concat(outbound.empty? ? segment : segment.drop(1))
  end

  used_edges = {}
  outbound.each_cons(2) { |first_id, second_id| used_edges[edge_key(first_id, second_id)] = return_penalty }
  returning = shortest_path(graph, waypoints.last, waypoints.first, used_edges)
  node_ids = outbound + returning.drop(1)
  [node_ids.map { |node_id| nodes.fetch(node_id) }]
end

def seceda_loop(cache)
  footway_loop(
    cache,
    "seceda-footways.json",
    [
      [46.5969980, 11.7277587],
      [46.6012195, 11.7356260],
      [46.5974986, 11.7477691]
    ],
    return_penalty: 8.0
  )
end

def santa_maddalena_viewpoint(cache)
  footway_path(
    cache,
    "santa-maddalena-footways.json",
    [
      [46.6414556, 11.7153339],
      [46.6447172, 11.7193166],
      [46.6481686, 11.7161156],
      [46.6465677, 11.7057504]
    ]
  )
end

def alpe_di_siusi_loop(cache)
  footway_loop(
    cache,
    "alpe-di-siusi-footways.json",
    [
      [46.5580492, 11.6647087],
      [46.5514201, 11.6513670],
      [46.5424328, 11.6455154],
      [46.5313827, 11.6253432],
      [46.5477495, 11.6282686],
      [46.5500589, 11.6465750]
    ],
    return_penalty: 2.0
  )
end

def feature(id, lines, tolerance)
  simplified = lines.map { |line| simplify(line, tolerance) }.reject { |line| line.length < 2 }
  abort "Feature #{id} has no usable geometry" if simplified.empty?

  coordinates = simplified.map do |line|
    line.map { |latitude, longitude| [longitude.round(6), latitude.round(6)] }
  end
  geometry = if coordinates.length == 1
               { "type" => "LineString", "coordinates" => coordinates.first }
             else
               { "type" => "MultiLineString", "coordinates" => coordinates }
             end
  {
    "type" => "Feature",
    "properties" => { "id" => id },
    "geometry" => geometry
  }
end

def build_features(cache)
  rail = ->(name, index = 0) { transit_lines(cache, name, index) }
  road = ->(name) { valhalla_lines(cache, name) }

  [
    feature("geneva-airport-kandersteg-rail", rail.call("gva-lausanne") + rail.call("lausanne-bern") + rail.call("bern-spiez") + rail.call("spiez-kandersteg"), 25),
    feature("kandersteg-oeschinensee-hike", road.call("kandersteg-oeschinensee"), 10),
    feature("kandersteg-spiez-rail", rail.call("spiez-kandersteg"), 25),
    feature("spiez-interlaken-rail", rail.call("spiez-interlaken", 1), 25),
    feature("interlaken-iseltwald-bus", road.call("interlaken-iseltwald"), 25),
    feature("interlaken-lauterbrunnen-rail", rail.call("interlaken-lauterbrunnen"), 25),
    feature("lauterbrunnen-grutschalp-cable", overpass_way(cache, "wengen-aerialways.json", [25_076_446]), 10),
    feature("grutschalp-murren-rail", rail.call("grutschalp-murren"), 10),
    feature("lauterbrunnen-wengen-rail", rail.call("lauterbrunnen-wengen"), 10),
    feature("wengen-mannlichen-cable", overpass_way(cache, "wengen-aerialways.json", [25_075_912]), 10),
    feature("mannlichen-kleine-scheidegg-hike", road.call("mannlichen-kleine"), 10),
    feature("kleine-scheidegg-grindelwald-rail", rail.call("kleine-grindelwald"), 10),
    feature("grindelwald-wengen-rail", rail.call("kleine-grindelwald") + rail.call("kleine-wengen"), 10),
    feature("wengen-brixen-via-zurich-rail", rail.call("lauterbrunnen-wengen") + rail.call("interlaken-lauterbrunnen") + rail.call("interlaken-bern") + rail.call("bern-zurich") + rail.call("zurich-innsbruck", 2) + rail.call("innsbruck-brixen"), 25),
    feature("brixen-lago-di-braies-road", road.call("brixen-braies"), 25),
    feature("lago-di-braies-santa-maddalena-bus", road.call("braies-santa"), 25),
    feature("santa-maddalena-viewpoint-hike", santa_maddalena_viewpoint(cache), 10),
    feature("santa-maddalena-ortisei-bus", road.call("santa-ortisei"), 25),
    feature("ortisei-seceda-cable", overpass_way(cache, "seceda-aerialways.json", [26_480_774, 48_443_865]), 10),
    feature("seceda-pieralongia-hike", seceda_loop(cache), 10),
    feature("ortisei-alpe-di-siusi-cable", overpass_way(cache, "alpe-aerialways.json", [35_091_509]), 10),
    feature("alpe-di-siusi-loop-hike", alpe_di_siusi_loop(cache), 10),
    feature("ortisei-bolzano-bus", road.call("ortisei-bolzano"), 25),
    feature("bolzano-munich-airport-rail", rail.call("bolzano-innsbruck") + rail.call("innsbruck-munich", 2) + rail.call("munich-hbf-ost", 4) + rail.call("munich-ost-airport"), 25)
  ]
end

def write_collection(features, output)
  ids = features.map { |item| item.dig("properties", "id") }
  abort "Generated duplicate feature IDs" unless ids.uniq.length == ids.length

  output.dirname.mkpath
  output.write(JSON.generate({ "type" => "FeatureCollection", "features" => features }))
  puts "Wrote #{output} (#{features.length} features, #{output.size} bytes)"
end

if $PROGRAM_NAME == __FILE__
  usage! unless ARGV.length == 2

  cache = Pathname.new(File.expand_path(ARGV[0], Dir.pwd))
  output = Pathname.new(File.expand_path(ARGV[1], Dir.pwd))
  abort "Cache directory does not exist: #{cache}" unless cache.directory?

  write_collection(build_features(cache), output)
end
