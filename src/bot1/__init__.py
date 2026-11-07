"""Bot 1: no live exchange or Telegram integration."""

__version__ = "0.1.0"

# Importing the library must not configure root logging or emit raw payloads.
import logging
logging.getLogger("bot1").addHandler(logging.NullHandler())
