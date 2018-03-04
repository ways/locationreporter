#!/usr/bin/env python

"""
Find location from GPS or wifi triangulation, and post to web
"""

import sys
import time
cfg = None


def read_config():
    global cfg
    print('Config read from config.py:')
    import config as cfg
    if cfg.verbose:
        print("Receivers:")
        for entry in cfg.receivers:
            print("* %s" % entry)


def report_fail(url, timeout=10):
    from requests import get
    if cfg.verbose:
        print("No location")
    response = get(url)
    if cfg.verbose:
        print(response)
    sys.exit(1)


def get_gps_location(timeout=10):
    gpstries = 2
    acc = 999

    from gps3 import gps3
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()

    try:
        gpsd_socket.connect()
        gpsd_socket.watch()

        while True:
            gpserrorcount = 0
            for new_data in gpsd_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    if cfg.verbose:
                        print('Reading gps data (%s/%s)' % (gpserrorcount, gpstries))
                    if 'n/a' == data_stream.TPV['lat']:
                        gpserrorcount += 1
                        if gpstries < gpserrorcount:  # Die if no GPS
                            if cfg.verbose:
                                print('No valid gps data!')
                            return False, (False, False)
                    else:
                        break

            timestamp = time.mktime(time.strptime(data_stream.TPV['time'], '%Y-%m-%dT%H:%M:%S.000Z'))
            if 'n/a' != data_stream.TPV['epx']:
                acc = str((int(data_stream.TPV['epx'] + data_stream.TPV['epy'])) / 2)

            alt = data_stream.TPV['alt']
            cog = data_stream.TPV['track']
            vel = data_stream.TPV['speed']
            sat = data_stream.TPV['satellites']

            if cfg.verbose:
                print(acc, data_stream.TPV['lat'], data_stream.TPV['lon'])  # e.g. 25, (50.1234567, -1.234567)

            #  '{"_type":"location"'
            #   + ',"tid":"' + id
            #   + '","acc":' + str(accuracy)
            #   + ',"lat":' + str(data_stream.TPV['lat'])
            #   + ',"lon":' + str(data_stream.TPV['lon'])
            #   + ',"tst":' + str(timestamp)
            #   + ',"conn":"m"'
            #   + ',"vel": ' + str(vel)
            #   + ',"cog": ' + str(cog)
            #   + altformated

            if not acc:
                report_fail()
                sys.exit(1)
    except KeyboardInterrupt:
        gpsd_socket.close()

    return acc, latlong, timestamp, alt, vel, cog


def get_wifi_location(device='', timeout=15):
    import wifindme
    acc, latlng = wifindme.locate(device=device, min_aps=2, service='m')
    timestamp = time.mktime(time.localtime())

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (acc, latlng))
    return acc, latlng, timestamp, None, None, None


def report_location(timeout=15, accuracy=None, latlong=(None, None), timestamp=None, alt=None, vel=None, cog=None, sat=None, bat=None):
    from requests import get
    import string

    for service in cfg.receivers:
        if cfg.verbose:
            print("Reporting to %s" % service['name'])
            print("url %s..., user %s" % (service['url'][:20], service['username']))

            # Merge data in URL
            # Phonetrack:
            # "https://users.no/index.php/apps/phonetrack/log/gpslogger/%PASSWORD/%USERNAME?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT",

            url = string.replace(service['url'], '%LAT', str(latlong[0]))
            url = string.replace(url, '%LON', str(latlong[1]))
            url = string.replace(url, '%ACC', str(accuracy))
            url = string.replace(url, '%TIMESTAMP', str(timestamp))
            url = string.replace(url, '%ACC', str(accuracy))
            url = string.replace(url, '%PASSWORD', service['password'])
            url = string.replace(url, '%USERNAME', service['username'])
            if alt:
                url = string.replace(url, '%ALT', alt)
            if bat:
                url = string.replace(url, '%BAT', bat)
            if sat:
                url = string.replace(url, '%SAT', sat)

            if cfg.verbose:
                print(url)
            response = get(url)
            if cfg.verbose:
                print(response)

            # Exit based on response
            if 200 == response.status_code:
                return True
            else:
                return False


def check_user():
    import os
    if os.geteuid() != 0:
        print("You usually need root privileges for wifi triangulation, please use 'sudo'.")


if __name__ == '__main__':
    timestamp = None
    alt = None
    vel = None
    cog = None

    from socket import gethostname
    hostname = gethostname()
    read_config()
    check_user()

    if not cfg.use_wifi and not cfg.use_gps:
        print("GPS _and_ wifi is disabled in config...")
        sys.exit(1)

    try:
        # Get a quick wifi location first
        if cfg.use_wifi:
            accuracy, latlong, timestamp, alt, vel, cog = get_wifi_location(cfg.wifi_device, cfg.timeout_location)
        if accuracy:
            report_location(cfg.timeout_post, accuracy, latlong, timestamp, alt, vel, cog)

        while True:
            accuracy = False

            if cfg.use_gps:
                accuracy, latlong, timestamp, alt, vel, cog = get_gps_location(cfg.timeout_location)

            if not accuracy and cfg.use_wifi:
                accuracy, latlong, timestamp, alt, vel, cog = get_wifi_location(cfg.wifi_device, cfg.timeout_location)

            if accuracy:
                report_location(cfg.timeout_post, accuracy, latlong, timestamp, alt, vel, cog)

            time.sleep(cfg.delay_seconds)

    except KeyboardInterrupt:
        print('\nTerminated by user\n')
