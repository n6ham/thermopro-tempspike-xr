# ThermoPro TempSpike XR for Home Assistant

A Home Assistant integration for the ThermoPro TempSpike XR (TP862b / TP863b) wireless dual-probe meat thermometer, with a bundled dashboard card that replicates the unit's display.

It reads the probes' radio messages decoded by [rtl_433](https://github.com/merbanan/rtl_433) and published to MQTT, and creates one device with proper Home Assistant entities, so you get history graphs and can use the readings in automations (e.g. "notify me when the black probe reaches 63 °C").

## Requirements

- Home Assistant 2024.11 or newer
- The [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) set up and connected
- rtl_433 receiving the thermometer (915 MHz in North America) and publishing events to MQTT, e.g. with the [rtl_433 add-on](https://github.com/pbkhrv/rtl_433-hass-addons). The `ThermoPro-TempSpikeXR` decoder publishes each probe on its own topic, such as `rtl_433/events/ThermoPro-TempSpikeXR/138`.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Open the menu (⋮) in the top-right corner and choose **Custom repositories**.
3. Add `https://github.com/n6ham/thermopro-tempspike-xr` with type **Integration**.
4. Find **ThermoPro TempSpike XR** in HACS and download it.
5. Restart Home Assistant.

### Manual

Copy the [`custom_components/thermopro_tempspike_xr`](custom_components/thermopro_tempspike_xr) folder into `/config/custom_components/` on your Home Assistant server and restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration** and choose **ThermoPro TempSpike XR**.
2. Enter the MQTT topic for each probe. The number at the end of the topic is the probe ID. To find it, go to **Settings → Devices & services → MQTT → Configure**, listen to `rtl_433/events/ThermoPro-TempSpikeXR/#`, and check the `color` field of the messages that arrive.

Each thermometer gets one device with these entities:

| Entity                                        | Description |
|-----------------------------------------------|-------------|
| Black / White probe internal temperature      | Meat temperature. |
| Black / White probe ambient temperature       | Temperature at the probe's handle (grill or oven temperature). |
| Black / White probe docked                    | On while the probe is in the base unit. |
| Black / White probe battery                   | Probe battery in % (0, 33, 67 or 100); the `bars` attribute holds the raw 0–3 level shown on the unit. |
| Booster battery                               | Booster battery in %, with the same `bars` attribute. |

Temperatures and docked state become unavailable when a probe hasn't been heard from for 2 minutes. Battery levels keep their last known value, including across restarts, because probe battery levels only arrive in messages sent directly by the probe (not in those relayed by the booster).

## Dashboard card

The integration also installs a dashboard card that looks like the thermometer's display. No resource needs to be added manually.

Add it from the dashboard editor (**Add card** → search for **ThermoPro TempSpike XR**), or in YAML:

```yaml
type: custom:thermopro-tempspike-xr-card
```

With a single thermometer, no options are needed: the card finds the device by itself.

| Option         | Type             | Default                    | Description |
|----------------|------------------|----------------------------|-------------|
| `device_id`    | string           | first TempSpike XR device  | Which thermometer to show, if you have more than one. |
| `display_unit` | `C` \| `F`       | Home Assistant unit system | Unit used on the display. |
| `show_decimal` | boolean          | `false`                    | Show temperatures with one decimal place (`69.4`) instead of whole numbers (`69`). |
| `max_width`    | number \| string | `360px`                    | Maximum width of the device. A number is treated as pixels; any CSS length is accepted (e.g. `"400px"`, `"30vw"`). |

In sections view the card fills the grid cell you give it and scales the device to fit; in masonry and panel views it scales with the column width, up to `max_width`.

## License

[GPL-3.0](LICENSE)
