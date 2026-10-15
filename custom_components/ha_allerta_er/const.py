"""Constants for the Allerta Emilia-Romagna integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ha_allerta_er"

VERSION: Final = "0.1.0"

# AllertaMeteoER (Regione Emilia-Romagna) - public CAP 1.2 feed.
# One <alert> with a single <note> and one <info> block per alert area.
CAP_URL: Final = "https://allertameteo.regione.emilia-romagna.it/o/xmlcap"

# Public web page ("Allerte e Bollettini Meteo") shown as the device link.
SITE_URL: Final = (
    "https://allertameteo.regione.emilia-romagna.it/allerte-e-bollettini"
)

USER_AGENT: Final = f"ha_allerta_er/{VERSION} (Home Assistant custom integration)"

# Refresh interval, in seconds. The feed changes a few times per day, so one
# hour is plenty; allowed range lets the user go from every minute to daily.
DEFAULT_SCAN_INTERVAL: Final = 3600
MIN_SCAN_INTERVAL: Final = 60
MAX_SCAN_INTERVAL: Final = 86400

# Short-lived cache shared by every area coordinator: all areas live in the
# same document, so refreshes happening close together result in a single HTTP
# request.
FEED_TTL: Final = timedelta(seconds=60)

CONF_AREA: Final = "area"
CONF_SCAN_INTERVAL: Final = "scan_interval"

ATTRIBUTION: Final = "Dati: AllertaMeteoER (Regione Emilia-Romagna)"

DISCLAIMER: Final = (
    "Integrazione NON ufficiale, non affiliata ad AllertaMeteoER o alla "
    "Regione Emilia-Romagna. La disponibilita' e la continuita' del servizio "
    "non sono in alcun modo garantite."
)
