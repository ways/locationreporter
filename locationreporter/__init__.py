#!/usr/bin/env python

"""
Find location from GPS or wifi triangulation, and post to web
"""

import sys
from time import sleep
cfg = None


def read_config():
    global cfg
    print('Config read from config.py:')
    import config as cfg
    if cfg.verbose:
        print("Receivers:")
        for entry in cfg.receivers:
            print("* %s" % entry)


def report_fail(timeout=10):
    from requests import get
    if cfg.verbose:
        print("No location")
    response = get(fail_url)
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

    return acc, latlong


def get_wifi_location(device='', timeout=15):
    import wifindme
    acc, latlng = wifindme.locate(device=device, min_aps=2, service='m')

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (acc, latlng))
    return acc, latlng


def report_location(accuracy, latlong, timeout=15):
    from requests import get

    for service in cfg.receivers().items():
        if cfg.verbose:
            print("Reporting to %s" % service)

        for url, user, password, failurl in service:
            if cfg.verbose:
                print("url %s, user %s, failurl %s" % (url[:10], user, failurl))

        # # report to phonetrack
        # url = "%slat=%s&lon=%s&acc=%s&timestamp=%s&sat=%s&alt=%s" % (
        # phonetrackurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), str(accuracy), str(time.time()), sat, alt)
        #
        # if verbose: print(url)
        # response = get(url)
        # if verbose: print(response)
        #
        # # report to gpslogger
        # url = "%slatitude=%s&longitude=%s&device=%s&accuracy=%s&provider=gps" % (
        # gpsloggerurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), hostname, str(accuracy))
        # if apipassword:
        #     url = url + "&api_password=" + apipassword
        #
        # if verbose: print(url)
        # response = get(url)
        # if verbose: print(response)
        #
        # # Exit will be based on last response (gpslogger)
        # if 200 == response.status_code:
        #     return True
        # else:
        #         return False


def check_user():
    import os
    if os.geteuid() != 0:
        print("You usually need root privileges for wifi triangulation, please use 'sudo'.")


if __name__ == '__main__':
    from socket import gethostname
    hostname = gethostname()
    read_config()
    check_user()

    try:
        while True:
            accuracy = False

            if cfg.gps_available:
                accuracy, latlong = get_gps_location(cfg.timeout_location)

            if not accuracy:
                accuracy, latlong = get_wifi_location(cfg.wifi_device, cfg.timeout_location)

            if accuracy:
                report_location(accuracy, latlong, cfg.timeout_post)

            sleep(cfg.delay_seconds)

    except KeyboardInterrupt:
        print('\nTerminated by user\n')
