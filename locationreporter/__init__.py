#!/usr/bin/env python

"""
Find location from GPS or wifi triangulation, and post to web
"""

import sys
from time import sleep

import config as cfg


def read_config():
    print('Config read from config.py:')
    print(cfg)
    print()


def report_fail():
    from requests import get
    if cfg.verbose:
        print("No location")
    response = get(fail_url)
    if cfg.verbose:
        print(response)
    sys.exit(1)


def get_gps_location():
    gpserrorcount = 0

    from gps3 import gps3
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()

    try:
        gpsd_socket.connect()
        gpsd_socket.watch()

        while True:

            for new_data in gpsd_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    if cfg.verbose:
                        print('Reading gps data (%s/20)' % gpserrorcount)
                    if 'n/a' == data_stream.TPV['lat']:
                        gpserrorcount += 1
                        if 20 < gpserrorcount:  # Die if no GPS
                            if verbose: print('No valid gps data!')
                            report_fail()
                            sys.exit(2)
                    else:
                        break

            timestamp = time.mktime(time.strptime(data_stream.TPV['time'], '%Y-%m-%dT%H:%M:%S.000Z'))
            accuracy = 999
            if 'n/a' != data_stream.TPV['epx']:
                accuracy = str((int(data_stream.TPV['epx'] + data_stream.TPV['epy'])) / 2)

            alt = data_stream.TPV['alt']
            cog = data_stream.TPV['track']
            vel = data_stream.TPV['speed']
            sat = data_stream.TPV['satellites']

            if verbose: print(
            accuracy, data_stream.TPV['lat'], data_stream.TPV['lon'])  # e.g. 25, (50.1234567, -1.234567)

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

            if not accuracy:
                report_fail()
                sys.exit(1)
    except KeyboardInterrupt:
        gpsd_socket.close()


def get_wifi_location(device="wlan0"):
    import wifindme
    accuracy, latlng = wifindme.locate(device=device, min_aps=2, service='m')

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (accuracy, latlng))
    return accuracy, latlng


def report_location(accuracy, latlong):
    from requests import get

    for name, url, password in cfg.receivers:
        # report to phonetrack
        url = "%slat=%s&lon=%s&acc=%s&timestamp=%s&sat=%s&alt=%s" % (
        phonetrackurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), str(accuracy), str(time.time()), sat, alt)

        if verbose: print(url)
        response = get(url)
        if verbose: print(response)

        # report to gpslogger
        url = "%slatitude=%s&longitude=%s&device=%s&accuracy=%s&provider=gps" % (
        gpsloggerurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), hostname, str(accuracy))
        if apipassword:
            url = url + "&api_password=" + apipassword

        if verbose: print(url)
        response = get(url)
        if verbose: print(response)

        # Exit will be based on last response (gpslogger)
        if 200 == response.status_code:
            return True
        else:
            return False


if __name__ == '__main__':
    read_config()

    from socket import gethostname
    hostname = gethostname()

    try:
        while True:
            if cfg.gps_available:
                accuracy, latlong = get_gps_location()
            accuracy, latlong = get_wifi_location()
            report_location(accuracy, latlong)

            sleep(cfg.delay_seconds)

    except KeyboardInterrupt:
        print('\nTerminated by user\n')
