#!/usr/bin/env ruby
# Validate the optional page link and the reusable inline fallback without editing source pages.
require "date"
require "yaml"
require "json"
require "open3"
require "tmpdir"
require "jekyll"

root = File.expand_path("..", __dir__)
source = File.read(File.join(root, "_travel/swiss+dolomites.md"), encoding: "UTF-8")
data = YAML.safe_load(source.split(/^---\s*$/)[1], permitted_classes: [Date, Time], aliases: true)
cases = {
  "linked" => ["/memories/swiss-dolomites/video/", true],
  "inline" => [:omit, true],
  "external" => ["https://example.com/video/", false],
  "protocol-relative" => ["//example.com/video/", false],
  "missing-page" => ["/memories/missing-video/", false],
  "wrong-layout" => ["/memories/", false],
  "fragment" => ["/memories/swiss-dolomites/video/#player", false],
  "invalid-type" => [true, false]
}
Dir.mktmpdir("journey-video-validation-", "/private/tmp") do |directory|
  cases.each do |name, (value, expected)|
    fixture = Marshal.load(Marshal.dump(data))
    if value == :omit
      fixture["journey"]["overview"].delete("page_url")
    else
      fixture["journey"]["overview"]["page_url"] = value
    end
    file = File.join(directory, "#{name}.md")
    File.write(file, "---\n#{JSON.generate(fixture)}\n---\n")
    stdout, stderr, status = Open3.capture3("ruby", File.join(root, "scripts/validate-travel-journey.rb"), file)
    raise "#{name}: #{stdout} #{stderr}" unless status.success? == expected
    raise "Wrong validation error: #{stderr}" if !expected && !stderr.include?("journey.overview.page_url")
  end
end

# Render in memory, not into _site, to verify other journeys retain the inline player.
site = Jekyll::Site.new(Jekyll.configuration("source" => root, "quiet" => true))
site.reset
site.read
site.generate
journey = site.collections["travel"].docs.find { |doc| doc.data["permalink"] == data["permalink"] }
raise "Source journey missing" unless journey
journey.data["journey"]["overview"].delete("page_url")
site.render
raise "Inline fallback lost its video" unless journey.output.include?("<video data-travel-overview")
raise "Inline fallback lost playback script" unless journey.output.include?("/assets/js/travel-overview.js")
raise "Inline fallback unexpectedly links away" if journey.output.include?("Click to see the overview route video")
puts "JOURNEY_VIDEO_PAGE_TESTS_OK: 8 link-validation cases and inline player fallback"
