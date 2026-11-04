import {
  LitElement,
  html,
  svg,
} from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";

import { thermoProTP86xbStyles } from "./thermopro-tempspike-xr-card-styles.js";

const DOMAIN = "thermopro_tempspike_xr";
const CARD_TYPE = "thermopro-tempspike-xr-card";

// Default upper bound for the device width; override with the max_width option.
const DEFAULT_MAX_WIDTH = "360px";

const BATTERY_MAX_BARS = 3;

// When to draw the probes in the base unit: never, only while the docked
// sensor is on, or always.
const SHOW_PROBES_VALUES = ["never", "docked", "always"];
const DEFAULT_SHOW_PROBES = "always";

// Resolve bundled assets relative to this script, so the card works wherever
// it is served from.
const assetUrl = (file) => new URL(`./${file}`, import.meta.url).href;

// Register the 7-segment font at document level: @font-face rules declared
// inside a shadow root are ignored by Chromium-based browsers.
// Labels use Arial Narrow where installed; mobile platforms lack it, so a
// bundled condensed font (SIL OFL 1.1) is the fallback.
const BUNDLED_FONTS = [
  { family: "segment7", file: "7segment.woff", format: "woff", descriptors: {} },
  { family: "tp86xb-condensed", file: "roboto-condensed-bold.woff2", format: "woff2", descriptors: { weight: "700" } },
];
for (const { family, file, format, descriptors } of BUNDLED_FONTS) {
  if (![...document.fonts].some((font) => font.family === family)) {
    const face = new FontFace(family, `url("${assetUrl(file)}") format("${format}")`, descriptors);
    document.fonts.add(face);
    face.load().catch((err) => console.error(`Failed to load ${file}`, err));
  }
}

