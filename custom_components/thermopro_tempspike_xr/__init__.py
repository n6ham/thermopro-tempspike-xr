"""ThermoPro TempSpike XR (TP862b / TP863b) integration via rtl_433 and MQTT."""

from __future__ import annotations

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .frontend import async_register_card
from .hub import TempSpikeHub

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

TempSpikeConfigEntry = ConfigEntry[TempSpikeHub]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the dashboard card once, independent of config entries."""
    await async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: TempSpikeConfigEntry) -> bool:
    """Set up a thermometer from a config entry."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT is not available")

    hub = TempSpikeHub(hass, entry)
    await hub.async_start()
    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TempSpikeConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        entry.runtime_data.async_stop()
    return unloaded
