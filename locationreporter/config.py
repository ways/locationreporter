#!/usr/bin/env python

# URL formats

# gpslogger https://github.com/mendhak/gpslogger format
# https://example.com/api/gpslogger?latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT&speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT

# phonetrack
# https://example.com/index.php/apps/phonetrack/log/gpslogger/<api key>/<name>?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT

receivers = dict()
general = dict()

verbose = True
delay_seconds = 10
gps_available = False
timeout = 10

receivers['gpslogger'] = {
    'url': 'https://example.com/api/gpslogger?latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT&speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT',
    'user': 'user',
    'passwd': 'password',
    'failurl': 'https://example.com/fail/url_to_hit_if_no_position_found'
}
receivers['phonetrack'] = {
    'url': 'https://example.com/index.php/apps/phonetrack/log/gpslogger/<api key>/<name>?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT',
    'user': 'user',
    'passwd': 'password',
    'failurl': 'https://example.com/fail/url_to_hit_if_no_position_found'
}