class ThermoProTempSpikeXrCard extends LitElement {
  static styles = thermoProTP86xbStyles;

  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  render() {
    const entities = this.resolveEntities();
    if (!entities) {
      return html`
        <ha-card>
          <div class="message">
            No ThermoPro TempSpike XR device found. Add it in Settings → Devices &amp; services.
          </div>
        </ha-card>
      `;
    }
    const black = this.readProbe(entities, "black");
    const white = this.readProbe(entities, "white");

    return html`
      <div class="thermopro-tp86xb-container ${this.showProbes() === "never" ? "no-probes" : ""}">
        <div class="thermopro-tp86xb-frame">
          <div class="thermopro-tp86xb-card">
            <div class="thermopro-tp86xb-image">
              ${this.showProbe(black) ? html`<img class="probe black" src="${assetUrl("probe-black.png")}"/>` : html``}
              ${this.showProbe(white) ? html`<img class="probe white" src="${assetUrl("probe-white.png")}"/>` : html``}
              <img class="base" src="${assetUrl("device.png")}"/>
            </div>
            <div class="thermopro-tp86xb-display">
              <div class="lcd-screen">
                <svg class="divider" xmlns="http://www.w3.org/2000/svg">
                  <line x1="50%" y1="2%" x2="50%" y2="50%"/>
                  <circle cx="50%" cy="57%" r="7%" fill="none"/>
                  <line x1="50%" y1="64%" x2="50%" y2="98%"/>
                </svg>
                ${this.renderProbe(black, "black")}
                ${this.renderProbe(white, "white")}
                <div class="unit">
                  <span>°${this.displayUnit()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Maps entity translation keys (e.g. "black_internal_temperature") to entity
  // IDs for the configured device, or the first TempSpike XR device found.
  resolveEntities() {
    const registry = Object.values(this.hass.entities || {}).filter(
      (entry) => entry.platform === DOMAIN && entry.device_id
    );
    const deviceId = this.config.device_id || registry[0]?.device_id;
    if (!deviceId) {
      return null;
    }
    const entities = {};
    for (const entry of registry) {
      if (entry.device_id === deviceId && entry.translation_key) {
        entities[entry.translation_key] = entry.entity_id;
      }
    }
    return Object.keys(entities).length ? entities : null;
  }

  readProbe(entities, color) {
    const docked = this.stateOf(entities[`${color}_docked`]);
    const battery = this.stateOf(entities[`${color}_battery`]);
    if (docked?.state === "on") {
      return { docked: true, internal: null, ambient: null, batteryBars: this.toBars(battery?.state) };
    }
    const internal = this.readTemperature(entities[`${color}_internal_temperature`]);
    const ambient = this.readTemperature(entities[`${color}_ambient_temperature`]);
    return {
      // No readings (expired or never received) most likely means the probe
      // is sitting in the base, so treat it as docked.
      docked: internal === null && ambient === null,
      internal,
      ambient,
      batteryBars: this.toBars(battery?.state),
    };
  }

  showProbes() {
    return this.config?.show_probes ?? DEFAULT_SHOW_PROBES;
  }

  // Whether to draw the probe in the base unit, per the show_probes option.
  showProbe(probe) {
    switch (this.showProbes()) {
      case "always":
        return true;
      case "never":
        return false;
      default:
        return probe.docked;
    }
  }

  stateOf(entityId) {
    return entityId ? this.hass.states[entityId] : undefined;
  }

  // Returns the temperature converted to the display unit, or null.
  readTemperature(entityId) {
    const stateObj = this.stateOf(entityId);
    const value = parseFloat(stateObj?.state);
    if (isNaN(value)) {
      return null;
    }
    const sourceUnit = (stateObj.attributes.unit_of_measurement || "°C").toUpperCase().at(-1);
    switch (sourceUnit + this.displayUnit()) {
      case "CF":
        return (value * 9) / 5 + 32;
      case "FC":
        return ((value - 32) * 5) / 9;
      default:
        return value;
    }
  }

  toBars(percent) {
    const value = parseFloat(percent);
    if (isNaN(value)) {
      return null;
    }
    return Math.max(0, Math.min(BATTERY_MAX_BARS, Math.round((value * BATTERY_MAX_BARS) / 100)));
  }

  displayUnit() {
    return this.config.display_unit
      ? this.config.display_unit.toUpperCase()
      : this.hass.config.unit_system.temperature.toUpperCase().at(-1);
  }

  // Always rendered (hidden via opacity) so the probe label doesn't shift.
  renderBattery(level, visible) {
    const known = level !== null && level !== undefined;
    const bars = known ? [2.5, 9, 15.5].slice(0, level) : [];
    return html`
      <svg class="battery ${visible && known ? "" : "hidden"}" viewBox="0 0 26 12" xmlns="http://www.w3.org/2000/svg">
        <rect class="battery-body" x="0.75" y="0.75" width="21.5" height="10.5" rx="1"/>
        <rect class="battery-cap" x="22.5" y="3.5" width="2.5" height="5"/>
        ${bars.map((x) => svg`<rect class="battery-bar" x="${x}" y="2.75" width="5" height="6.5"/>`)}
      </svg>
    `;
  }

  renderProbe(probe, color) {
    const hasInt = probe.internal !== null;
    const hasAmb = probe.ambient !== null;
    return html`
      <div class="probe-display">
        <div class="header">
          <span class="probe-id">probe ${color}</span>
          ${this.renderBattery(probe.batteryBars, hasInt || hasAmb)}
        </div>
        <div class="temp">
          <div class="temp-type"><span>Internal</span></div>
          <div class="temp-num">
            <span>${this.formatTemperature(probe.internal)}</span>
          </div>
        </div>
        <div class="temp">
          <div class="temp-type"><span>Ambient</span></div>
          <div class="temp-num">
            <span>${this.formatTemperature(probe.ambient)}</span>
          </div>
        </div>
      </div>
    `;
  }

  formatTemperature(temperature) {
    if (temperature === null) {
      return "---";
    }
    return temperature.toFixed(this.config.show_decimal ? 1 : 0);
  }

  setConfig(config) {
    if (config.device_id !== undefined && typeof config.device_id !== "string") {
      throw new Error("device_id must be a device ID string.");
    }
    if (config.display_unit !== undefined) {
      if (
        typeof config.display_unit !== "string" ||
        !["C", "F"].includes(config.display_unit.toUpperCase())
      ) {
        throw new Error("Unsupported temperature display unit. Supported units are C & F.");
      }
    }
    if (config.show_decimal !== undefined && typeof config.show_decimal !== "boolean") {
      throw new Error("show_decimal must be true or false (default).");
    }
    if (config.show_probes !== undefined && !SHOW_PROBES_VALUES.includes(config.show_probes)) {
      throw new Error(`show_probes must be one of: ${SHOW_PROBES_VALUES.join(", ")}.`);
    }
    this.style.setProperty("--tp86xb-max-width", this.parseMaxWidth(config.max_width));
    const aspectRatio = this.parseAspectRatio(config.aspect_ratio);
    if (aspectRatio === null) {
      this.style.removeProperty("--tp86xb-aspect-ratio");
    } else {
      this.style.setProperty("--tp86xb-aspect-ratio", aspectRatio);
    }
    this.config = config;
  }

  // Accepts a positive number or a "width/height" or "width:height" string,
  // e.g. 1, 0.75, "4/3", "4:3". Returns width divided by height.
  parseAspectRatio(aspectRatio) {
    if (aspectRatio === undefined || aspectRatio === null) {
      return null;
    }
    let ratio = NaN;
    if (typeof aspectRatio === "number") {
      ratio = aspectRatio;
    } else if (typeof aspectRatio === "string") {
      const parts = aspectRatio.split(/[/:]/).map((part) => Number(part.trim()));
      if (parts.length === 1) {
        ratio = parts[0];
      } else if (parts.length === 2) {
        ratio = parts[0] / parts[1];
      }
    }
    if (!Number.isFinite(ratio) || ratio <= 0) {
      throw new Error(
        `Invalid aspect_ratio: ${aspectRatio}. Use a positive number or "width/height" (e.g. 1 or "4/3").`
      );
    }
    return String(ratio);
  }

  // Accepts a number (pixels) or any CSS length, e.g. 400, "400px", "30vw".
  parseMaxWidth(maxWidth) {
    if (maxWidth === undefined || maxWidth === null) {
      return DEFAULT_MAX_WIDTH;
    }
    if (typeof maxWidth === "number" && maxWidth > 0) {
      return `${maxWidth}px`;
    }
    if (typeof maxWidth === "string" && CSS.supports("max-width", maxWidth)) {
      return maxWidth;
    }
    throw new Error(
      `Invalid max_width: ${maxWidth}. Use a number of pixels or a CSS length (e.g. "400px").`
    );
  }

  // Default config when the card is added from the card picker: no options
  // needed, the card finds the thermometer by itself.
  static getStubConfig() {
    return {};
  }

  // The height of the card in 50px units. Home Assistant uses this to
  // distribute cards over the available columns in masonry view.
  getCardSize() {
    const height = this.offsetHeight;
    return height > 0 ? Math.ceil(height / 50) : 13;
  }

  // The rules for sizing the card in the grid in sections view. The device is
  // scaled to fit whatever cell size the user picks, keeping its proportions.
  getGridOptions() {
    return {
      columns: 12,
      // Without the probes the device is 874 / 952.4 as tall: 9 * 0.918 ≈ 8.
      rows: this.showProbes() === "never" ? 8 : 9,
      min_columns: 4,
      min_rows: 4,
    };
  }
}

if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, ThermoProTempSpikeXrCard);

  // Make the card show up in the dashboard editor's card picker.
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TYPE,
    name: "ThermoPro TempSpike XR",
    description: "Display of a ThermoPro TempSpike XR (TP862b/TP863b) dual-probe wireless thermometer.",
  });
}
