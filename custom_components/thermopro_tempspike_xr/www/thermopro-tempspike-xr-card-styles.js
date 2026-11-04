import { css } from "https://unpkg.com/lit-element@2.0.1/lit-element.js?module";

const probeImageHorizontalPosition = css`15%`;
const probeImageWidth = css`13%`;

export const thermoProTP86xbStyles = css`
  /* The segment7 and tp86xb-condensed fonts are registered at document level in the card script. */

  :host {
    display: block;
    height: 100%;
  }

  .message {
    padding: 16px;
  }

  /*
   * Area available for the device. In sections view the grid gives the card a
   * fixed height, so this fills the cell. In masonry view the card height is
   * not fixed, so the percentage height resolves to auto and aspect-ratio
   * derives the height from the width instead.
   */
  /*
   * Device box = base image (560 x 874) plus, when the probes are drawn, a
   * top margin of 14% of the width for them: 560 x (874 + 0.14 * 560) =
   * 560 x 952.4. The LCD overlay is positioned in the same box, so its
   * top/height differ between the two layouts.
   */
  .thermopro-tp86xb-container {
    --device-aspect-ratio: 560 / 952.4;
    --device-width-to-height: 0.588; /* 560 / 952.4 */
    --base-margin-top: 14%;
    --display-top: 41.6%;
    --display-height: 43%;
  }

  .thermopro-tp86xb-container.no-probes {
    --device-aspect-ratio: 560 / 874;
    --device-width-to-height: 0.6407; /* 560 / 874 */
    --base-margin-top: 0;
    --display-top: 36.36%; /* (0.416 * 952.4 - 78.4) / 874 */
    --display-height: 46.86%; /* 0.43 * 952.4 / 874 */
  }

  .thermopro-tp86xb-container {
    --frame-ratio: var(--tp86xb-aspect-ratio, var(--device-width-to-height));
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    max-width: var(--tp86xb-max-width, 360px);
    height: 100%;
    margin: 0 auto;
    aspect-ratio: var(--frame-ratio);
    container-type: size;
  }

  /* Box with the aspect_ratio proportions; the device is centered in it. */
  .thermopro-tp86xb-frame {
    display: flex;
    justify-content: center;
    align-items: center;
    width: min(100cqw, 100cqh * var(--frame-ratio));
    aspect-ratio: var(--frame-ratio);
  }

  /* The device: the largest box with the device's proportions that fits. */
  .thermopro-tp86xb-card {
    position: relative;
    isolation: isolate; /* keep the probe images (z-index: -1) inside the card */
    text-align: center;
    width: min(100%, 100% * var(--device-width-to-height) / var(--frame-ratio));
    aspect-ratio: var(--device-aspect-ratio);
    --font-digits: segment7, monospace;
    --font-labels: 'Arial Narrow', tp86xb-condensed, sans-serif; /* Condensed look for labels */
  }
  
  .thermopro-tp86xb-image .probe {
    display: block;
    position: absolute;
    width: ${probeImageWidth};
    top: 0;
    clip-path: inset(0 0 50%);
    z-index: -1;
  }

  .thermopro-tp86xb-image .probe.black {
    left: ${probeImageHorizontalPosition};
  }

  .thermopro-tp86xb-image .probe.white {
    right: ${probeImageHorizontalPosition};
  }
  
  .thermopro-tp86xb-image .base {
    display: block;
    width: 100%;
    margin-top: var(--base-margin-top);
  }

  .thermopro-tp86xb-display {
    position: absolute;
    top: var(--display-top);
    left: 50%;
    width: 70%;
    height: var(--display-height);
    transform: translate(-50%, -50%);
    color: rgba(0, 0, 0, 0.5);
  }
  
  .lcd-screen {
    width: 100%; 
    height: 100%;
    container-type: inline-size;
    display: grid;
    grid-template-columns: 50% 50%;
    grid-template-rows: 100%;
    text-shadow: rgba(0, 0, 0, 0.1) 0.06cqw 0.06cqw 0cqw;
  }
  
  .unit {
    display: flex;
    justify-content: center;
    align-items: center;
    position: absolute;
    transform: translate(-50%, -50%);
    top: 57%;
    left: 50%;
    width: 12cqw;
    height: 12cqw;
  }
  
  .unit span {
    font-size: 10cqw;
    font-weight: bold;
    transform: translate(-16%, 0%);
  }

  .probe-display {
    display: grid;
    grid-template-columns: 100%;
    grid-template-rows: 10% 45% 45%;
    position: relative;
    padding: 0 3cqw;
  }

  .probe-display .header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 2cqw;
    font-family: var(--font-labels);
    font-weight: bold;
    font-size: 5cqw;
    text-transform: uppercase;
    padding-top: 5cqw;
  }

  .probe-display .header span {
    white-space: nowrap;
    transform: scaleY(1.2);
  }

  .probe-display .header .battery {
    height: 3.6cqw;
    width: auto;
    flex-shrink: 0;
  }

  .probe-display .header .battery.hidden {
    opacity: 0;
  }

  .battery .battery-body {
    fill: none;
    stroke: currentColor;
    stroke-width: 1.5;
  }

  .battery .battery-cap,
  .battery .battery-bar {
    fill: currentColor;
  }

  .divider {
    position: absolute;
    width: 100%;
    height: 100%;
  }

  .divider line, .divider circle {
    stroke: rgba(0, 0, 0, 0.5);
    stroke-width: 0.75cqw;
  }

  .probe-display .temp:nth-child(2) {
    padding-top: 6cqw;
  }

  .probe-display .temp:nth-child(3) {
    padding-top: 12cqw;
  }

  /* text-align, not justify-self: Safari doesn't support justify-self in
     block layout, so labels and digits fell back to the card's centering. */
  .temp-type {
    text-align: left;
    transform: scaleY(1.2);
  }

  .temp-type span {
    white-space: nowrap;
    font-family: var(--font-labels);
    font-weight: bold;
    font-size: 5cqw;
    text-transform: uppercase;
  }

  .temp-num {
    text-align: right;
    /* Makes up for the 1cqw shorter digits so they keep their position. */
    padding-top: 1cqw;
  }

  .temp-num span {
    white-space: nowrap;
    font-family: var(--font-digits);
    /* Four 7-segment digits are 1.88em wide (the period has no width): at
       23cqw they need 43.2cqw of the 44cqw column (50cqw minus 2 * 3cqw
       padding), so "---.-" and "100.0" fit on one line. */
    font-size: 23cqw;
    line-height: 1;
  }
`;
