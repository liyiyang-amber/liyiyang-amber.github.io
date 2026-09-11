(function () {
  'use strict';

  var root = document.querySelector('.invisible-cities');
  if (!root || root.classList.contains('ic-enhanced')) return;

  var layout = root.querySelector('.ic-layout');
  var grid = root.querySelector('.ic-grid');
  var reader = root.querySelector('.ic-reader');
  var readerTools = root.querySelector('.ic-reader-tools');
  var closeButton = root.querySelector('.ic-close');
  var backdrop = root.querySelector('.ic-drawer-backdrop');
  var image = root.querySelector('.ic-venice');
  var quote = root.querySelector('[data-ic-quote]');
  var tooltip = root.querySelector('.ic-tooltip');
  var defaultQuote = quote.textContent;
  var entries = Array.from(root.querySelectorAll('.ic-entry'));
  var links = Array.from(root.querySelectorAll('[data-ic-target]'));
  var byId = new Map(entries.map(function (entry) { return [entry.id, entry]; }));
  var selected = null;
  var returnTo = null;
  var tooltipLink = null;
  var modal = false;
  var outsideReader = [
    document.querySelector('.masthead'),
    document.querySelector('.ic-author-sidebar'),
    root.querySelector('.ic-header'),
    grid,
    root.querySelector('.ic-attribution')
  ].filter(Boolean);

  function focusReading() {
    if (selected) selected.querySelector('.ic-name').focus({ preventScroll: true });
  }

  function revealControl(container, control) {
    var bounds = container.getBoundingClientRect();
    var item = control.getBoundingClientRect();
    if (item.top < bounds.top + 8) container.scrollTop += item.top - bounds.top - 8;
    else if (item.bottom > bounds.bottom - 8) container.scrollTop += item.bottom - bounds.bottom + 8;
  }

  function syncDrawer() {
    modal = !!selected && root.clientWidth <= 960;
    reader.setAttribute('role', modal ? 'dialog' : 'complementary');
    if (modal) reader.setAttribute('aria-modal', 'true');
    else reader.removeAttribute('aria-modal');
    backdrop.hidden = !modal;
    outsideReader.forEach(function (region) { region.inert = modal; });
    // A desktop-to-mobile resize may leave focus in the now-inert city grid.
    if (modal && !reader.contains(document.activeElement)) focusReading();
  }

  function hideTooltip() {
    tooltip.hidden = true;
    if (tooltipLink) tooltipLink.removeAttribute('aria-describedby');
    tooltipLink = null;
  }

  function showTooltip(link) {
    if (!link.dataset.icNote) return;
    hideTooltip();
    tooltipLink = link;
    tooltip.textContent = link.dataset.icNote;
    tooltip.hidden = false;
    link.setAttribute('aria-describedby', tooltip.id);
    var bounds = root.getBoundingClientRect();
    var anchor = link.getBoundingClientRect();
    var gridBounds = grid.getBoundingClientRect();
    if (anchor.bottom < gridBounds.top || anchor.top > gridBounds.bottom) {
      hideTooltip();
      return;
    }
    var width = tooltip.offsetWidth;
    var height = tooltip.offsetHeight;
    var left = anchor.left - bounds.left + (anchor.width - width) / 2;
    var top = anchor.top - bounds.top - height - 8;
    if (anchor.top - height - 8 < Math.max(bounds.top, 0)) {
      top = anchor.bottom - bounds.top + 8;
    }
    tooltip.style.left = Math.max(12, Math.min(left, bounds.width - width - 12)) + 'px';
    tooltip.style.top = Math.max(8, Math.min(top, bounds.height - height - 8)) + 'px';
  }

  function render(entry) {
    selected = entry;
    hideTooltip();
    entries.forEach(function (item) { item.hidden = item !== entry; });
    links.forEach(function (link) {
      link.setAttribute('aria-pressed', String(!!entry && link.dataset.icTarget === entry.id));
    });
    reader.hidden = !entry;
    layout.classList.toggle('ic-panel-open', !!entry);
    layout.classList.toggle('ic-has-city', !!entry && entry.dataset.icKind === 'city');
    image.style.filter = entry ? entry.dataset.icFilter : root.dataset.defaultFilter;
    quote.textContent = !entry ? defaultQuote : entry.dataset.icKind === 'city'
      ? '“' + entry.dataset.icName + '” — ' + entry.dataset.icTheme
      : entry.dataset.icName;
    if (entry) reader.setAttribute('aria-labelledby', entry.querySelector('.ic-name').id);
    else reader.removeAttribute('aria-labelledby');
    syncDrawer();
  }

  function closePanel() {
    render(null);
    if (returnTo) {
      returnTo.focus({ preventScroll: true });
      // Reveal the restored control by scrolling only its own grid.
      revealControl(grid, returnTo);
      // Restoring keyboard focus should not leave a stale hover tooltip open.
      hideTooltip();
    }
  }

  function select(link) {
    var entry = byId.get(link.dataset.icTarget);
    if (!entry) return;
    if (entry === selected) {
      closePanel();
      return;
    }
    returnTo = grid.querySelector('[data-ic-target="' + entry.id + '"]');
    render(entry);
    reader.scrollTop = 0;
    focusReading();
  }

  links.forEach(function (link) {
    // Real fragment links remain usable if JavaScript is unavailable.
    link.setAttribute('role', 'button');
    link.setAttribute('aria-controls', reader.id);
    // The site attaches jQuery smooth-scroll to every anchor. Intercept these
    // controls before that handler tries to scroll to a still-hidden reading.
    link.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      select(link);
    }, true);
    link.addEventListener('keydown', function (event) {
      if (event.key === ' ') {
        event.preventDefault();
        select(link);
      }
    });
    if (link.dataset.icNote) {
      link.addEventListener('pointerenter', function (event) {
        if (event.pointerType !== 'touch') showTooltip(link);
      });
      link.addEventListener('pointerleave', hideTooltip);
      link.addEventListener('focus', function () { showTooltip(link); });
      link.addEventListener('blur', hideTooltip);
    }
  });
  closeButton.addEventListener('click', closePanel);
  backdrop.addEventListener('click', closePanel);
  root.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      hideTooltip();
      if (selected) {
        event.preventDefault();
        closePanel();
      }
    }
    if (event.key === 'Tab' && modal) {
      var controls = Array.from(reader.querySelectorAll('button, a[href], [tabindex="0"]'))
        .filter(function (control) { return !control.disabled && control.getClientRects().length; });
      var first = controls[0];
      var last = controls[controls.length - 1];
      var active = document.activeElement;
      if (!controls.includes(active) || (event.shiftKey && active === first) || (!event.shiftKey && active === last)) {
        event.preventDefault();
        var target = event.shiftKey ? last : first;
        target.focus({ preventScroll: true });
        revealControl(reader, target);
      }
    }
  });
  function updateTooltipPosition() {
    // Keyboard focus can scroll a city into view after its focus event.
    if (tooltipLink && document.activeElement === tooltipLink) showTooltip(tooltipLink);
    else hideTooltip();
  }
  window.addEventListener('scroll', updateTooltipPosition, { passive: true, capture: true });
  window.addEventListener('resize', function () {
    syncDrawer();
    updateTooltipPosition();
  }, { passive: true });
  if (window.ResizeObserver) new ResizeObserver(syncDrawer).observe(root);
  document.body.classList.add('ic-page-enhanced');
  root.classList.add('ic-enhanced');
  readerTools.hidden = false;
  render(byId.get(window.location.hash.slice(1)) || null);
  if (selected) {
    returnTo = grid.querySelector('[data-ic-target="' + selected.id + '"]');
    reader.scrollTop = 0;
    focusReading();
  }
}());
