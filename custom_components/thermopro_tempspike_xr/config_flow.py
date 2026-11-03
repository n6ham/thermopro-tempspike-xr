"""Config flow: asks for the MQTT topics of the two probes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.util import valid_subscribe_topic
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import (
    CONF_PROBE_1_TOPIC,
    CONF_PROBE_2_TOPIC,
    CONF_TOPICS,
    DEFAULT_NAME,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


class TempSpikeConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ThermoPro TempSpike XR."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the device name and the two probe topics."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_available")

        errors: dict[str, str] = {}
        if user_input is not None:
            topics, errors = _validate_topics(user_input)
            if not errors:
                await self.async_set_unique_id(topics_unique_id(topics))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                    data={CONF_TOPICS: topics},
                )

        defaults = user_input or {}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                **_topics_schema(defaults),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the two probe topics of an existing thermometer."""
        entry = self._get_reconfigure_entry()

        errors: dict[str, str] = {}
        if user_input is not None:
            topics, errors = _validate_topics(user_input)
            if not errors:
                unique_id = topics_unique_id(topics)
                if unique_id != entry.unique_id:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                return self.async_update_reload_and_abort(
                    entry, unique_id=unique_id, data_updates={CONF_TOPICS: topics}
                )

        current = entry.data[CONF_TOPICS]
        schema = vol.Schema(
            _topics_schema(
                user_input
                or {CONF_PROBE_1_TOPIC: current[0], CONF_PROBE_2_TOPIC: current[1]}
            )
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors
        )


def _topics_schema(defaults: Mapping[str, Any]) -> dict[vol.Marker, Any]:
    return {
        vol.Required(
            key, default=defaults.get(key, DEFAULT_TOPIC_PREFIX)
        ): str
        for key in (CONF_PROBE_1_TOPIC, CONF_PROBE_2_TOPIC)
    }


def _validate_topics(user_input: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    """Return the stripped topics and any form errors."""
    topics = [
        user_input[CONF_PROBE_1_TOPIC].strip(),
        user_input[CONF_PROBE_2_TOPIC].strip(),
    ]
    errors: dict[str, str] = {}
    for key, topic in zip((CONF_PROBE_1_TOPIC, CONF_PROBE_2_TOPIC), topics):
        try:
            valid_subscribe_topic(topic)
        except vol.Invalid:
            errors[key] = "invalid_topic"
    if not errors and topics[0] == topics[1]:
        errors["base"] = "same_topic"
    return topics, errors


def topics_unique_id(topics: list[str]) -> str:
    """Unique ID of a thermometer, independent of the order of its topics."""
    return "|".join(sorted(topics))
