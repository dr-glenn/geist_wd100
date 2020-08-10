Read a Geist Watchdog 100 device.

Geist WD 100 will be used to monitor MIRA telescope dome environment and protect
the mirror from dew forming.

geist_data.py runs on a desktop system.

geist8266.py runs in microPython on ESP8266 or ESP32.

geist_pi is meant to run as a cron job on a Raspberry Pi. It will log environment,
send alerts to users and be able to turn on a mirror heater.

geist.php shows the current Geist conditions. We will probably want the page to automatically refresh
every 5 minutes. Bruce Weaver suggssts that the page background color changes according to dewpoint risk:
Light Grey for safe.
Yellow to indicate approaching a danger of dew settling on mirror @ 10 degrees within dew point
Bright red when within 5 degrees
Text data displayed on web page as well as a manual turn on and off of heaters button
Clicking the on button should start a timer say 30 minutes run time
and auto shutoff to prevent the heaters from being left on.
