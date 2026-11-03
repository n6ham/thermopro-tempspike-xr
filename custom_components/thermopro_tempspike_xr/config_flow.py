"""Config flow: asks for the MQTT topics of the black and white probes."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.util import valid_subscribe_topic
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import (
    CONF_BLACK_TOPIC,
    CONF_WHITE_TOPIC,
    DEFAULT_NAME,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


class TempSpikeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ThermoPro TempSpike XR."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the device name and the two probe topics."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_available")

        errors: dict[str, str] = {}
        if user_input is not None:
            black = user_input[CONF_BLACK_TOPIC].strip()
            white = user_input[CONF_WHITE_TOPIC].strip()
            for key, topic in ((CONF_BLACK_TOPIC, black), (CONF_WHITE_TOPIC, white)):
                try:
                    valid_subscribe_topic(topic)
                except vol.Invalid:
                    errors[key] = "invalid_topic"
            if not errors and black == white:
                errors["base"] = "same_topic"

            if not errors:
                await self.async_set_unique_id(f"{black}|{white}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                    data={CONF_BLACK_TOPIC: black, CONF_WHITE_TOPIC: white},
                )

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_BLACK_TOPIC,
                    default=defaults.get(CONF_BLACK_TOPIC, DEFAULT_TOPIC_PREFIX),
                ): str,
                vol.Required(
                    CONF_WHITE_TOPIC,
                    default=defaults.get(CONF_WHITE_TOPIC, DEFAULT_TOPIC_PREFIX),
                ): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
