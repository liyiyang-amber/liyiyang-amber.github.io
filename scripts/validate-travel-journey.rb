#!/usr/bin/env ruby
# frozen_string_literal: true

require "date"
require "json"
require "pathname"
require "uri"
require "yaml"

ROOT = Pathname.new(File.expand_path("..", __dir__))
CONTENT_STATUSES = %w[itinerary complete].freeze
REQUIRED_JOURNEY_FIELDS = %w[content_status eyebrow period days places].freeze
REQUIRED_DAY_FIELDS = %w[id date place_ids].freeze
REQUIRED_PLACE_FIELDS = %w[id name latitude longitude].freeze
REQUIRED_COMPLETE_PLACE_FIELDS = %w[excerpt cover cover_alt journal photos].freeze
REQUIRED_PHOTO_FIELDS = %w[thumb medium full alt caption captured_on].freeze
ROUTE_MODES = %w[rail cable_car bus rideshare hike].freeze
ROUTE_STATUSES = %w[mapped not_mapped].freeze
ASCII_SLUG = /\A[a-z0-9]+(?:-[a-z0-9]+)*\z/

def load_front_matter(path)
  source = File.read(path, encoding: "UTF-8")
  match = source.match(/\A---\s*\n(.*?)\n---\s*(?:\n|\z)/m)
  raise "missing YAML front matter" unless match

  YAML.safe_load(match[1], permitted_classes: [Date, Time], aliases: true) || {}
end

def present?(value)
  !value.nil? && !(value.respond_to?(:empty?) && value.empty?)
end

def date_value(value)
  return value if value.is_a?(Date)
  return value.to_date if value.respond_to?(:to_date)

  Date.iso8601(value.to_s)
rescue Date::Error
  nil
end

def local_asset_path(value)
  return nil unless value.is_a?(String)
  return nil if value.include?("://")

  ROOT.join(value.sub(%r{\A/}, ""))
end

def archive_image_path(value)
  return nil unless value.is_a?(String)
  return nil if value.include?("://")

  normalized = value.sub(%r{\A/}, "")
  normalized = "images/#{normalized}" unless normalized.start_with?("images/")
  ROOT.join(normalized)
end

def validate_asset(value, label, errors)
  path = local_asset_path(value)
  if path.nil?
    errors << "#{label} must be a local path"
  elsif !path.file?
    errors << "#{label} does not exist: #{value}"
  end
end

def coordinate?(value)
  number = Float(value, exception: false)
  number&.finite?
end

def line_coordinates?(coordinates)
  coordinates.is_a?(Array) && coordinates.length >= 2 && coordinates.all? do |coordinate|
    coordinate.is_a?(Array) && coordinate.length >= 2 &&
      coordinate?(coordinate[0]) && coordinate?(coordinate[1]) &&
      Float(coordinate[0]).between?(-180, 180) && Float(coordinate[1]).between?(-90, 90)
  end
end

def route_geometry?(object)
  return false unless object.is_a?(Hash)

  case object["type"]
  when "LineString"
    line_coordinates?(object["coordinates"])
  when "MultiLineString"
    coordinates = object["coordinates"]
    coordinates.is_a?(Array) && !coordinates.empty? && coordinates.all? { |line| line_coordinates?(line) }
  when "Feature"
    route_geometry?(object["geometry"])
  when "FeatureCollection"
    features = object["features"]
    features.is_a?(Array) && !features.empty? && features.all? { |feature| route_geometry?(feature) }
  else
    false
  end
end

def https_url?(value)
  return false unless value.is_a?(String)

  uri = URI.parse(value)
  uri.scheme == "https" && present?(uri.host)
rescue URI::InvalidURIError
  false
end

def validate_slug(value, label, ids, errors)
  unless value.is_a?(String) && value.match?(ASCII_SLUG)
    errors << "#{label} must be an ASCII lowercase slug" if present?(value)
    return
  end

  errors << "#{label} is duplicated: #{value}" if ids[value]
  ids[value] = true
end

def validate_route(value, required, layered, errors)
  unless present?(value)
    errors << "journey.route_geojson is required when route geometry is enabled" if required
    return {}
  end

  route_path = local_asset_path(value)
  if route_path.nil? || !route_path.file?
    errors << "journey.route_geojson must reference an existing local file"
    return {}
  end

  route = JSON.parse(route_path.read)
  unless route_geometry?(route)
    errors << "journey.route_geojson must contain valid finite LineString or MultiLineString geometry"
    return {}
  end
  return {} unless layered

  unless route["type"] == "FeatureCollection"
    errors << "journey.route_geojson must be a FeatureCollection when route_legs are present"
    return {}
  end

  feature_ids = {}
  route.fetch("features", []).each_with_index do |feature, index|
    label = "journey.route_geojson.features[#{index}]"
    properties = feature["properties"]
    unless properties.is_a?(Hash) && properties.keys == ["id"]
      errors << "#{label}.properties must contain only id"
      next
    end
    validate_slug(properties["id"], "#{label}.properties.id", feature_ids, errors)
  end
  feature_ids
