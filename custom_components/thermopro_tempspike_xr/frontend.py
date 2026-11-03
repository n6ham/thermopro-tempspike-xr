"""Serve the bundled dashboard card and load it on every dashboard."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import CARD_FILENAME, DOMAIN, URL_BASE


async def async_register_card(hass: HomeAssistant) -> None:
    """Expose the www folder and add the card as a frontend module."""
    www = Path(__file__).parent / "www"
    # No long-term caching: the card's relative imports (styles, images, font)
    # are not versioned, so they must be revalidated after an update.
    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(www), cache_headers=False)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILENAME}?v={integration.version}")
