# Receiving the thermometer with rtl_433 and MQTT

This guide sets up everything the integration needs to receive the thermometer's radio messages in Home Assistant:

1. **Mosquitto broker**: the MQTT broker that carries the messages.
2. **rtl_433**: receives the probes' radio signal with an SDR dongle, decodes it and publishes it to MQTT.
3. **MQTT Explorer** (optional): lets you watch the messages and find the probe IDs.

Then [set up the integration](../README.md#setup).

> Home Assistant now calls add-ons **apps** (**Settings → Apps**). Older guides and some app READMEs still say "add-ons" or "Add-on Store".

## What you need

- Home Assistant OS (or Supervised). Apps aren't available on Home Assistant Container or Core; there you can run the same programs yourself, e.g. in Docker.
- An [SDR dongle supported by rtl_433](https://triq.org/rtl_433/HARDWARE.html), such as an RTL-SDR Blog V3 or V4, plugged into the machine running Home Assistant.
- An antenna for the thermometer's band. The North American TempSpike XR transmits on 915 MHz.

## 1. Mosquitto broker

1. Go to **Settings → Apps → Install app**, find **Mosquitto broker** and select **Install**.
2. Turn on **Start on boot** and **Watchdog**, then select **Start**. Check the **Log** tab after a minute or so to confirm it's running.
3. Go to **Settings → Devices & services**. **MQTT** shows up as a discovered integration: select **Add**, then **Submit**.
4. Add a login for each MQTT client. Mosquitto doesn't allow anonymous connections, so rtl_433 and MQTT Explorer each need a username and password. On the Mosquitto broker app's **Configuration** tab, under **Logins**, select **Add** and create:
   - `rtl_433`, used by rtl_433 to publish the probes' messages
   - `explorer`, used by MQTT Explorer (skip it if you don't install MQTT Explorer)

   Give each one its own password, then select **Save** and restart the app. The names `homeassistant` and `addons` are reserved. Avoid `$`, `` ` `` and `\` in the rtl_433 password, or escape them with `\`: the rtl_433 app processes its config file as a shell template.

## 2. rtl_433

1. Add the app repository: go to **Settings → Apps → Install app**, open the menu (⋮) in the top-right corner, choose **Repositories**, add `https://github.com/pbkhrv/rtl_433-hass-addons` and select **Add**.
2. Find **rtl_433** in the list and select **Install**. You only need this one app (see [Don't install rtl_433 MQTT Auto Discovery](#dont-install-rtl_433-mqtt-auto-discovery) below).
3. Plug in the SDR dongle, turn on **Start on boot** and **Watchdog**, and select **Start**. On first start the app creates a default configuration file, `/homeassistant/rtl_433/rtl_433.conf.template`.
4. Edit that file (e.g. with the **File editor** or **Studio Code Server** app) so it looks like this:

   ```
   output mqtt://core-mosquitto:1883,user=rtl_433,pass=RTL_433_PASSWORD,events=rtl_433/events[/model][/id]
   report_meta time:iso:usec:tz

   frequency 915M

   ## Protocols to enable (command line option "-R")
   protocol 294 # ThermoPro TempSpike XR TP862b / TP863b Wireless Dual-Probe Meat Thermometer
   # Add a "protocol" line for each other device you want to receive.
   ```

   - `core-mosquitto:1883` is the Mosquitto broker app's address inside Home Assistant.
   - `user` and `pass` are the `rtl_433` login you added in [step 4 of Mosquitto broker](#1-mosquitto-broker): replace `RTL_433_PASSWORD` with the password you gave that login.
   - `events=rtl_433/events[/model][/id]` publishes each probe on its own topic, such as `rtl_433/events/ThermoPro-TempSpikeXR/138`, which is what the integration subscribes to. By default rtl_433 publishes all events on a single topic.
   - `protocol 294` turns on the thermometer's decoder (`ThermoPro-TempSpikeXR`). Once any protocol is listed, rtl_433 decodes only the listed ones, which keeps neighbors' weather stations and cars' tire pressure sensors out of MQTT. To receive other devices too, add a `protocol` line for each; their numbers are in the [list of supported protocols](https://github.com/merbanan/rtl_433#supported-device-protocols).
   - The default file also has a list of `protocol -…` lines, which turn off tire pressure sensors. With `protocol 294` listed they have no effect, so you can delete them.
   - Optionally, add `output kv` to also print every decoded message in the app's **Log** tab, which helps when checking reception. It can be noisy, so remove it once things work.
5. Restart the app and check the **Log** tab. It should show rtl_433 starting on 915 MHz and connecting to MQTT.

### Don't install rtl_433 MQTT Auto Discovery

The repository also has an **rtl_433 MQTT Auto Discovery** app. It creates Home Assistant entities from rtl_433 messages, which would duplicate the entities this integration creates for the thermometer. You don't need it for the thermometer.

## 3. MQTT Explorer (optional)

MQTT Explorer shows every topic on the broker and the messages arriving on it. It's the easiest way to check that rtl_433 is receiving the thermometer and to find the probe IDs.

1. Add the app repository `https://github.com/GollumDom/addon-repository` the same way as in step 1 of [rtl_433](#2-rtl_433).
2. Find **MQTT Explorer**, select **Install**, then **Start**, and open its web UI.
3. Connect to the broker:
   - **Host:** `core-mosquitto` (the Mosquitto app's hostname inside Home Assistant). Use your Home Assistant's IP address instead if `core-mosquitto` doesn't connect.
   - **Port:** `1883`
   - **Username / Password:** the `explorer` login you added in [step 4 of Mosquitto broker](#1-mosquitto-broker).
4. Take the probes out of the base so they start transmitting, and expand `rtl_433 → events → ThermoPro-TempSpikeXR`. Each probe shows up as a topic named after its ID, e.g. `138`. You need both IDs; which one is black and which is white doesn't matter.

Without MQTT Explorer, you can do the same check in **Settings → Devices & services → MQTT → Configure**: listen to `rtl_433/events/ThermoPro-TempSpikeXR/#`.

## Next step

[Add the integration](../README.md#setup) and enter the two probe topics, e.g. `rtl_433/events/ThermoPro-TempSpikeXR/138`.

## Troubleshooting

- **No `rtl_433` topics at all:** check the rtl_433 app's log. "usb_claim_interface error" or "No supported devices found" means the dongle isn't visible to the app: re-plug it and restart the app.
- **rtl_433 runs but nothing from the thermometer:** check that `frequency 915M` is in the config and that the probes are out of the base. Docked probes transmit rarely.
- **rtl_433 log shows an MQTT connection or authorization error:** check that the `user` and `pass` in the `output` line match the `rtl_433` login in the Mosquitto broker app's configuration, and that you restarted Mosquitto after adding it.
- **Messages arrive on `rtl_433/<hostname>/events` instead:** the `events=…` part of the `output` line is missing; see step 4 of [rtl_433](#2-rtl_433).
