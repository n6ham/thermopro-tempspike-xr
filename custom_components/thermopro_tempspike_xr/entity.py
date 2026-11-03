"""Base entity for ThermoPro TempSpike XR."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .hub import TempSpikeHub


class TempSpikeEntity(Entity):
    """Entity updated by the hub's dispatcher signal."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: TempSpikeHub, key: str) -> None:
        self.hub = hub
        self._attr_translation_key = key
        self._attr_unique_id = f"{hub.entry_id}_{key}"
        self._attr_device_info = hub.device_info

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.hub.signal, self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
