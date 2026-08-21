#!/usr/bin/env ruby
# frozen_string_literal: true

require "date"
require "json"
require "open3"
require "optparse"
require "pathname"
require "yaml"

WIDTHS = [480, 960, 1600].freeze
SUPPORTED_EXTENSIONS = %w[.jpg .jpeg .png .heic .heif .webp .tif .tiff].freeze

options = { date_overrides: nil }
parser = OptionParser.new do |config|
  config.banner = "Usage: ruby scripts/prepare-travel-photos.rb SOURCE_DIR OUTPUT_DIR [URL_PREFIX] [--date-overrides FILE]"
  config.on("--date-overrides FILE", "YAML mapping of source filenames or slugs to ISO capture dates") do |file|
    options[:date_overrides] = file
  end
end
parser.parse!(ARGV)

unless (2..3).cover?(ARGV.length)
  warn parser
  exit 2
end

def slug_for(path)
  path.basename(path.extname).to_s
      .downcase
      .gsub(/[^a-z0-9]+/, "-")
      .gsub(/\A-+|-+\z/, "")
end

def normalize_date(value)
  return value.strftime("%Y-%m-%d") if value.is_a?(Date) || value.is_a?(Time)

  match = value.to_s.match(/(\d{4})[:-](\d{2})[:-](\d{2})/)
  return nil unless match

  Date.new(match[1].to_i, match[2].to_i, match[3].to_i).iso8601
rescue Date::Error
  nil
end

def sips_capture_date(source)
  output, status = Open3.capture2e("sips", "-g", "creation", source.to_s)
  return nil unless status.success?

  line = output.lines.find { |candidate| candidate.strip.start_with?("creation:") }
  normalize_date(line&.split(":", 2)&.last)
rescue Errno::ENOENT
  nil
end

def ffprobe_capture_date(source)
  fields = "stream_tags=DateTimeOriginal,date_time_original,creation_time:" \
           "format_tags=DateTimeOriginal,date_time_original,creation_time"
  output, _errors, status = Open3.capture3(
    "ffprobe", "-v", "error", "-select_streams", "v:0",
    "-show_entries", fields, "-of", "json", source.to_s
  )
  return nil unless status.success?

  metadata = JSON.parse(output)
  tag_sets = Array(metadata["streams"]).map { |stream| stream["tags"] }
  tag_sets << metadata.dig("format", "tags")
  tag_sets.compact.each do |tags|
    tags.each do |key, value|
      normalized_key = key.downcase.delete("_")
      next unless %w[datetimeoriginal creationtime].include?(normalized_key)

      date = normalize_date(value)
      return date if date
    end
  end
  nil
rescue Errno::ENOENT, JSON::ParserError
  nil
end

def load_overrides(path)
  return {} unless path

  override_path = Pathname.new(File.expand_path(path, Dir.pwd))
  abort "Date override file does not exist: #{override_path}" unless override_path.file?
  data = YAML.safe_load(override_path.read, permitted_classes: [Date, Time], aliases: false)
  abort "Date override file must contain a YAML mapping" unless data.is_a?(Hash)

  data.each_with_object({}) do |(key, value), overrides|
    date = normalize_date(value)
    abort "Invalid date override for #{key}: #{value}" unless date

    overrides[key.to_s] = date
  end
end

def capture_date_for(source, slug, overrides)
  override = overrides[source.basename.to_s] || overrides[source.basename(source.extname).to_s] || overrides[slug]
  return override if override

  sips_capture_date(source) || ffprobe_capture_date(source)
end

source_directory = Pathname.new(File.expand_path(ARGV[0], Dir.pwd))
output_directory = Pathname.new(File.expand_path(ARGV[1], Dir.pwd))
url_prefix = (ARGV[2] || "/images/memories/swiss-dolomites").sub(%r{/+\z}, "")
date_overrides = load_overrides(options[:date_overrides])

abort "Source directory does not exist: #{source_directory}" unless source_directory.directory?
abort "Source and output directories must differ" if source_directory == output_directory

_stdout, _stderr, status = Open3.capture3("ffmpeg", "-version")
abort "ffmpeg is required to prepare photos" unless status.success?

sources = source_directory.children.select do |path|
  path.file? && SUPPORTED_EXTENSIONS.include?(path.extname.downcase)
end.sort
abort "No supported photos found in #{source_directory}" if sources.empty?

slugs = {}
capture_dates = {}
sources.each do |source|
  slug = slug_for(source)
  abort "Filename cannot produce an ASCII slug: #{source.basename}" if slug.empty?
  abort "Duplicate output slug '#{slug}' from #{source.basename} and #{slugs[slug].basename}" if slugs[slug]

  capture_date = capture_date_for(source, slug, date_overrides)
  abort "No EXIF capture date for #{source.basename}; add it to --date-overrides" unless capture_date

  slugs[slug] = source
  capture_dates[slug] = capture_date
end

output_directory.mkpath
sources.each do |source|
  slug = slug_for(source)
  WIDTHS.each do |width|
    output = output_directory.join("#{slug}-#{width}.webp")
    abort "Refusing to overwrite existing output: #{output}" if output.exist?

    filter = "scale='min(#{width},iw)':-2:flags=lanczos"
    command = [
      "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
      "-i", source.to_s, "-map_metadata", "-1", "-frames:v", "1", "-an",
      "-vf", filter, "-c:v", "libwebp", "-quality", "82", "-compression_level", "6",
      output.to_s
    ]
    success = system(*command)
    abort "Photo conversion failed for #{source.basename} at #{width}px" unless success
  end

  puts <<~YAML
    - thumb: #{url_prefix}/#{slug}-480.webp
      medium: #{url_prefix}/#{slug}-960.webp
      full: #{url_prefix}/#{slug}-1600.webp
      alt: ""
      caption: ""
      captured_on: #{capture_dates[slug]}
  YAML
end