rescue JSON::ParserError => error
  errors << "journey.route_geojson is invalid JSON: #{error.message}"
  {}
end

def validate_route_legs(route_legs, day_ids, feature_ids, errors)
  unless route_legs.is_a?(Array) && !route_legs.empty?
    errors << "journey.route_legs must contain at least one route leg"
    return
  end

  route_ids = {}
  referenced_features = {}
  feature_modes = {}
  previous_sequence = {}
  route_legs.each_with_index do |route_leg, index|
    label = "journey.route_legs[#{index}]"
    unless route_leg.is_a?(Hash)
      errors << "#{label} must be a mapping"
      next
    end

    %w[id day_id sequence label status].each do |field|
      errors << "#{label}.#{field} is required" unless present?(route_leg[field])
    end
    validate_slug(route_leg["id"], "#{label}.id", route_ids, errors)

    day_id = route_leg["day_id"]
    errors << "#{label}.day_id references unknown day: #{day_id}" if present?(day_id) && !day_ids[day_id]
    sequence = Integer(route_leg["sequence"], exception: false)
    if sequence.nil? || sequence <= 0
      errors << "#{label}.sequence must be a positive integer"
    elsif previous_sequence[day_id] && sequence <= previous_sequence[day_id]
      errors << "#{label}.sequence must be strictly increasing within #{day_id}"
    else
      previous_sequence[day_id] = sequence
    end

    status = route_leg["status"]
    errors << "#{label}.status must be mapped or not_mapped" unless ROUTE_STATUSES.include?(status)
    validate_mapped_route_leg(route_leg, label, feature_ids, referenced_features, feature_modes, errors) if status == "mapped"
    validate_unmapped_route_leg(route_leg, label, errors) if status == "not_mapped"

    %w[external_url context_url].each do |field|
      next unless present?(route_leg[field])

      errors << "#{label}.#{field} must be an HTTPS URL" unless https_url?(route_leg[field])
    end
    if present?(route_leg["external_url"]) != present?(route_leg["external_label"])
      errors << "#{label}.external_url and external_label must be provided together"
    end
  end

  feature_ids.each_key do |feature_id|
    unless referenced_features[feature_id]
      errors << "journey.route_geojson feature is not referenced by route_legs: #{feature_id}"
    end
  end
end

def validate_mapped_route_leg(route_leg, label, feature_ids, referenced_features, feature_modes, errors)
  mode = route_leg["mode"]
  errors << "#{label}.mode must be one of #{ROUTE_MODES.join(', ')}" unless ROUTE_MODES.include?(mode)
  %w[feature_id source_label source_url].each do |field|
    errors << "#{label}.#{field} is required for mapped routes" unless present?(route_leg[field])
  end

  feature_id = route_leg["feature_id"]
  unless feature_id.is_a?(String) && feature_id.match?(ASCII_SLUG)
    errors << "#{label}.feature_id must be an ASCII lowercase slug"
    return
  end

  errors << "#{label}.feature_id references unknown geometry: #{feature_id}" unless feature_ids[feature_id]
  referenced_features[feature_id] = true
  if feature_modes[feature_id] && feature_modes[feature_id] != mode
    errors << "#{label}.mode conflicts with another leg using #{feature_id}"
  end
  feature_modes[feature_id] = mode
  errors << "#{label}.source_url must be an HTTPS URL" unless https_url?(route_leg["source_url"])
end

def validate_unmapped_route_leg(route_leg, label, errors)
  errors << "#{label}.feature_id must be omitted for not_mapped routes" if present?(route_leg["feature_id"])
  errors << "#{label}.mode must be omitted for not_mapped routes" if present?(route_leg["mode"])
  errors << "#{label}.note is required for not_mapped routes" unless present?(route_leg["note"])
end

def validate_archive_image(data, required, errors)
  value = data.dig("header", "overlay_image")
  unless present?(value)
    errors << "header.overlay_image is required in complete mode" if required
    return
  end

  path = archive_image_path(value)
  if path.nil?
    errors << "header.overlay_image must be a local path"
  elsif !path.file?
    errors << "header.overlay_image does not exist: #{value}"
  end
end

def validate_photos(photos, label, required, errors)
  unless photos.is_a?(Array) && !photos.empty?
    errors << "#{label}.photos must contain at least one photo" if required || present?(photos)
    return
  end

  photos.each_with_index do |photo, photo_index|
    photo_label = "#{label}.photos[#{photo_index}]"
    unless photo.is_a?(Hash)
      errors << "#{photo_label} must be a mapping"
      next
    end

    REQUIRED_PHOTO_FIELDS.each do |field|
      errors << "#{photo_label}.#{field} is required" unless present?(photo[field])
    end
    %w[thumb medium full].each do |field|
      validate_asset(photo[field], "#{photo_label}.#{field}", errors) if present?(photo[field])
    end
    if present?(photo["captured_on"]) && date_value(photo["captured_on"]).nil?
      errors << "#{photo_label}.captured_on must be an ISO date"
    end
  end
