#!/usr/bin/env python

# URL formats

# gpslogger https://github.com/mendhak/gpslogger format
# https://example.com/api/gpslogger?latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT&speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT

# phonetrack
# https://example.com/index.php/apps/phonetrack/log/gpslogger/<api key>/<name>?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT

receivers = dict()

verbose = True
delay_seconds = 10
use_gps = True
use_wifi = True
timeout_location = 10
timeout_report = 10
wifi_device = 'wlp4s0'

# receivers['gpslogger'] = {
#     'url': 'https://h.users.no/api/gpslogger?latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT&speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT',
#     'user': '',
#     'passwd': 'h3ih3i',
#     'failurl': 'https://h.users.no/fail/url_to_hit_if_no_position_found'
# }

# List of dictionaries, each dict is a receiver

receivers = [
    {
        'name': 'phonetrack',
        'url': "https://users.no/index.php/apps/phonetrack/log/gpslogger/%PASSWORD/%USERNAME?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT",
        'username': '',  # Empty for hostname
        'password': '030b524dcb3143c49c5a5944dde1b989',
        'failurl': 'https://h.users.no/fail/url_to_hit_if_no_position_found'  # Will be posted to if location fails, just to get a heartbeat
    }
]
