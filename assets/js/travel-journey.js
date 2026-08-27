(function () {
  "use strict";

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, function (character) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      }[character];
    });
  }

  function attachTrackpadPinchZoom(map, mapElement) {
    var zoomStep = 0.25;
    var wheelPixelsPerZoomLevel = 60;
    var pendingWheelZoom = 0;
    var wheelFrame = null;
    var wheelAnchor = null;
    var gestureActive = false;
    var gestureStartZoom = 0;
    var gestureAnchor = null;
    var cleanedUp = false;
    var wheelListenerOptions = { passive: false };
    var gestureListenerOptions = { passive: false };

    function clampZoom(zoom) {
      var minZoom = map.getMinZoom();
      var maxZoom = map.getMaxZoom();
      if (Number.isFinite(minZoom)) zoom = Math.max(minZoom, zoom);
      if (Number.isFinite(maxZoom)) zoom = Math.min(maxZoom, zoom);
      return zoom;
    }

    function snapZoom(zoom) {
      return Math.round(zoom / zoomStep) * zoomStep;
    }

    function pointFromEvent(event) {
      var rect = mapElement.getBoundingClientRect();
      if (Number.isFinite(event.clientX) && Number.isFinite(event.clientY)) {
        var x = event.clientX - rect.left;
        var y = event.clientY - rect.top;
        if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
          return window.L.point(x, y);
        }
      }
      return window.L.point(rect.width / 2, rect.height / 2);
    }

    function normalizedWheelDelta(event) {
      var delta = event.deltaY;
      if (event.deltaMode === 1) delta *= 16;
      else if (event.deltaMode === 2) delta *= mapElement.clientHeight || window.innerHeight;
      return Math.max(-240, Math.min(240, delta));
    }

    function applyWheelZoom() {
      wheelFrame = null;
      if (!map || !wheelAnchor || Math.abs(pendingWheelZoom) < zoomStep / 2) return;

      var currentZoom = map.getZoom();
      var targetZoom = snapZoom(clampZoom(currentZoom + pendingWheelZoom));
      var appliedZoom = targetZoom - currentZoom;
      if (appliedZoom === 0) {
        pendingWheelZoom = 0;
        return;
      }

      pendingWheelZoom -= appliedZoom;
      map.setZoomAround(wheelAnchor, targetZoom, { animate: false });
    }

    function onWheel(event) {
      if (!event.ctrlKey) return;
      event.preventDefault();
      event.stopPropagation();
      if (gestureActive) return;

      wheelAnchor = pointFromEvent(event);
      pendingWheelZoom += -normalizedWheelDelta(event) / wheelPixelsPerZoomLevel;
      if (wheelFrame === null) wheelFrame = window.requestAnimationFrame(applyWheelZoom);
    }

    function onGestureStart(event) {
      event.preventDefault();
      event.stopPropagation();
      gestureActive = true;
      gestureStartZoom = map.getZoom();
      gestureAnchor = pointFromEvent(event);
      pendingWheelZoom = 0;
      if (wheelFrame !== null) {
        window.cancelAnimationFrame(wheelFrame);
        wheelFrame = null;
      }
    }

    function onGestureChange(event) {
      if (!gestureActive) return;
      event.preventDefault();
      event.stopPropagation();
      if (!Number.isFinite(event.scale) || event.scale <= 0) return;

      gestureAnchor = pointFromEvent(event);
      var targetZoom = snapZoom(clampZoom(map.getScaleZoom(event.scale, gestureStartZoom)));
      map.setZoomAround(gestureAnchor, targetZoom, { animate: false });
    }

    function onGestureEnd(event) {
      if (!gestureActive) return;
      event.preventDefault();
      event.stopPropagation();
      gestureActive = false;
      gestureAnchor = null;
    }

    function cleanup() {
      if (cleanedUp) return;
      cleanedUp = true;
      if (wheelFrame !== null) window.cancelAnimationFrame(wheelFrame);
      mapElement.removeEventListener("wheel", onWheel, wheelListenerOptions);
      mapElement.removeEventListener("gesturestart", onGestureStart, gestureListenerOptions);
      mapElement.removeEventListener("gesturechange", onGestureChange, gestureListenerOptions);
      mapElement.removeEventListener("gestureend", onGestureEnd, gestureListenerOptions);
      window.removeEventListener("pagehide", cleanup);
      map.off("unload", cleanup);
    }

    mapElement.addEventListener("wheel", onWheel, wheelListenerOptions);
    if (
      typeof window.GestureEvent !== "undefined" &&
      (!window.navigator || !window.navigator.maxTouchPoints)
    ) {
      mapElement.addEventListener("gesturestart", onGestureStart, gestureListenerOptions);
      mapElement.addEventListener("gesturechange", onGestureChange, gestureListenerOptions);
      mapElement.addEventListener("gestureend", onGestureEnd, gestureListenerOptions);
    }
    window.addEventListener("pagehide", cleanup);
    map.on("unload", cleanup);
  }

  ready(function () {
    var root = document.querySelector("[data-travel-journey]");
    if (!root) return;

    var mapElement = root.querySelector("[data-travel-map]");
    var tooltip = root.querySelector("[data-map-tooltip]");
    var status = root.querySelector("[data-map-status]");
    var dayDialog = root.querySelector("[data-day-dialog]");
    var dayDialogTitle = root.querySelector("[data-day-dialog-title]");
    var dayDialogDate = root.querySelector("[data-day-dialog-date]");
    var dayDialogRoute = root.querySelector("[data-day-dialog-route]");
    var dayDialogLink = root.querySelector("[data-day-dialog-link]");
    var routeDialog = root.querySelector("[data-route-dialog]");
    var routeDialogTitle = root.querySelector("[data-route-dialog-title]");
    var routeDialogMode = root.querySelector("[data-route-dialog-mode]");
    var routeDialogSource = root.querySelector("[data-route-dialog-source]");
    var routeDialogNote = root.querySelector("[data-route-dialog-note]");
    var routeDialogSourceLink = root.querySelector("[data-route-dialog-source-link]");
    var routeDialogExternalLink = root.querySelector("[data-route-dialog-external-link]");
    var routeDialogDayLink = root.querySelector("[data-route-dialog-day-link]");
    var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    var activeDialog = null;
    var activeDayId = null;
    var activePlaceId = null;
    var touchPreviewPlaceId = null;
    var activeRouteId = null;
    var routeUnavailable = false;
    var map = null;
    var markers = {};
    var routeLayers = {};
    var enabledModes = {
      rail: true,
      cable_car: true,
      bus: true,
      rideshare: true,
      hike: true,
    };

    var places = Array.prototype.map.call(
      root.querySelectorAll("[data-journey-place]"),
      function (section) {
        var id = section.getAttribute("data-place-id");
        var nameElement = section.querySelector("[data-place-name]");
        var excerptElement = section.querySelector("[data-place-excerpt]");
        var coverElement = section.querySelector("[data-place-cover]");
        var visitDates = (section.getAttribute("data-visit-dates") || "")
          .split("||")
          .map(function (value) {
            return value.trim();
          })
          .filter(Boolean);
        return {
          id: id,
          markerLabel: section.getAttribute("data-marker-label"),
          name: nameElement ? nameElement.textContent.trim() : id,
          latitude: Number(section.getAttribute("data-latitude")),
          longitude: Number(section.getAttribute("data-longitude")),
          visitDates: visitDates,
          excerpt: excerptElement ? excerptElement.textContent.trim() : "",
          cover: coverElement ? coverElement.currentSrc || coverElement.src : "",
          coverAlt: coverElement ? coverElement.alt : "",
          section: section,
        };
      }
    );

    var days = Array.prototype.map.call(
      root.querySelectorAll("[data-journey-day]"),
      function (section) {
        return {
          id: section.getAttribute("data-day-id"),
          number: section.getAttribute("data-day-number"),
          date: section.getAttribute("data-day-date"),
          placeIds: (section.getAttribute("data-place-ids") || "").split(/\s+/).filter(Boolean),
          section: section,
        };
      }
    );

    var routes = Array.prototype.map.call(
      root.querySelectorAll("[data-journey-route]"),
      function (section) {
        return {
          id: section.getAttribute("data-route-id"),
          dayId: section.getAttribute("data-route-day-id"),
          sequence: Number(section.getAttribute("data-route-sequence")),
          featureId: section.getAttribute("data-route-feature-id") || "",
          mode: section.getAttribute("data-route-mode") || "",
          modeLabel: section.getAttribute("data-route-mode-label") || "Connection",
          label: section.getAttribute("data-route-label") || "Route connection",
          status: section.getAttribute("data-route-status"),
          sourceLabel: section.getAttribute("data-route-source-label") || "",
          sourceUrl: section.getAttribute("data-route-source-url") || "",
          externalLabel: section.getAttribute("data-route-external-label") || "",
          externalUrl: section.getAttribute("data-route-external-url") || "",
          note: section.getAttribute("data-route-note") || "",
          section: section,
        };
      }
    );

    function findPlace(id) {
      return places.find(function (place) {
        return place.id === id;
      });
    }

    function findDay(id) {
      return days.find(function (day) {
        return day.id === id;
      });
    }

    function findRoute(id) {
      return routes.find(function (route) {
        return route.id === id;
      });
    }

    function routesForFeature(featureId) {
      return routes.filter(function (route) {
        return route.status === "mapped" && route.featureId === featureId;
      });
    }

    function routeForFeature(featureId) {
      var matches = routesForFeature(featureId);
      if (activeDayId) {
        var dayMatch = matches.find(function (route) {
          return route.dayId === activeDayId;
        });
        if (dayMatch) return dayMatch;
      }
      return matches[0];
    }

    function showStatus(message) {
      if (!status) return;
      status.textContent = message;
      status.hidden = false;
    }

    function hideStatus() {
      if (!status) return;
      status.hidden = true;
      status.textContent = "";
    }

    function focusableElements(dialog) {
      return Array.prototype.filter.call(
        dialog.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'),
        function (element) {
          return !element.hidden && element.offsetParent !== null;
        }
      );
    }

    function openDialog(dialog, trigger) {
      if (!dialog || typeof dialog.showModal !== "function") return false;
      if (dialog.open) return true;
      if (activeDialog && activeDialog !== dialog && activeDialog.open) {
        activeDialog._skipFocusRestore = true;
        activeDialog.close();
      }
      dialog._returnTrigger = trigger || document.activeElement;
      activeDialog = dialog;
      dialog.showModal();
      document.body.classList.add("travel-dialog-open");
      window.requestAnimationFrame(function () {
        var close = dialog.querySelector("[data-dialog-close]");
        if (close) close.focus();
      });
      return true;
    }

    function closeDialog(dialog, restoreFocus) {
      if (!dialog || !dialog.open) return;
      if (restoreFocus === false) dialog._skipFocusRestore = true;
      dialog.close();
    }

    Array.prototype.forEach.call(root.querySelectorAll("dialog"), function (dialog) {
      dialog.addEventListener("click", function (event) {
        if (event.target === dialog) closeDialog(dialog, true);
      });
      dialog.addEventListener("close", function () {
        if (activeDialog === dialog) activeDialog = null;
        if (!root.querySelector("dialog[open]")) {
          document.body.classList.remove("travel-dialog-open");
        }
        if (dialog._skipFocusRestore) {
          dialog._skipFocusRestore = false;
          return;
        }
        if (dialog._returnTrigger && typeof dialog._returnTrigger.focus === "function") {
          dialog._returnTrigger.focus();
        }
        if (dialog === routeDialog) setActiveRoute(null);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (!activeDialog || !activeDialog.open) return;
      if (event.key === "Escape") {
        event.preventDefault();
        closeDialog(activeDialog, true);
        return;
      }
      if (event.key !== "Tab") return;

      var focusable = focusableElements(activeDialog);
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });

    function setActiveDay(id) {
      activeDayId = id;
      Array.prototype.forEach.call(root.querySelectorAll("[data-day-trigger]"), function (trigger) {
        var active = trigger.getAttribute("data-day-trigger") === id;
        trigger.classList.toggle("is-active", active);
        if (active) trigger.setAttribute("aria-current", "true");
        else trigger.removeAttribute("aria-current");
      });
      updateRouteStyles();
    }

    function setActivePlace(id) {
      activePlaceId = id;
      Object.keys(markers).forEach(function (placeId) {
        var element = markers[placeId].getElement();
        if (element) element.classList.toggle("is-active", placeId === id);
      });
    }

    function setActiveRoute(id) {
      activeRouteId = id;
      Array.prototype.forEach.call(root.querySelectorAll("[data-journey-route]"), function (section) {
        section.classList.toggle("is-active", section.getAttribute("data-route-id") === id);
      });
      updateRouteStyles();
    }

    function populateDayDialog(day) {
      dayDialogTitle.textContent = "Day " + day.number;
      dayDialogDate.textContent = day.date;
      dayDialogLink.setAttribute("href", "#journey-" + day.id);
      dayDialogRoute.textContent = "";

      day.placeIds.forEach(function (placeId) {
        var place = findPlace(placeId);
        if (!place) return;
        var item = document.createElement("li");
        var link = document.createElement("a");
        var marker = document.createElement("span");
        var name = document.createElement("strong");
        link.href = "#journey-place-" + place.id;
        link.setAttribute("data-dialog-place-link", "");
        marker.className = "travel-day-dialog__marker";
        marker.setAttribute("aria-hidden", "true");
        marker.textContent = place.markerLabel;
        name.textContent = place.name;
        link.appendChild(marker);
        link.appendChild(name);
        item.appendChild(link);
        dayDialogRoute.appendChild(item);
      });
    }

    function openDay(dayId, trigger) {
      var day = findDay(dayId);
      if (!day) return;
      setActiveDay(day.id);
      fitDayBounds(day);
      if (dayDialog) populateDayDialog(day);
      if (!dayDialog || !openDialog(dayDialog, trigger)) {
        window.location.hash = "journey-" + day.id;
        return;
      }
    }

    function scrollToPlace(placeId) {
      var place = findPlace(placeId);
      if (!place) return;
      touchPreviewPlaceId = null;
      if (tooltip) {
        tooltip.hidden = true;
        tooltip.textContent = "";
      }
      setActivePlace(null);
      place.section.scrollIntoView({
        behavior: reducedMotion.matches ? "auto" : "smooth",
        block: "start",
      });
      var heading = place.section.querySelector("[data-place-name]");
      if (heading) heading.focus({ preventScroll: true });
      if (window.history && typeof window.history.replaceState === "function") {
        window.history.replaceState(null, "", "#journey-place-" + place.id);
      }
    }

    function populateRouteDialog(route) {
      if (!routeDialog) return;
      routeDialogTitle.textContent = route.label;
      routeDialogMode.textContent = route.modeLabel;
      routeDialogSource.textContent = route.sourceLabel || "Route details";
      routeDialogNote.textContent = route.note;
      routeDialogNote.hidden = !route.note;
      routeDialogSourceLink.href = route.sourceUrl || "#";
      routeDialogSourceLink.hidden = !route.sourceUrl;
      routeDialogExternalLink.href = route.externalUrl || "#";
      routeDialogExternalLink.textContent = route.externalLabel || "Open route reference";
      routeDialogExternalLink.hidden = !route.externalUrl;
      routeDialogDayLink.href = "#journey-" + route.dayId;
    }

    function openRoute(routeId, trigger) {
      var route = findRoute(routeId);
      if (!route || route.status !== "mapped") return;
      setActiveRoute(route.id);
      populateRouteDialog(route);
      if (!routeDialog || !openDialog(routeDialog, trigger)) {
        window.location.hash = "journey-" + route.dayId;
      }
    }

    function closeAndScroll(dialog, selector) {
      closeDialog(dialog, false);
      window.setTimeout(function () {
        var section = document.querySelector(selector);
        if (!section) return;
        section.scrollIntoView({ behavior: reducedMotion.matches ? "auto" : "smooth", block: "start" });
        var heading = section.querySelector("h3");
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          heading.focus({ preventScroll: true });
        }
      }, 0);
    }

    root.addEventListener("click", function (event) {
      var close = event.target.closest("[data-dialog-close]");
      if (close && root.contains(close)) {
        event.preventDefault();
        closeDialog(close.closest("dialog"), true);
        return;
      }

      var dialogPlaceLink = event.target.closest("[data-dialog-place-link]");
      if (dialogPlaceLink && root.contains(dialogPlaceLink)) {
        event.preventDefault();
        closeAndScroll(dayDialog, dialogPlaceLink.getAttribute("href"));
        return;
      }

      var dayTrigger = event.target.closest("[data-day-trigger]");
      if (dayTrigger && root.contains(dayTrigger)) {
        event.preventDefault();
        openDay(dayTrigger.getAttribute("data-day-trigger"), dayTrigger);
        return;
      }

      var modeToggle = event.target.closest("[data-route-mode-toggle]");
      if (modeToggle && root.contains(modeToggle) && !modeToggle.disabled) {
        event.preventDefault();
        var mode = modeToggle.getAttribute("data-route-mode-toggle");
        enabledModes[mode] = !enabledModes[mode];
        modeToggle.setAttribute("aria-pressed", enabledModes[mode] ? "true" : "false");
        updateRouteStyles();
        if (activeDayId) fitDayBounds(findDay(activeDayId));
        return;
      }

      var routeTrigger = event.target.closest("[data-route-trigger]");
      if (routeTrigger && root.contains(routeTrigger)) {
        event.preventDefault();
        openRoute(routeTrigger.getAttribute("data-route-trigger"), routeTrigger);
      }
    });

    if (dayDialogLink) {
      dayDialogLink.addEventListener("click", function (event) {
        event.preventDefault();
        closeAndScroll(dayDialog, dayDialogLink.getAttribute("href"));
      });
    }
    if (routeDialogDayLink) {
      routeDialogDayLink.addEventListener("click", function (event) {
        event.preventDefault();
        closeAndScroll(routeDialog, routeDialogDayLink.getAttribute("href"));
      });
    }

    if (!mapElement || places.length === 0) return;

    var invalidPlace = places.find(function (place) {
      return !Number.isFinite(place.latitude) || !Number.isFinite(place.longitude);
    });
    if (invalidPlace) {
      showStatus("The interactive map is unavailable because a place is missing valid coordinates.");
      return;
    }
    if (!window.L) {
      showStatus("The interactive map is unavailable. The complete itinerary remains available below.");
      return;
    }

    map = window.L.map(mapElement, {
      zoomControl: true,
      zoomSnap: 0.25,
      zoomDelta: 1,
      scrollWheelZoom: false,
      dragging: true,
      touchZoom: true,
      doubleClickZoom: true,
      keyboard: true,
    });
    attachTrackpadPinchZoom(map, mapElement);

    var tileErrors = 0;
    var tileLayer = window.L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }
    );
    tileLayer.on("tileerror", function () {
      tileErrors += 1;
      if (tileErrors === 4) {
        showStatus("Map tiles could not be loaded. Waypoints and the complete itinerary remain available.");
      }
    });
    tileLayer.on("load", function () {
      if (tileErrors < 4 && !routeUnavailable) hideStatus();
    });
    tileLayer.addTo(map);

    var placeBounds = window.L.latLngBounds(
      places.map(function (place) {
        return [place.latitude, place.longitude];
      })
    );
    var allBounds = window.L.latLngBounds(placeBounds);

    function markerIcon(place) {
      return window.L.divIcon({
        className: "travel-marker-icon",
        html: '<span class="travel-marker" aria-hidden="true">' + escapeHtml(place.markerLabel) + "</span>",
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      });
    }

    function positionTooltip(point) {
      if (!tooltip || !map || !point) return;
      var frame = mapElement.parentElement;
      var tooltipWidth = tooltip.offsetWidth || 280;
      var tooltipHeight = tooltip.offsetHeight || 190;
      var left = point.x + 18;
      var top = point.y - tooltipHeight - 10;
      if (left + tooltipWidth > frame.clientWidth - 10) left = point.x - tooltipWidth - 18;
      if (top < 10) top = point.y + 18;
      left = Math.max(10, Math.min(left, frame.clientWidth - tooltipWidth - 10));
      top = Math.max(10, Math.min(top, frame.clientHeight - tooltipHeight - 10));
      tooltip.style.left = left + "px";
      tooltip.style.top = top + "px";
    }

    function showPlaceTooltip(place) {
      if (!tooltip) return;
      setActiveRoute(null);
      tooltip.textContent = "";
      if (place.cover) {
        var image = document.createElement("img");
        image.className = "travel-map-tooltip__image";
        image.src = place.cover;
        image.alt = place.coverAlt;
        tooltip.appendChild(image);
      }
      var body = document.createElement("div");
      var heading = document.createElement("div");
      var name = document.createElement("strong");
      var visitSummary = document.createElement("span");
      var visits = document.createElement("p");
      var excerpt = document.createElement("p");
      var action = document.createElement("a");
      body.className = "travel-map-tooltip__body";
      heading.className = "travel-map-tooltip__heading";
      name.textContent = place.name;
      visitSummary.textContent =
        place.visitDates.length === 1 ? place.visitDates[0] : place.visitDates.length + " visits";
      visits.className = "travel-map-tooltip__visits";
      visits.textContent = place.visitDates.join(" · ");
      excerpt.className = "travel-map-tooltip__excerpt";
      excerpt.textContent = place.excerpt;
      action.className = "travel-map-tooltip__action";
      action.href = "#journey-place-" + place.id;
      action.textContent = "↓ Click to scroll to this place";
      action.addEventListener("click", function (event) {
        event.preventDefault();
        scrollToPlace(place.id);
      });
      action.addEventListener("blur", function () {
        window.setTimeout(function () {
          if (tooltip && tooltip.contains(document.activeElement)) return;
          hidePlaceTooltip(place.id, true);
        }, 0);
      });
      heading.appendChild(name);
      heading.appendChild(visitSummary);
      body.appendChild(heading);
      if (place.visitDates.length > 1) body.appendChild(visits);
      if (place.excerpt) body.appendChild(excerpt);
      body.appendChild(action);
      tooltip.appendChild(body);
      tooltip.hidden = false;
      window.requestAnimationFrame(function () {
        positionTooltip(map.latLngToContainerPoint([place.latitude, place.longitude]));
      });
    }

    function hidePlaceTooltip(placeId, force) {
      if (!tooltip || activePlaceId !== placeId) return;
      if (!force && !finePointer.matches && touchPreviewPlaceId === placeId) return;
      tooltip.hidden = true;
      tooltip.textContent = "";
      if (touchPreviewPlaceId === placeId) touchPreviewPlaceId = null;
      setActivePlace(null);
    }

    function clearPlacePreview() {
      if (tooltip) {
        tooltip.hidden = true;
        tooltip.textContent = "";
      }
      touchPreviewPlaceId = null;
      setActivePlace(null);
    }

    function showRouteTooltip(route, latlng) {
      if (!tooltip || !finePointer.matches || !route) return;
      setActivePlace(null);
      tooltip.textContent = "";
      var body = document.createElement("div");
      var mode = document.createElement("p");
      var heading = document.createElement("div");
      var name = document.createElement("strong");
      var source = document.createElement("p");
      var action = document.createElement("p");
      body.className = "travel-map-tooltip__body";
      mode.className = "travel-map-tooltip__mode";
      mode.textContent = route.modeLabel;
      heading.className = "travel-map-tooltip__heading";
      name.textContent = route.label;
      source.className = "travel-map-tooltip__source";
      source.textContent = route.sourceLabel;
      action.className = "travel-map-tooltip__count";
      action.textContent = "Select for route details";
      heading.appendChild(name);
      body.appendChild(mode);
      body.appendChild(heading);
      if (route.sourceLabel) body.appendChild(source);
      body.appendChild(action);
      tooltip.appendChild(body);
      tooltip.hidden = false;
      window.requestAnimationFrame(function () {
        positionTooltip(map.latLngToContainerPoint(latlng));
      });
    }

    function hideRouteTooltip(routeId) {
      if (!tooltip) return;
      tooltip.hidden = true;
      tooltip.textContent = "";
      if (activeRouteId === routeId && (!routeDialog || !routeDialog.open)) setActiveRoute(null);
    }

    places.forEach(function (place) {
      var marker = window.L.marker([place.latitude, place.longitude], {
        icon: markerIcon(place),
        keyboard: true,
        title: "Preview and scroll to " + place.name,
        alt: "Preview and scroll to " + place.name,
        riseOnHover: true,
      });
      markers[place.id] = marker;

      function activate() {
        setActivePlace(place.id);
        showPlaceTooltip(place);
      }

      function deactivate() {
        hidePlaceTooltip(place.id);
      }

      marker.on("mouseover", function () {
        if (finePointer.matches) activate();
      });
      marker.on("mouseout", function () {
        if (finePointer.matches) deactivate();
      });
      marker.on("click", function () {
        if (finePointer.matches) {
          scrollToPlace(place.id);
          return;
        }
        if (touchPreviewPlaceId === place.id && tooltip && !tooltip.hidden) {
          scrollToPlace(place.id);
          return;
        }
        touchPreviewPlaceId = place.id;
        activate();
      });
      marker.on("add", function () {
        var element = marker.getElement();
        if (!element) return;
        element.setAttribute("role", "button");
        element.setAttribute("aria-label", "Preview and scroll to " + place.name);
        element.addEventListener("focus", activate);
        element.addEventListener("blur", function () {
          window.setTimeout(function () {
            if (tooltip && tooltip.contains(document.activeElement)) return;
            hidePlaceTooltip(place.id, true);
          }, 0);
        });
        element.addEventListener("keydown", function (event) {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            scrollToPlace(place.id);
          }
        });
      });
      marker.addTo(map);
    });

    document.addEventListener("pointerdown", function (event) {
      if (!touchPreviewPlaceId) return;
      if (event.target.closest && event.target.closest(".travel-marker-icon, [data-map-tooltip]")) return;
      clearPlacePreview();
    });

    map.on("movestart zoomstart", function () {
      clearPlacePreview();
      if (!routeDialog || !routeDialog.open) setActiveRoute(null);
    });

    var routeModeStyles = {
      rail: { color: "#315a47", weight: 4, dashArray: "1 9" },
      cable_car: { color: "#39758e", weight: 4, dashArray: "12 5 2 5" },
      bus: { color: "#aa6a2b", weight: 4, dashArray: "10 7" },
      rideshare: { color: "#6f5968", weight: 4, dashArray: null },
      hike: { color: "#b44f39", weight: 5, dashArray: null },
    };

    function updateRouteStyles() {
      routes.forEach(function (route) {
        var visible = route.status !== "mapped" || enabledModes[route.mode] !== false;
        route.section.classList.toggle("is-mode-hidden", !visible);
      });
      if (!map) return;

      Object.keys(routeLayers).forEach(function (featureId) {
        var entry = routeLayers[featureId];
        var visible = enabledModes[entry.mode] !== false;
        if (!visible) {
          if (map.hasLayer(entry.foreground)) map.removeLayer(entry.foreground);
          if (map.hasLayer(entry.shadow)) map.removeLayer(entry.shadow);
          return;
        }
        if (!map.hasLayer(entry.shadow)) entry.shadow.addTo(map);
        if (!map.hasLayer(entry.foreground)) entry.foreground.addTo(map);

        var belongsToDay = !activeDayId || entry.dayIds.indexOf(activeDayId) !== -1;
        var isActive = entry.routeIds.indexOf(activeRouteId) !== -1;
        var style = routeModeStyles[entry.mode];
        entry.shadow.setStyle({
          opacity: activeDayId && !belongsToDay ? 0.04 : isActive ? 0.9 : 0.72,
          weight: style.weight + (isActive ? 8 : 6),
        });
        entry.foreground.setStyle({
          opacity: activeDayId && !belongsToDay ? 0.12 : 0.94,
          weight: style.weight + (isActive ? 2 : 0),
        });
        if (isActive) entry.foreground.bringToFront();
      });
    }

    function fitJourneyBounds() {
      if (!allBounds.isValid()) return;
      map.fitBounds(allBounds, {
        padding: window.innerWidth <= 720 ? [28, 28] : [56, 56],
        maxZoom: 10,
      });
    }

    function fitDayBounds(day) {
      if (!map || !day) return;
      var bounds = window.L.latLngBounds([]);
      day.placeIds.forEach(function (placeId) {
        var place = findPlace(placeId);
        if (!place) return;
        bounds.extend([place.latitude, place.longitude]);
      });
      Object.keys(routeLayers).forEach(function (featureId) {
        var entry = routeLayers[featureId];
        if (enabledModes[entry.mode] === false || entry.dayIds.indexOf(day.id) === -1) return;
        bounds.extend(entry.bounds);
      });
      if (!bounds.isValid()) return;
      map.fitBounds(bounds, {
        padding: window.innerWidth <= 720 ? [38, 38] : [74, 74],
        maxZoom: 11,
      });
    }

    function validLine(line) {
      return (
        Array.isArray(line) &&
        line.length >= 2 &&
        line.every(function (coordinate) {
          return (
            Array.isArray(coordinate) &&
            coordinate.length >= 2 &&
            Number.isFinite(coordinate[0]) &&
            Number.isFinite(coordinate[1])
          );
        })
      );
    }

    function validRouteGeometry(geojson) {
      if (!geojson || geojson.type !== "FeatureCollection" || !Array.isArray(geojson.features)) return false;
      var ids = {};
      return (
        geojson.features.length > 0 &&
        geojson.features.every(function (feature) {
          var id = feature && feature.properties && feature.properties.id;
          var geometry = feature && feature.geometry;
          if (!id || ids[id] || routesForFeature(id).length === 0 || !geometry) return false;
          ids[id] = true;
          if (geometry.type === "LineString") return validLine(geometry.coordinates);
          if (geometry.type === "MultiLineString") {
            return Array.isArray(geometry.coordinates) && geometry.coordinates.length > 0 && geometry.coordinates.every(validLine);
          }
          return false;
        })
      );
    }

    function bindRouteInteraction(entry, layer) {
      function currentRoute() {
        return routeForFeature(entry.id);
      }

      function activate(latlng) {
        var route = currentRoute();
        if (!route || enabledModes[entry.mode] === false) return;
        setActiveRoute(route.id);
        showRouteTooltip(route, latlng || entry.bounds.getCenter());
      }

      function deactivate() {
        var route = currentRoute();
        if (!route) return;
        hideRouteTooltip(route.id);
      }

      layer.on("mouseover", function (event) {
        activate(event.latlng);
      });
      layer.on("mouseout", deactivate);
      layer.on("click", function () {
        var route = currentRoute();
        if (route) openRoute(route.id, layer.getElement());
      });

      function configureElement() {
        var element = layer.getElement();
        var route = currentRoute();
        if (!element || !route || element.getAttribute("data-route-keyboard-ready") === "true") return;
        element.classList.add("travel-route-path");
        element.setAttribute("tabindex", "0");
        element.setAttribute("role", "button");
        element.setAttribute("aria-label", "View route details for " + route.label);
        element.setAttribute("data-route-keyboard-ready", "true");
        element.addEventListener("focus", function () {
          activate(entry.bounds.getCenter());
        });
        element.addEventListener("blur", deactivate);
        element.addEventListener("keydown", function (event) {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          var selectedRoute = currentRoute();
          if (selectedRoute) openRoute(selectedRoute.id, element);
        });
      }

      configureElement();
      layer.on("add", configureElement);
      map.on("moveend zoomend", configureElement);
    }

    var routeUrl = root.getAttribute("data-route-url");
    if (!routeUrl) {
      fitJourneyBounds();
      return;
    }

    window
      .fetch(routeUrl, { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("Route request failed");
        return response.json();
      })
      .then(function (geojson) {
        if (!validRouteGeometry(geojson)) throw new Error("Route geometry is invalid");
        geojson.features.forEach(function (feature) {
          var id = feature.properties.id;
          var matchingRoutes = routesForFeature(id);
          var mode = matchingRoutes[0].mode;
          var style = routeModeStyles[mode];
          if (!style) throw new Error("Route mode is invalid");

          var shadow = window.L.geoJSON(feature, {
            interactive: false,
            style: {
              color: "#f8f2e6",
              weight: style.weight + 6,
              opacity: 0.72,
              lineCap: "round",
              lineJoin: "round",
            },
          }).addTo(map);
          var foreground = window.L.geoJSON(feature, {
            className: "travel-route-path",
            style: {
              color: style.color,
              weight: style.weight,
              opacity: 0.94,
              dashArray: style.dashArray,
              lineCap: "round",
              lineJoin: "round",
            },
          }).addTo(map);
          var entry = {
            id: id,
            mode: mode,
            dayIds: matchingRoutes.map(function (route) {
              return route.dayId;
            }),
            routeIds: matchingRoutes.map(function (route) {
              return route.id;
            }),
            shadow: shadow,
            foreground: foreground,
            bounds: foreground.getBounds(),
          };
          routeLayers[id] = entry;
          foreground.eachLayer(function (layer) {
            bindRouteInteraction(entry, layer);
          });
          allBounds.extend(entry.bounds);
        });

        Array.prototype.forEach.call(root.querySelectorAll("[data-route-mode-toggle]"), function (button) {
          button.disabled = false;
        });
        updateRouteStyles();
        if (activeDayId) fitDayBounds(findDay(activeDayId));
        else fitJourneyBounds();
      })
      .catch(function () {
        routeUnavailable = true;
        showStatus("The route layers could not be loaded. Waypoints, travel modes, and the complete itinerary remain available.");
        fitJourneyBounds();
      });
  });
})();
