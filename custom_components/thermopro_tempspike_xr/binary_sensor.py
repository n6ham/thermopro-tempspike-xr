"""Docked state of each probe."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TempSpikeConfigEntry
from .const import COLORS
from .entity import TempSpikeEntity
from .hub import TempSpikeHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TempSpikeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = entry.runtime_data
    async_add_entities(DockedSensor(hub, color) for color in COLORS)


class DockedSensor(TempSpikeEntity, BinarySensorEntity):
    """On while the probe sits in the base unit."""

    def __init__(self, hub: TempSpikeHub, color: str) -> None:
        super().__init__(hub, f"{color}_docked")
        self._color = color

    @property
    def available(self) -> bool:
        return self.hub.probes[self._color].fresh

    @property
    def is_on(self) -> bool | None:
        return self.hub.probes[self._color].docked
