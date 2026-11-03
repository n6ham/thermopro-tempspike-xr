"""Temperature and battery sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TempSpikeConfigEntry
from .const import BATTERY_MAX_BARS, COLORS
from .entity import TempSpikeEntity
from .hub import TempSpikeHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TempSpikeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = entry.runtime_data
    entities: list[SensorEntity] = []
    for color in COLORS:
        entities.append(TemperatureSensor(hub, color, "internal"))
        entities.append(TemperatureSensor(hub, color, "ambient"))
        entities.append(ProbeBatterySensor(hub, color))
    entities.append(BoosterBatterySensor(hub))
    async_add_entities(entities)


def _bars_to_percent(bars: int | None) -> int | None:
    return None if bars is None else round(bars * 100 / BATTERY_MAX_BARS)


def _percent_to_bars(percent: Any) -> int | None:
    try:
        return round(float(percent) * BATTERY_MAX_BARS / 100)
    except (TypeError, ValueError):
        return None


class TemperatureSensor(TempSpikeEntity, SensorEntity):
    """Internal or ambient temperature of a probe."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, hub: TempSpikeHub, color: str, kind: str) -> None:
        super().__init__(hub, f"{color}_{kind}_temperature")
        self._color = color
        self._kind = kind

    @property
    def available(self) -> bool:
        return self.hub.probes[self._color].fresh

    @property
    def native_value(self) -> float | None:
        probe = self.hub.probes[self._color]
        value = probe.internal_c if self._kind == "internal" else probe.ambient_c
        return None if value is None else round(value, 1)


class _BatterySensor(TempSpikeEntity, RestoreSensor):
    """Battery level in percent; the raw number of bars is an attribute.

    The value is restored after a restart, since probe battery levels only
    arrive in messages sent directly by the probe.
    """

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def _get_bars(self) -> int | None:
        raise NotImplementedError

    def _set_bars(self, bars: int) -> None:
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._get_bars() is None and (last := await self.async_get_last_sensor_data()):
            bars = _percent_to_bars(last.native_value)
            if bars is not None:
                self._set_bars(bars)

    @property
    def native_value(self) -> int | None:
        return _bars_to_percent(self._get_bars())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"bars": self._get_bars()}


class ProbeBatterySensor(_BatterySensor):
    def __init__(self, hub: TempSpikeHub, color: str) -> None:
        super().__init__(hub, f"{color}_battery")
        self._color = color

    def _get_bars(self) -> int | None:
        return self.hub.probes[self._color].battery_bars

    def _set_bars(self, bars: int) -> None:
        self.hub.probes[self._color].battery_bars = bars


class BoosterBatterySensor(_BatterySensor):
    def __init__(self, hub: TempSpikeHub) -> None:
        super().__init__(hub, "booster_battery")

    def _get_bars(self) -> int | None:
        return self.hub.booster_battery_bars

    def _set_bars(self, bars: int) -> None:
        self.hub.booster_battery_bars = bars