end

def validate_page(path)
  data = load_front_matter(path)
  return [:ignored, []] unless data["layout"] == "travel-journey"
  return [:unpublished, []] if data["published"] == false

  errors = []
  %w[title permalink date].each do |field|
    errors << "missing #{field}" unless present?(data[field])
  end

  journey = data["journey"]
  unless journey.is_a?(Hash)
    return [:invalid, errors << "journey must be a mapping"]
  end

  REQUIRED_JOURNEY_FIELDS.each do |field|
    errors << "journey.#{field} is required" unless present?(journey[field])
  end

  status = journey["content_status"]
  errors << "journey.content_status must be itinerary or complete" unless CONTENT_STATUSES.include?(status)
  complete = status == "complete"

  days = journey["days"]
  places = journey["places"]
  unless days.is_a?(Array) && !days.empty?
    return [:invalid, errors << "journey.days must contain at least one day"]
  end
  unless places.is_a?(Array) && !places.empty?
    return [:invalid, errors << "journey.places must contain at least one place"]
  end

  day_ids = {}
  referenced_place_ids = []
  previous_date = nil
  first_date = nil
  days.each_with_index do |day, day_index|
    label = "journey.days[#{day_index}]"
    unless day.is_a?(Hash)
      errors << "#{label} must be a mapping"
      next
    end

    REQUIRED_DAY_FIELDS.each do |field|
      errors << "#{label}.#{field} is required" unless present?(day[field])
    end
    validate_slug(day["id"], "#{label}.id", day_ids, errors)

    date = date_value(day["date"])
    if date.nil?
      errors << "#{label}.date must be an ISO date"
    else
      first_date ||= date
      errors << "#{label}.date must be later than the previous day" if previous_date && date <= previous_date
      previous_date = date
    end

    place_ids = day["place_ids"]
    unless place_ids.is_a?(Array) && !place_ids.empty?
      errors << "#{label}.place_ids must contain at least one place ID"
      next
    end
    place_ids.each_with_index do |place_id, place_index|
      unless place_id.is_a?(String) && place_id.match?(ASCII_SLUG)
        errors << "#{label}.place_ids[#{place_index}] must be an ASCII lowercase slug"
      end
      referenced_place_ids << [place_id, "#{label}.place_ids[#{place_index}]"]
    end
  end

  page_date = date_value(data["date"])
  if page_date && first_date && page_date != first_date
    errors << "page date must match the first journey day"
  end

  place_ids = {}
  places.each_with_index do |place, place_index|
    label = "journey.places[#{place_index}]"
    unless place.is_a?(Hash)
      errors << "#{label} must be a mapping"
      next
    end

    REQUIRED_PLACE_FIELDS.each do |field|
      errors << "#{label}.#{field} is required" unless present?(place[field])
    end
    REQUIRED_COMPLETE_PLACE_FIELDS.each do |field|
      errors << "#{label}.#{field} is required in complete mode" if complete && !present?(place[field])
    end
    validate_slug(place["id"], "#{label}.id", place_ids, errors)

    latitude = Float(place["latitude"], exception: false)
    longitude = Float(place["longitude"], exception: false)
    errors << "#{label}.latitude must be between -90 and 90" unless latitude&.between?(-90, 90)
    errors << "#{label}.longitude must be between -180 and 180" unless longitude&.between?(-180, 180)

    if !complete && present?(place["cover"]) && !present?(place["cover_alt"])
      errors << "#{label}.cover_alt is required when cover is present"
    end
    validate_asset(place["cover"], "#{label}.cover", errors) if present?(place["cover"])
    validate_photos(place["photos"], label, complete, errors) if complete || !place["photos"].nil?
  end

  referenced_place_ids.each do |place_id, label|
    errors << "#{label} references unknown place: #{place_id}" unless place_ids[place_id]
  end

  route_legs = journey["route_legs"]
  layered_routes = present?(route_legs)
  feature_ids = validate_route(journey["route_geojson"], complete || layered_routes, layered_routes, errors)
  validate_route_legs(route_legs, day_ids, feature_ids, errors) if layered_routes
  validate_archive_image(data, complete, errors)

  [errors.empty? ? :valid : :invalid, errors]
rescue StandardError => error
  [:invalid, [error.message]]
end

paths = if ARGV.empty?
          ROOT.glob("_travel/*.{md,markdown}")
        else
          ARGV.map { |argument| Pathname.new(File.expand_path(argument, Dir.pwd)) }
        end

failed = false
checked = 0
paths.sort.each do |path|
  state, errors = validate_page(path)
  next if state == :ignored

  checked += 1
  case state
  when :valid
    puts "OK   #{path.relative_path_from(ROOT)}"
  when :unpublished
    puts "SKIP #{path.relative_path_from(ROOT)} (unpublished)"
  else
    failed = true
    warn "FAIL #{path.relative_path_from(ROOT)}"
    errors.each { |error| warn "  - #{error}" }
  end
end

warn "No travel-journey pages found" if checked.zero?
exit(failed ? 1 : 0)
