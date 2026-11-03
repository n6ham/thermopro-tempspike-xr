"""Constants for the ThermoPro TempSpike XR integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "thermopro_tempspike_xr"

CONF_TOPICS: Final = "topics"
CONF_PROBE_1_TOPIC: Final = "probe_1_topic"
CONF_PROBE_2_TOPIC: Final = "probe_2_topic"

# Config entry version 1 keys, used only for migration.
CONF_BLACK_TOPIC: Final = "black_topic"
CONF_WHITE_TOPIC: Final = "white_topic"

DEFAULT_NAME: Final = "ThermoPro TempSpike XR"
DEFAULT_TOPIC_PREFIX: Final = "rtl_433/events/ThermoPro-TempSpikeXR/"

# Probe colors, in display order (black on the left, white on the right).
COLORS: Final = ("black", "white")

# Readings older than this are reported as unavailable (probe out of range or off).
EXPIRE_AFTER: Final = timedelta(seconds=120)

# Battery levels are reported as a number of indicator bars.
BATTERY_MAX_BARS: Final = 3

# Dashboard card served by this integration.
URL_BASE: Final = "/thermopro_tempspike_xr"
CARD_FILENAME: Final = "thermopro-tempspike-xr-card.js"
