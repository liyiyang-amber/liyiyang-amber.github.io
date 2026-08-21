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
    - id: spiez
      name: Spiez
      latitude: 46.6865846
      longitude: 7.6800353
    - id: interlaken
      name: Interlaken Ost
      latitude: 46.6904478
      longitude: 7.8689965
    - id: iseltwald
      name: Iseltwald
      latitude: 46.7104598
      longitude: 7.9634571
    - id: murren
      name: Mürren
      latitude: 46.5636889
      longitude: 7.8971188
    - id: lauterbrunnen
      name: Lauterbrunnen
      latitude: 46.5983618
      longitude: 7.9080357
    - id: wengen
      name: Wengen
      latitude: 46.6050081
      longitude: 7.9208650
    - id: mannlichen
      name: Männlichen
      latitude: 46.6181397
      longitude: 7.9380395
    - id: grindelwald
      name: Grindelwald
      latitude: 46.6245321
      longitude: 8.0325427
    - id: brixen
      name: Brixen / Bressanone
      latitude: 46.7100050
      longitude: 11.6497561
    - id: lago-di-braies
      name: Lago di Braies
      latitude: 46.6947208
      longitude: 12.0858434
    - id: santa-maddalena-val-di-funes
      name: Santa Maddalena, Val di Funes
      latitude: 46.6414556
      longitude: 11.7153339
    - id: ortisei
      name: Ortisei
      latitude: 46.5752077
      longitude: 11.6721382
    - id: seceda
      name: Seceda
      latitude: 46.6005922
      longitude: 11.7257836
    - id: alpe-di-siusi
      name: Alpe di Siusi
      latitude: 46.5310560
      longitude: 11.6247091
    - id: munich-airport
      name: Munich Airport
      latitude: 48.3539625
      longitude: 11.7785925
---
