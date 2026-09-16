/*
 * Live countdown for the Moonhack hero.
 *
 * Expects a wrapper with data-mh-countdown, ISO data-start/data-end
 * attributes, and <b data-mh-unit="days|hours|minutes|seconds"> targets.
 * Hugo renders a build-time day count as the no-JS fallback.
 */
(function () {
  var wrap = document.querySelector("[data-mh-countdown]");
  if (!wrap) return;

  var start = Date.parse(wrap.dataset.start);
  var end = Date.parse(wrap.dataset.end || wrap.dataset.start);
  if (isNaN(start)) return;

  var list = wrap.querySelector(".mh-countdown");
  var message = wrap.querySelector(".mh-countdown__message");
  var units = {};
  ["days", "hours", "minutes", "seconds"].forEach(function (unit) {
    units[unit] = wrap.querySelector('[data-mh-unit="' + unit + '"]');
  });

  function announce(text) {
    if (list) list.hidden = true;
    if (message) {
      message.textContent = text;
      message.hidden = false;
    }
  }

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function tick() {
    var remaining = start - Date.now();

    if (remaining <= 0) {
      announce(
        Date.now() <= end
          ? wrap.dataset.live || "Happening now"
          : wrap.dataset.done || "That's a wrap",
      );
      return false;
    }

    var seconds = Math.floor(remaining / 1000);
    var values = {
      days: Math.floor(seconds / 86400),
      hours: Math.floor((seconds % 86400) / 3600),
      minutes: Math.floor((seconds % 3600) / 60),
      seconds: seconds % 60,
    };

    Object.keys(units).forEach(function (unit) {
      if (!units[unit]) return;
      units[unit].textContent =
        unit === "days" ? String(values[unit]) : pad(values[unit]);
    });

    return true;
  }

  if (tick()) {
    var timer = setInterval(function () {
      if (!tick()) clearInterval(timer);
    }, 1000);
  }
})();
