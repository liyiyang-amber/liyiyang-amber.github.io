---
title: "Swiss and Dolomites Travel Log"
layout: travel-journey
author_profile: true
excerpt: "'Almost heaven, Alpine heights,<br>
Where the glaciers drown the sun in light.<br>
Life is old there, older than the trees,<br> 
Younger than the heartache freezing in the breeze.'"
permalink: /memories/swiss-dolomites/
date: 2024-06-15
header:
  overlay_image: covers/Swissdo_cover.jpg
  overlay_filter: 0.25

journey:
  content_status: itinerary
  eyebrow: Switzerland & the Dolomites
  period: June 15–24, 2024
  route_geojson: /assets/data/travel/swiss-dolomites-routes.geojson
  route_legs:
    - id: day-01-geneva-kandersteg
      day_id: day-01
      sequence: 1
      feature_id: geneva-airport-kandersteg-rail
      mode: rail
      label: Geneva Airport → Kandersteg via Lausanne, Bern, and Spiez
      source_label: Physical railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-02-oeschinensee-hike
      day_id: day-02
      sequence: 1
      feature_id: kandersteg-oeschinensee-hike
      mode: hike
      label: Kandersteg ↔ Oeschinensee
      source_label: Trail reconstructed from OpenStreetMap; AllTrails supplied as the itinerary reference
      source_url: https://www.openstreetmap.org/copyright
      external_label: View the referenced hike on AllTrails
      external_url: https://www.alltrails.com/trail/switzerland/bern/oeschinensee-kandersteg
      status: mapped
      note: The map shows the shared hiking corridor once for the outward and return journey.
    - id: day-03-kandersteg-spiez
      day_id: day-03
      sequence: 1
      feature_id: kandersteg-spiez-rail
      mode: rail
      label: Kandersteg → Spiez
      source_label: Physical railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-03-spiez-interlaken
      day_id: day-03
      sequence: 2
      feature_id: spiez-interlaken-rail
      mode: rail
      label: Spiez → Interlaken Ost
      source_label: Physical railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-03-iseltwald-round-trip
      day_id: day-03
      sequence: 3
      feature_id: interlaken-iseltwald-bus
      mode: bus
      label: Interlaken Ost ↔ Iseltwald
      source_label: Road path reconstructed from OpenStreetMap
      source_url: https://www.openstreetmap.org/copyright
      status: mapped
    - id: day-03-interlaken-lauterbrunnen
      day_id: day-03
      sequence: 4
      feature_id: interlaken-lauterbrunnen-rail
      mode: rail
      label: Interlaken Ost → Lauterbrunnen
      source_label: Physical railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-03-lauterbrunnen-grutschalp
      day_id: day-03
      sequence: 5
      feature_id: lauterbrunnen-grutschalp-cable
      mode: cable_car
      label: Lauterbrunnen → Grütschalp
      source_label: Official Lauterbrunnen–Mürren connection; cableway geometry from OpenStreetMap
      source_url: https://www.jungfrau.ch/en-gb/arrival-at-station-car-parks/valley-stations/blm-valley-station/
      status: mapped
    - id: day-03-grutschalp-murren
      day_id: day-03
      sequence: 6
      feature_id: grutschalp-murren-rail
      mode: rail
      label: Grütschalp → Mürren
      source_label: Physical mountain-railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-03-murren-grutschalp
      day_id: day-03
      sequence: 7
      feature_id: grutschalp-murren-rail
      mode: rail
      label: Mürren → Grütschalp
      source_label: Physical mountain-railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-03-grutschalp-lauterbrunnen
      day_id: day-03
      sequence: 8
      feature_id: lauterbrunnen-grutschalp-cable
      mode: cable_car
      label: Grütschalp → Lauterbrunnen
      source_label: Official Lauterbrunnen–Mürren connection; cableway geometry from OpenStreetMap
      source_url: https://www.jungfrau.ch/en-gb/arrival-at-station-car-parks/valley-stations/blm-valley-station/
      status: mapped
    - id: day-03-lauterbrunnen-wengen
      day_id: day-03
      sequence: 9
      feature_id: lauterbrunnen-wengen-rail
      mode: rail
      label: Lauterbrunnen → Wengen
      source_label: Physical mountain-railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-04-wengen-mannlichen
      day_id: day-04
      sequence: 1
      feature_id: wengen-mannlichen-cable
      mode: cable_car
      label: Wengen → Männlichen
      source_label: Official Wengen–Männlichen cableway; geometry from OpenStreetMap
      source_url: https://www.maennlichen.ch/en/summer/experiences/royal-ride.html
      status: mapped
    - id: day-04-mannlichen-hike
      day_id: day-04
      sequence: 2
      feature_id: mannlichen-kleine-scheidegg-hike
      mode: hike
      label: Männlichen → Kleine Scheidegg
      source_label: Trail reconstructed from OpenStreetMap; AllTrails supplied as the itinerary reference
      source_url: https://www.openstreetmap.org/copyright
      external_label: View the referenced hike on AllTrails
      external_url: https://www.alltrails.com/trail/switzerland/bern/panoramaweg-mannlichen-kleine-scheidegg
      status: mapped
      note: Kleine Scheidegg is a route endpoint, not a numbered journey place.
    - id: day-04-kleine-scheidegg-grindelwald
      day_id: day-04
      sequence: 3
      feature_id: kleine-scheidegg-grindelwald-rail
      mode: rail
      label: Kleine Scheidegg → Grindelwald
      source_label: Physical mountain-railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-04-grindelwald-wengen
      day_id: day-04
      sequence: 4
      feature_id: grindelwald-wengen-rail
      mode: rail
      label: Grindelwald → Wengen via Kleine Scheidegg
      source_label: Physical mountain-railway alignment checked against the Swiss federal railway network
      source_url: https://www.bav.admin.ch/de/schienennetz-id-981
      status: mapped
    - id: day-05-wengen-brixen
      day_id: day-05
      sequence: 1
      feature_id: wengen-brixen-via-zurich-rail
      mode: rail
      label: Wengen → Brixen via Bern, Zürich, Innsbruck, and Brenner
      source_label: Physical public-transport railway shapes from open European timetable data
      source_url: https://transitous.org/sources/
      status: mapped
      note: The line represents railway alignment, not verified June 2024 train numbers.
    - id: day-06-brixen-braies
      day_id: day-06
      sequence: 1
      feature_id: brixen-lago-di-braies-road
      mode: rideshare
      label: Brixen → Lago di Braies by Uber
      source_label: Road path reconstructed from OpenStreetMap
      source_url: https://www.openstreetmap.org/copyright
      status: mapped
    - id: day-06-braies-santa-maddalena
      day_id: day-06
      sequence: 2
      feature_id: lago-di-braies-santa-maddalena-bus
      mode: bus
      label: Lago di Braies → Santa Maddalena, Val di Funes
      source_label: Named-place bus connector reconstructed on OpenStreetMap roads
      source_url: https://www.openstreetmap.org/copyright
      context_url: https://www.suedtirolmobil.info/en/my-journey/network-maps
      status: mapped
    - id: day-06-santa-maddalena-hike
      day_id: day-06
      sequence: 3
      feature_id: santa-maddalena-viewpoint-hike
      mode: hike
      label: Santa Maddalena → panoramic viewpoint → Santa Maddalena
      source_label: Out-and-back corridor reconstructed from OpenStreetMap; AllTrails supplied as the itinerary reference
      source_url: https://www.openstreetmap.org/copyright
      external_label: View the referenced hike on AllTrails
      external_url: https://www.alltrails.com/trail/italy/south-tyrol/punto-panoramico-santa-maddalena
      status: mapped
      note: The map shows the shared walking corridor once for the outward and return hike.
    - id: day-06-santa-maddalena-ortisei
      day_id: day-06
      sequence: 4
      feature_id: santa-maddalena-ortisei-bus
      mode: bus
      label: Santa Maddalena, Val di Funes → Ortisei
      source_label: Named-place bus connector reconstructed on OpenStreetMap roads
      source_url: https://www.openstreetmap.org/copyright
      context_url: https://www.suedtirolmobil.info/en/my-journey/network-maps
      status: mapped
    - id: day-07-seceda-round-trip
      day_id: day-07
      sequence: 1
      feature_id: ortisei-seceda-cable
      mode: cable_car
      label: Ortisei ↔ Seceda via Furnes
      source_label: Official Ortisei–Furnes–Seceda lift system; geometry from OpenStreetMap
      source_url: https://www.seceda.it/en/summer
      status: mapped
    - id: day-08-ortisei-seceda
      day_id: day-08
      sequence: 1
      feature_id: ortisei-seceda-cable
      mode: cable_car
      label: Ortisei → Seceda via Furnes
      source_label: Official Ortisei–Furnes–Seceda lift system; geometry from OpenStreetMap
      source_url: https://www.seceda.it/en/summer
      status: mapped
    - id: day-08-seceda-hike
      day_id: day-08
      sequence: 2
      feature_id: seceda-pieralongia-hike
      mode: hike
      label: Seceda → Forcella Pana → Pieralongia → Seceda
      source_label: Loop reconstructed from OpenStreetMap; AllTrails supplied as the itinerary reference
      source_url: https://www.openstreetmap.org/copyright
      external_label: View the referenced hike on AllTrails
      external_url: https://www.alltrails.com/trail/italy/south-tyrol/seceda-malga-pieralongia
      status: mapped
    - id: day-08-seceda-ortisei
      day_id: day-08
      sequence: 3
      feature_id: ortisei-seceda-cable
      mode: cable_car
      label: Seceda → Ortisei via Furnes
      source_label: Official Ortisei–Furnes–Seceda lift system; geometry from OpenStreetMap
      source_url: https://www.seceda.it/en/summer
      status: mapped
    - id: day-09-ortisei-alpe-di-siusi
      day_id: day-09
      sequence: 1
      feature_id: ortisei-alpe-di-siusi-cable
      mode: cable_car
      label: Ortisei → Alpe di Siusi by the Mont Sëuc gondola
      source_label: Official Ortisei–Alpe di Siusi cableway; geometry from OpenStreetMap
      source_url: https://www.funiviaortisei.eu/en/orari-e-prezzi
      status: mapped
    - id: day-09-alpe-di-siusi-hike
      day_id: day-09
      sequence: 2
      feature_id: alpe-di-siusi-loop-hike
      mode: hike
      label: Mont Sëuc → Alpe di Siusi loop → Mont Sëuc
      source_label: Loop reconstructed from OpenStreetMap; AllTrails supplied as the itinerary reference
      source_url: https://www.openstreetmap.org/copyright
      external_label: View the referenced hike on AllTrails
      external_url: https://www.alltrails.com/trail/italy/south-tyrol/ortisei-alpe-siusi
      status: mapped
    - id: day-09-alpe-di-siusi-ortisei
      day_id: day-09
      sequence: 3
      feature_id: ortisei-alpe-di-siusi-cable
      mode: cable_car
      label: Alpe di Siusi → Ortisei by the Mont Sëuc gondola
      source_label: Official Ortisei–Alpe di Siusi cableway; geometry from OpenStreetMap
      source_url: https://www.funiviaortisei.eu/en/orari-e-prezzi
      status: mapped
    - id: day-10-ortisei-bolzano
      day_id: day-10
      sequence: 1
      feature_id: ortisei-bolzano-bus
      mode: bus
      label: Ortisei → Bolzano
      source_label: Named-place bus connector reconstructed on OpenStreetMap roads
      source_url: https://www.openstreetmap.org/copyright
      context_url: https://www.suedtirolmobil.info/en/my-journey/network-maps
      status: mapped
      note: Bolzano is a transfer point, not a numbered journey place.
    - id: day-10-bolzano-munich-airport
      day_id: day-10
      sequence: 2
      feature_id: bolzano-munich-airport-rail
      mode: rail
      label: Bolzano → Munich Airport via Brenner, Innsbruck, and München Hbf
      source_label: Physical public-transport railway shapes from open European timetable data
      source_url: https://transitous.org/sources/
      status: mapped
      note: The airport section follows the S8 alignment via München Ost.
  days:
    - id: day-01
      date: 2024-06-15
      place_ids:
        - geneva-airport
        - kandersteg
    - id: day-02
      date: 2024-06-16
      place_ids:
        - kandersteg
        - oeschinensee
        - kandersteg
    - id: day-03
      date: 2024-06-17
      place_ids:
        - kandersteg
        - spiez
        - interlaken
        - iseltwald
        - murren
        - lauterbrunnen
        - wengen
    - id: day-04
      date: 2024-06-18
      place_ids:
        - wengen
        - mannlichen
        - grindelwald
        - wengen
    - id: day-05
      date: 2024-06-19
      place_ids:
        - wengen
        - brixen
    - id: day-06
      date: 2024-06-20
      place_ids:
        - brixen
        - lago-di-braies
        - santa-maddalena-val-di-funes
        - ortisei
    - id: day-07
      date: 2024-06-21
      place_ids:
        - ortisei
        - seceda
        - ortisei
    - id: day-08
      date: 2024-06-22
      place_ids:
        - ortisei
        - seceda
        - ortisei
    - id: day-09
      date: 2024-06-23
      place_ids:
        - ortisei
        - alpe-di-siusi
        - ortisei
    - id: day-10
      date: 2024-06-24
      place_ids:
        - ortisei
        - munich-airport
  places:
    - id: geneva-airport
      name: Geneva Airport
      latitude: 46.2377125
      longitude: 6.1079823
      cover: /images/memories/swiss-dolomites/geneva-airport-1600.webp
      cover_alt: Geneva Airport runway seen through an airplane window with cloud-covered mountains beyond
      excerpt: We landed at Geneva Airport on June 15, with the Alps appearing beyond the runway, before continuing by rail to Kandersteg.
    - id: kandersteg
      name: Kandersteg
      latitude: 46.4955600
      longitude: 7.6715068
      cover: /images/memories/swiss-dolomites/kandersteg-1600.webp
      cover_alt: Cows grazing in an alpine meadow below snow-streaked mountains near Kandersteg
      excerpt: Kandersteg was our alpine base for the first three days, surrounded by snowy peaks and green meadows, with Oeschinensee close by.
      photos:
        - thumb: /images/memories/swiss-dolomites/kandersteg-1-480.webp
          medium: /images/memories/swiss-dolomites/kandersteg-1-960.webp
          full: /images/memories/swiss-dolomites/kandersteg-1-1600.webp
          alt: Snow-covered mountain peaks framed by a forest path near Kandersteg
          caption: Snow-covered peaks above the forest near Kandersteg
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/kandersteg-2-480.webp
          medium: /images/memories/swiss-dolomites/kandersteg-2-960.webp
          full: /images/memories/swiss-dolomites/kandersteg-2-1600.webp
          alt: Kandersteg rooftops beneath snow-streaked mountains and a clear blue sky
          caption: Kandersteg village beneath the mountains
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/kandersteg-3-480.webp
          medium: /images/memories/swiss-dolomites/kandersteg-3-960.webp
          full: /images/memories/swiss-dolomites/kandersteg-3-1600.webp
          alt: Stone church below a cloud-wrapped rocky mountain in Kandersteg
          caption: Church and mountain cliffs in Kandersteg
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/kandersteg-4-480.webp
          medium: /images/memories/swiss-dolomites/kandersteg-4-960.webp
          full: /images/memories/swiss-dolomites/kandersteg-4-1600.webp
          alt: Walkers on a winding path beneath snow-covered mountain cliffs near Kandersteg
          caption: Mountain path near Kandersteg
          captured_on: 2024-06-16
    - id: oeschinensee
      name: Oeschinensee
      latitude: 46.4984951
      longitude: 7.7268429
      cover: /images/memories/swiss-dolomites/oeschinensee-1600.webp
      cover_alt: Turquoise Oeschinensee beneath gray cliffs and evergreen forest
      excerpt: We hiked from Kandersteg to Oeschinensee on June 16, following the trail above turquoise water, evergreen forest, waterfalls, and gray mountain cliffs.
      photos:
        - thumb: /images/memories/swiss-dolomites/oeschinensee-1-480.webp
          medium: /images/memories/swiss-dolomites/oeschinensee-1-960.webp
          full: /images/memories/swiss-dolomites/oeschinensee-1-1600.webp
          alt: Oeschinensee below layered cliffs and cascading waterfalls
          caption: Waterfalls above Oeschinensee
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/oeschinensee-2-480.webp
          medium: /images/memories/swiss-dolomites/oeschinensee-2-960.webp
          full: /images/memories/swiss-dolomites/oeschinensee-2-1600.webp
          alt: Rocky alpine cliffs and waterfalls rising above Oeschinensee
          caption: Cliffs above the lake
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/oeschinensee-3-480.webp
          medium: /images/memories/swiss-dolomites/oeschinensee-3-960.webp
          full: /images/memories/swiss-dolomites/oeschinensee-3-1600.webp
          alt: Turquoise Oeschinensee with a rocky shore, conifers, and a small boat
          caption: Oeschinensee from the hiking trail
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/oeschinensee-4-480.webp
          medium: /images/memories/swiss-dolomites/oeschinensee-4-960.webp
          full: /images/memories/swiss-dolomites/oeschinensee-4-1600.webp
          alt: Clouds and mountains reflected in the turquoise water of Oeschinensee
          caption: Reflections on Oeschinensee
          captured_on: 2024-06-16
        - thumb: /images/memories/swiss-dolomites/oeschinensee-5-480.webp
          medium: /images/memories/swiss-dolomites/oeschinensee-5-960.webp
          full: /images/memories/swiss-dolomites/oeschinensee-5-1600.webp
          alt: Oeschinensee glowing turquoise beneath layered cliffs and waterfalls
          caption: Turquoise lake and cliffs
          captured_on: 2024-06-16
    - id: spiez
      name: Spiez
      latitude: 46.6865846
      longitude: 7.6800353
      cover: /images/memories/swiss-dolomites/spiez-1600.webp
      cover_alt: Spiez Castle, vineyards, and Lake Thun beneath the mountains
      excerpt: We passed through Spiez by rail on June 17, catching a view of Spiez Castle, hillside vineyards, and Lake Thun beneath the mountains.
    - id: interlaken
      name: Interlaken Ost
      latitude: 46.6904478
      longitude: 7.8689965
      cover: /images/memories/swiss-dolomites/interlaken-1600.webp
      cover_alt: A church spire and Swiss flags in Interlaken with a snowy mountain beyond
      excerpt: Interlaken Ost was our rail-and-bus crossroads on June 17, with Swiss flags, a church spire, and a snow-covered peak rising beyond the town.
    - id: iseltwald
      name: Iseltwald
      latitude: 46.7104598
      longitude: 7.9634571
      cover: /images/memories/swiss-dolomites/iseltwald-1600.webp
      cover_alt: Lakeside buildings and boats reflected in Lake Brienz at Iseltwald
      excerpt: We made a lakeside stop in Iseltwald on June 17, where boats and waterfront houses reflected across the calm blue water of Lake Brienz.
    - id: murren
      name: Mürren
      latitude: 46.5636889
      longitude: 7.8971188
      cover: /images/memories/swiss-dolomites/murren-1600.webp
      cover_alt: Clouds drifting across snow-covered mountains above the green slopes near Mürren
      excerpt: We reached Mürren through Grütschalp on June 17, finding green alpine slopes and wooden chalets beneath cloud-wrapped, snow-covered peaks.
      photos:
        - thumb: /images/memories/swiss-dolomites/murren-1-480.webp
          medium: /images/memories/swiss-dolomites/murren-1-960.webp
          full: /images/memories/swiss-dolomites/murren-1-1600.webp
          alt: A snow-covered mountain framed by evergreen trees and an alpine shed near Mürren
          caption: Mountain view near Mürren
          captured_on: 2024-06-17
        - thumb: /images/memories/swiss-dolomites/murren-2-480.webp
          medium: /images/memories/swiss-dolomites/murren-2-960.webp
          full: /images/memories/swiss-dolomites/murren-2-1600.webp
          alt: A snow-covered mountain ridge above dark forest and a distant waterfall near Mürren
          caption: Snowy ridge above the valley
          captured_on: 2024-06-17
        - thumb: /images/memories/swiss-dolomites/murren-3-480.webp
          medium: /images/memories/swiss-dolomites/murren-3-960.webp
          full: /images/memories/swiss-dolomites/murren-3-1600.webp
          alt: Distant snow-covered peaks above green pastures and chalets near Mürren
          caption: Pastures beneath the peaks
          captured_on: 2024-06-17
    - id: lauterbrunnen
      name: Lauterbrunnen
      latitude: 46.5983618
      longitude: 7.9080357
      cover: /images/memories/swiss-dolomites/lauterbrunnen-1600.webp
      cover_alt: Lauterbrunnen church and village below snow-covered mountains framed by cliffs
      excerpt: Lauterbrunnen brought us back into the valley on June 17, with its church, sheer cliffs, and Staubbach Falls framed by snowy mountains.
      photos:
        - thumb: /images/memories/swiss-dolomites/lauterbrunnen-1-480.webp
          medium: /images/memories/swiss-dolomites/lauterbrunnen-1-960.webp
          full: /images/memories/swiss-dolomites/lauterbrunnen-1-1600.webp
          alt: Staubbach Falls dropping from a sheer cliff beside Lauterbrunnen village
          caption: Staubbach Falls
          captured_on: 2024-06-17
    - id: wengen
      name: Wengen
      latitude: 46.6050081
      longitude: 7.9208650
      cover: /images/memories/swiss-dolomites/wengen-1600.webp
      cover_alt: Wengen chalets and green meadows beneath snow-covered mountains
      excerpt: Wengen became our mountain base from June 17 to 19, with chalet rooftops, green meadows, and snowy peaks shifting from bright daylight to moonlit blue.
      photos:
        - thumb: /images/memories/swiss-dolomites/wengen-1-480.webp
          medium: /images/memories/swiss-dolomites/wengen-1-960.webp
          full: /images/memories/swiss-dolomites/wengen-1-1600.webp
          alt: A sunlit snow-covered mountain rising above chalet rooftops in Wengen
          caption: Mountain view from Wengen
          captured_on: 2024-06-19
        - thumb: /images/memories/swiss-dolomites/wengen-2-480.webp
          medium: /images/memories/swiss-dolomites/wengen-2-960.webp
          full: /images/memories/swiss-dolomites/wengen-2-1600.webp
          alt: The moon above snow-covered mountains at blue hour in Wengen
          caption: Moon over the mountains
          captured_on: 2024-06-18
    - id: mannlichen
      name: Männlichen
      latitude: 46.6181397
      longitude: 7.9380395
      cover: /images/memories/swiss-dolomites/mannlichen-1600.webp
      cover_alt: Snow-covered peaks beyond the Männlichen mountain station and green slopes
      excerpt: We rode the cable car from Wengen to Männlichen on June 18, then set out along the Panoramaweg beneath broad snow-covered peaks and a clear blue sky.
      photos:
        - thumb: /images/memories/swiss-dolomites/mannlichen-1-480.webp
          medium: /images/memories/swiss-dolomites/mannlichen-1-960.webp
          full: /images/memories/swiss-dolomites/mannlichen-1-1600.webp
          alt: A broad snow-covered mountain range beyond the green ridge at Männlichen
          caption: Panorama from Männlichen
          captured_on: 2024-06-18
        - thumb: /images/memories/swiss-dolomites/mannlichen-2-480.webp
          medium: /images/memories/swiss-dolomites/mannlichen-2-960.webp
          full: /images/memories/swiss-dolomites/mannlichen-2-1600.webp
          alt: Snow-covered peaks with a Swiss flagpole in the foreground at Männlichen
          caption: Swiss flag and alpine peaks
          captured_on: 2024-06-18
        - thumb: /images/memories/swiss-dolomites/mannlichen-3-480.webp
          medium: /images/memories/swiss-dolomites/mannlichen-3-960.webp
          full: /images/memories/swiss-dolomites/mannlichen-3-1600.webp
          alt: A snow-covered mountain framed by a window inside the Männlichen station
          caption: Mountain framed by the station window
          captured_on: 2024-06-18
    - id: grindelwald
      name: Grindelwald
      latitude: 46.6245321
      longitude: 8.0325427
      cover: /images/memories/swiss-dolomites/grindelwald-1600.webp
      cover_alt: Snow-covered peaks above Grindelwald with green alpine slopes and a small reservoir
      excerpt: We continued by mountain railway to Grindelwald on June 18, looking across green slopes and chalets toward the snow-covered mountain walls above the valley.
      photos:
        - thumb: /images/memories/swiss-dolomites/grindelwald-1-480.webp
          medium: /images/memories/swiss-dolomites/grindelwald-1-960.webp
          full: /images/memories/swiss-dolomites/grindelwald-1-1600.webp
          alt: Green meadows and chalets in Grindelwald below a snow-streaked mountain face
          caption: Meadows and chalets in Grindelwald
          captured_on: 2024-06-18
        - thumb: /images/memories/swiss-dolomites/grindelwald-2-480.webp
          medium: /images/memories/swiss-dolomites/grindelwald-2-960.webp
          full: /images/memories/swiss-dolomites/grindelwald-2-1600.webp
          alt: A hiker photographing snow-covered peaks from a mountain path above Grindelwald
          caption: Mountain path above Grindelwald
          captured_on: 2024-06-18
        - thumb: /images/memories/swiss-dolomites/grindelwald-3-480.webp
          medium: /images/memories/swiss-dolomites/grindelwald-3-960.webp
          full: /images/memories/swiss-dolomites/grindelwald-3-1600.webp
          alt: Snow-covered peaks and alpine paths above Grindelwald
          caption: Snowy peaks above Grindelwald
          captured_on: 2024-06-18
    - id: brixen
      name: Brixen / Bressanone
      latitude: 46.7100050
      longitude: 11.6497561
      cover: /images/memories/swiss-dolomites/brixen-1600.webp
      cover_alt: Brixen old-town rooftops and a stone clock tower beneath an overcast sky
      excerpt: We arrived in Brixen by rail on June 19, walking beneath pastel old-town facades and the stone clock tower rising above its narrow streets.
    - id: lago-di-braies
      name: Lago di Braies
      latitude: 46.6947208
      longitude: 12.0858434
      cover: /images/memories/swiss-dolomites/lago-di-braies-1600.webp
      cover_alt: A traveler in a wooden rowboat on Lago di Braies beneath steep mountain cliffs
      excerpt: We reached Lago di Braies by car on June 20, rowing across emerald water beneath steep pale cliffs, snow-streaked slopes, and dark evergreen forest.
      photos:
        - thumb: /images/memories/swiss-dolomites/lago-di-braies-1-480.webp
          medium: /images/memories/swiss-dolomites/lago-di-braies-1-960.webp
          full: /images/memories/swiss-dolomites/lago-di-braies-1-1600.webp
          alt: Emerald Lago di Braies with wooden rowboats below pale limestone cliffs
          caption: Emerald lake below limestone cliffs
          captured_on: 2024-06-20
        - thumb: /images/memories/swiss-dolomites/lago-di-braies-2-480.webp
          medium: /images/memories/swiss-dolomites/lago-di-braies-2-960.webp
          full: /images/memories/swiss-dolomites/lago-di-braies-2-1600.webp
          alt: Dense evergreen forest and towering rock cliffs across Lago di Braies
          caption: Forested shore of Lago di Braies
          captured_on: 2024-06-20
        - thumb: /images/memories/swiss-dolomites/lago-di-braies-3-480.webp
          medium: /images/memories/swiss-dolomites/lago-di-braies-3-960.webp
          full: /images/memories/swiss-dolomites/lago-di-braies-3-1600.webp
          alt: Calm green water and distant rowboats beneath the mountains at Lago di Braies
          caption: Rowboats beneath the mountains
          captured_on: 2024-06-20
        - thumb: /images/memories/swiss-dolomites/lago-di-braies-4-480.webp
          medium: /images/memories/swiss-dolomites/lago-di-braies-4-960.webp
          full: /images/memories/swiss-dolomites/lago-di-braies-4-1600.webp
          alt: Sunlit rocky cliffs rising above the green lake and conifer shoreline
          caption: Sunlit cliffs above the lake
          captured_on: 2024-06-20
        - thumb: /images/memories/swiss-dolomites/lago-di-braies-5-480.webp
          medium: /images/memories/swiss-dolomites/lago-di-braies-5-960.webp
          full: /images/memories/swiss-dolomites/lago-di-braies-5-1600.webp
          alt: Wooden rowboats floating on dark emerald water beneath pale mountain cliffs
          caption: Wooden boats on emerald water
          captured_on: 2024-06-20
    - id: santa-maddalena-val-di-funes
      name: Santa Maddalena, Val di Funes
      latitude: 46.6414556
      longitude: 11.7153339
      cover: /images/memories/swiss-dolomites/santa-maddalena-val-di-funes-1600.webp
      cover_alt: Santa Maddalena church and green meadows beneath cloud-covered Odle peaks
      excerpt: We stopped in Santa Maddalena on June 20, hiking through green meadows past the village church toward a panoramic view of the cloud-wrapped Odle peaks.
    - id: ortisei
      name: Ortisei
      latitude: 46.5752077
      longitude: 11.6721382
      cover: /images/memories/swiss-dolomites/ortisei-1600.webp
      cover_alt: Ortisei rooftops and a pink church tower below green hills wrapped in low cloud
      excerpt: Ortisei was our Dolomites base from June 20 to 24, where sunshine, rain, mist, and fast-moving clouds transformed the church and surrounding peaks within remarkably short periods.
      photos:
        - thumb: /images/memories/swiss-dolomites/ortisei-1-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-1-960.webp
          full: /images/memories/swiss-dolomites/ortisei-1-1600.webp
          alt: Ortisei church tower below a pale Dolomite peak in clear evening light
          caption: Church tower beneath a Dolomite peak
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-2-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-2-960.webp
          full: /images/memories/swiss-dolomites/ortisei-2-1600.webp
          alt: Ortisei church tower with the mountain behind it veiled by rain and mist
          caption: Mountain through the rain
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-3-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-3-960.webp
          full: /images/memories/swiss-dolomites/ortisei-3-1600.webp
          alt: Pink church tower in Ortisei with low cloud drifting across the dark hillside
          caption: Low cloud around Ortisei
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-4-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-4-960.webp
          full: /images/memories/swiss-dolomites/ortisei-4-1600.webp
          alt: Blue sky breaking through clouds above the Ortisei church tower and mountain
          caption: Clearing clouds above the church
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-5-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-5-960.webp
          full: /images/memories/swiss-dolomites/ortisei-5-1600.webp
          alt: Three views of storm clouds, filtered sunlight, and a pink sunset over the Ortisei valley
          caption: Weather changing over the valley
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-6-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-6-960.webp
          full: /images/memories/swiss-dolomites/ortisei-6-1600.webp
          alt: Low fog drifting through forested green hills above the houses of Ortisei
          caption: Fog drifting across green hills
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/ortisei-7-480.webp
          medium: /images/memories/swiss-dolomites/ortisei-7-960.webp
          full: /images/memories/swiss-dolomites/ortisei-7-1600.webp
          alt: A quiet street and houses in Ortisei below banks of low cloud
          caption: Ortisei beneath low cloud
          captured_on: 2024-06-23
    - id: seceda
      name: Seceda
      latitude: 46.6005922
      longitude: 11.7257836
      cover: /images/memories/swiss-dolomites/seceda-1600.webp
      cover_alt: Jagged Seceda rock towers and green alpine ridges beneath moving cloud
      excerpt: We rode the cableway from Ortisei to Seceda on June 21 and 22, returning for the Pieralongia hike beneath jagged rock towers and steep green ridges.
      photos:
        - thumb: /images/memories/swiss-dolomites/seceda-1-480.webp
          medium: /images/memories/swiss-dolomites/seceda-1-960.webp
          full: /images/memories/swiss-dolomites/seceda-1-1600.webp
          alt: Close view of the jagged Seceda towers with snow lingering in rocky gullies
          caption: Jagged Seceda towers
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-2-480.webp
          medium: /images/memories/swiss-dolomites/seceda-2-960.webp
          full: /images/memories/swiss-dolomites/seceda-2-1600.webp
          alt: Hikers crossing a green alpine slope below the sharp rock peaks of Seceda
          caption: Alpine slope below the peaks
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-3-480.webp
          medium: /images/memories/swiss-dolomites/seceda-3-960.webp
          full: /images/memories/swiss-dolomites/seceda-3-1600.webp
          alt: Hikers following a mountain trail toward the jagged Seceda ridgeline
          caption: Hiking beneath Seceda
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-4-480.webp
          medium: /images/memories/swiss-dolomites/seceda-4-960.webp
          full: /images/memories/swiss-dolomites/seceda-4-1600.webp
          alt: White clouds sweeping across the steep rock towers and green ridges of Seceda
          caption: Clouds crossing the rock towers
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-5-480.webp
          medium: /images/memories/swiss-dolomites/seceda-5-960.webp
          full: /images/memories/swiss-dolomites/seceda-5-1600.webp
          alt: Layered rocky ridges and snow-streaked peaks at Seceda beneath a gray sky
          caption: Layered ridges in gray light
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-6-480.webp
          medium: /images/memories/swiss-dolomites/seceda-6-960.webp
          full: /images/memories/swiss-dolomites/seceda-6-1600.webp
          alt: Two views of cloud-shadowed alpine meadows and a small pond reflecting the sky
          caption: Alpine meadows and a reflecting pond
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-7-480.webp
          medium: /images/memories/swiss-dolomites/seceda-7-960.webp
          full: /images/memories/swiss-dolomites/seceda-7-1600.webp
          alt: A small alpine cabin surrounded by green meadow and dense evergreen forest below Seceda
          caption: Forest meadow below Seceda
          captured_on: 2024-06-22
        - thumb: /images/memories/swiss-dolomites/seceda-8-480.webp
          medium: /images/memories/swiss-dolomites/seceda-8-960.webp
          full: /images/memories/swiss-dolomites/seceda-8-1600.webp
          alt: Dark Seceda peaks under bright white clouds above steep green slopes
          caption: Cloud shadows over the ridge
          captured_on: 2024-06-22
    - id: alpe-di-siusi
      name: Alpe di Siusi
      latitude: 46.5310560
      longitude: 11.6247091
      cover: /images/memories/swiss-dolomites/alpe-di-siusi-1600.webp
      cover_alt: Cloud-wrapped Dolomite peaks above evergreen forest and green slopes at Alpe di Siusi
      excerpt: We reached Alpe di Siusi by cable car on June 23, following the hiking loop through wildflower meadows and evergreen forest beneath cloud-wrapped Dolomite peaks.
      photos:
        - thumb: /images/memories/swiss-dolomites/alpe-di-siusi-1-480.webp
          medium: /images/memories/swiss-dolomites/alpe-di-siusi-1-960.webp
          full: /images/memories/swiss-dolomites/alpe-di-siusi-1-1600.webp
          alt: Dolomite peaks emerging through low cloud above forest and meadow at Alpe di Siusi
          caption: Dolomite peaks through low cloud
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/alpe-di-siusi-2-480.webp
          medium: /images/memories/swiss-dolomites/alpe-di-siusi-2-960.webp
          full: /images/memories/swiss-dolomites/alpe-di-siusi-2-1600.webp
          alt: A dark mountain face partly hidden by thick cloud above a line of evergreen trees
          caption: Mountain face behind the clouds
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/alpe-di-siusi-3-480.webp
          medium: /images/memories/swiss-dolomites/alpe-di-siusi-3-960.webp
          full: /images/memories/swiss-dolomites/alpe-di-siusi-3-1600.webp
          alt: A wooden bench among alpine wildflowers beside a hiking path at Alpe di Siusi
          caption: Wildflowers beside the hiking path
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/alpe-di-siusi-4-480.webp
          medium: /images/memories/swiss-dolomites/alpe-di-siusi-4-960.webp
          full: /images/memories/swiss-dolomites/alpe-di-siusi-4-1600.webp
          alt: Cloud lifting from a rocky peak above the green forested plateau of Alpe di Siusi
          caption: Cloud lifting over the plateau
          captured_on: 2024-06-23
        - thumb: /images/memories/swiss-dolomites/alpe-di-siusi-5-480.webp
          medium: /images/memories/swiss-dolomites/alpe-di-siusi-5-960.webp
          full: /images/memories/swiss-dolomites/alpe-di-siusi-5-1600.webp
          alt: A lone wooden hut on a green alpine meadow beneath broad white clouds
          caption: A lone hut on the meadow
          captured_on: 2024-06-23
    - id: munich-airport
      name: Munich Airport
      latitude: 48.3539625
      longitude: 11.7785925
      excerpt: We left Ortisei on June 24, traveling by bus and rail through Bolzano and Innsbruck to Munich, then continuing to Munich Airport for our departure.
---
