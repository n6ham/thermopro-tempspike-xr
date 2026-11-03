"""MQTT listener that keeps the latest state of both TempSpike XR probes.

Messages are produced by the rtl_433 ``ThermoPro-TempSpikeXR`` decoder. Each
probe publishes on its own topic. A message is sent either by the probe itself
(``is_probe`` = 1, carries the probe battery level) or relayed by the booster
(``is_booster`` = 1, carries the booster battery level instead). Flags such as
``is_docked``, ``is_probe`` and ``is_booster`` are omitted when they are 0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import partial
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    BATTERY_MAX_BARS,
    COLORS,
    CONF_BLACK_TOPIC,
    CONF_WHITE_TOPIC,
    DOMAIN,
    EXPIRE_AFTER,
)

_LOGGER = logging.getLogger(__name__)

EXPIRY_CHECK_INTERVAL = EXPIRE_AFTER / 12


@dataclass
class ProbeState:
    """Latest known state of one probe."""

    internal_c: float | None = None
    ambient_c: float | None = None
    docked: bool | None = None
    battery_bars: int | None = None
    last_seen: datetime | None = None
    fresh: bool = False


class TempSpikeHub:
    """Subscribes to both probe topics and notifies entities about updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry_id = entry.entry_id
        self.topics = {
            "black": entry.data[CONF_BLACK_TOPIC],
            "white": entry.data[CONF_WHITE_TOPIC],
        }
        self.probes = {color: ProbeState() for color in COLORS}
        self.booster_battery_bars: int | None = None
        self.signal = f"{DOMAIN}_update_{entry.entry_id}"
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ThermoPro",
            model="TempSpike XR (TP862b / TP863b)",
        )
        self._unsubscribers: list[CALLBACK_TYPE] = []

    async def async_start(self) -> None:
        """Subscribe to the probe topics."""
        for color, topic in self.topics.items():
            self._unsubscribers.append(
                await mqtt.async_subscribe(
                    self.hass, topic, partial(self._handle_message, color), qos=0
                )
            )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass, self._check_expiry, EXPIRY_CHECK_INTERVAL
            )
        )

    @callback
    def async_stop(self) -> None:
        """Unsubscribe from everything."""
        while self._unsubscribers:
            self._unsubscribers.pop()()

    @callback
    def _handle_message(self, color: str, msg: mqtt.ReceiveMessage) -> None:
        try:
            payload = json.loads(msg.payload)
        except ValueError:
            _LOGGER.debug("Ignoring non-JSON message on %s: %s", msg.topic, msg.payload)
            return
        if not isinstance(payload, dict):
            return

        reported_color = payload.get("color")
        if reported_color and reported_color != color:
            _LOGGER.warning(
                "Message on %s reports a %s probe, but the topic is configured for the %s probe",
                msg.topic,
                reported_color,
                color,
            )

        probe = self.probes[color]
        probe.internal_c = _temperature_c(payload, "temperature_int")
        probe.ambient_c = _temperature_c(payload, "temperature_amb")
        probe.docked = _flag(payload, "is_docked")

        if _flag(payload, "is_probe"):
            bars = _battery_bars(payload.get("probe_batery"))
            if bars is not None:
                probe.battery_bars = bars
        if _flag(payload, "is_booster"):
            bars = _battery_bars(payload.get("booster_battery"))
            if bars is not None:
                self.booster_battery_bars = bars

        probe.last_seen = dt_util.utcnow()
        probe.fresh = True
        async_dispatcher_send(self.hass, self.signal)

    @callback
    def _check_expiry(self, now: datetime) -> None:
        changed = False
        for probe in self.probes.values():
            if probe.fresh and (
                probe.last_seen is None or now - probe.last_seen > EXPIRE_AFTER
            ):
                probe.fresh = False
                changed = True
        if changed:
            async_dispatcher_send(self.hass, self.signal)


def _flag(payload: dict[str, Any], key: str) -> bool:
    """rtl_433 omits these flags when they are 0."""
    try:
        return int(payload.get(key, 0)) == 1
    except (TypeError, ValueError):
        return False


def _temperature_c(payload: dict[str, Any], prefix: str) -> float | None:
    """Read a temperature in °C, accepting rtl_433's customary (°F) output too."""
    try:
        if f"{prefix}_C" in payload:
            return float(payload[f"{prefix}_C"])
        if f"{prefix}_F" in payload:
            return (float(payload[f"{prefix}_F"]) - 32) * 5 / 9
    except (TypeError, ValueError):
        pass
    return None


def _battery_bars(value: Any) -> int | None:
    try:
        bars = int(value)
    except (TypeError, ValueError):
        return None
    return bars if 0 <= bars <= BATTERY_MAX_BARS else None
