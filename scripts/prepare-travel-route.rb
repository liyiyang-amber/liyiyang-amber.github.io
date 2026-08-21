#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require "rexml/document"

EARTH_RADIUS_METERS = 6_371_000.0

def usage!
  warn <<~USAGE
    Usage:
      ruby scripts/prepare-travel-route.rb INPUT.gpx OUTPUT.geojson [TOLERANCE_METERS]
      ruby scripts/prepare-travel-route.rb --collection OUTPUT.geojson ID=INPUT[@TOLERANCE] [...]
  USAGE
  exit 2
end

def valid_coordinate?(latitude, longitude)
  latitude&.between?(-90.0, 90.0) && longitude&.between?(-180.0, 180.0)
end

def points_from(element, point_name)
  points = []
  element.each_element(".//*") do |child|
    next unless child.name.split(":").last == point_name

    latitude = Float(child.attributes["lat"], exception: false)
    longitude = Float(child.attributes["lon"], exception: false)
    raise "Invalid GPX coordinate" unless valid_coordinate?(latitude, longitude)

    points << [latitude, longitude]
  end
  points
end

def project(point, reference_latitude)
  latitude, longitude = point
  radians = Math::PI / 180.0
  x = EARTH_RADIUS_METERS * longitude * radians * Math.cos(reference_latitude * radians)
  y = EARTH_RADIUS_METERS * latitude * radians
  [x, y]
end

def distance_to_segment(point, start_point, end_point)
  reference_latitude = (start_point[0] + end_point[0] + point[0]) / 3.0
  px, py = project(point, reference_latitude)
  ax, ay = project(start_point, reference_latitude)
  bx, by = project(end_point, reference_latitude)
  dx = bx - ax
  dy = by - ay
  return Math.hypot(px - ax, py - ay) if dx.zero? && dy.zero?

  fraction = [[((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy), 0.0].max, 1.0].min
  nearest_x = ax + fraction * dx
  nearest_y = ay + fraction * dy
  Math.hypot(px - nearest_x, py - nearest_y)
end

def simplify(points, tolerance)
  return points if points.length <= 2

  maximum_distance = 0.0
  split_index = nil
  points[1...-1].each_with_index do |point, offset|
    distance = distance_to_segment(point, points.first, points.last)
    next unless distance > maximum_distance

    maximum_distance = distance
    split_index = offset + 1
  end

  return [points.first, points.last] if maximum_distance <= tolerance || split_index.nil?

  left = simplify(points[0..split_index], tolerance)
  right = simplify(points[split_index..], tolerance)
  left[0...-1] + right
end

def gpx_segments(path)
  document = REXML::Document.new(path.read)
  segments = []

  document.each_element("//*") do |element|
    next unless element.name.split(":").last == "trkseg"

    points = points_from(element, "trkpt")
    segments << points if points.length >= 2
  end

  if segments.empty?
    route_points = []
    document.each_element("//*") do |element|
      next unless element.name.split(":").last == "rtept"

      latitude = Float(element.attributes["lat"], exception: false)
      longitude = Float(element.attributes["lon"], exception: false)
      raise "Invalid GPX route coordinate" unless valid_coordinate?(latitude, longitude)

      route_points << [latitude, longitude]
    end
    segments << route_points if route_points.length >= 2
  end

  segments
end


def geojson_segments(object)
  return [] unless object.is_a?(Hash)

  case object["type"]
  when "FeatureCollection"
    object.fetch("features", []).flat_map { |feature| geojson_segments(feature) }
  when "Feature"
    geojson_segments(object["geometry"])
  when "LineString"
    [object.fetch("coordinates").map { |longitude, latitude| [latitude, longitude] }]
  when "MultiLineString"
    object.fetch("coordinates").map do |line|
      line.map { |longitude, latitude| [latitude, longitude] }
    end
  else
    []
  end
end


def source_segments(path)
  case path.extname.downcase
  when ".gpx"
    gpx_segments(path)
  when ".geojson", ".json"
    geojson_segments(JSON.parse(path.read))
  else
    raise "Unsupported route input: #{path}"
  end
rescue JSON::ParserError => error
  raise "Invalid GeoJSON in #{path}: #{error.message}"
end


def geometry_for(segments, tolerance)
  simplified = segments.map { |segment| simplify(segment, tolerance) }.reject { |segment| segment.length < 2 }
  raise "No track or route segment with at least two points was found" if simplified.empty?

  coordinates = simplified.map do |segment|
    segment.map { |latitude, longitude| [longitude.round(6), latitude.round(6)] }
  end
  if coordinates.length == 1
    { "type" => "LineString", "coordinates" => coordinates.first }
  else
    { "type" => "MultiLineString", "coordinates" => coordinates }
  end
end


def write_geojson(output, object)
  abort "Refusing to overwrite existing output: #{output}" if output.exist?

  output.dirname.mkpath
  output.write(JSON.generate(object))
  puts "Wrote #{output}"
end


if ARGV.first == "--collection"
  usage! unless ARGV.length >= 3

  output = Pathname.new(File.expand_path(ARGV[1], Dir.pwd))
  ids = {}
  features = ARGV.drop(2).map do |specification|
    match = specification.match(/\A([a-z0-9]+(?:-[a-z0-9]+)*)=(.+?)(?:@([0-9]+(?:\.[0-9]+)?))?\z/)
    abort "Invalid collection input: #{specification}" unless match

    id = match[1]
    abort "Duplicate feature ID: #{id}" if ids[id]
    ids[id] = true
    input = Pathname.new(File.expand_path(match[2], Dir.pwd))
    tolerance = Float(match[3] || "25", exception: false)
    abort "Input route does not exist: #{input}" unless input.file?
    abort "Tolerance must be a non-negative number" unless tolerance && tolerance >= 0

    {
      "type" => "Feature",
      "properties" => { "id" => id },
      "geometry" => geometry_for(source_segments(input), tolerance)
    }
  end

  write_geojson(output, { "type" => "FeatureCollection", "features" => features })
  exit
end


usage! unless (2..3).cover?(ARGV.length)

input = Pathname.new(File.expand_path(ARGV[0], Dir.pwd))
output = Pathname.new(File.expand_path(ARGV[1], Dir.pwd))
tolerance = Float(ARGV[2] || "25", exception: false)
abort "Input GPX does not exist: #{input}" unless input.file?
abort "Tolerance must be a non-negative number" unless tolerance && tolerance >= 0

segments = gpx_segments(input)
abort "No GPX track or route segment with at least two points was found" if segments.empty?

write_geojson(
  output,
  {
    "type" => "Feature",
    "properties" => {},
    "geometry" => geometry_for(segments, tolerance)
  }
)
