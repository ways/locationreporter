#!/usr/bin/env python

"""
Find location from GPS or wifi triangulation, and post to web
"""

import sys
import time
import signal

system_version = '0.1'
system_name = 'locationreporter.py'

cfg = None


def read_config():
    global cfg
    # print('Config read from config.py.')
    import config as cfg
    if cfg.verbose:
        print("Configured receivers:")
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


def get_gps_location():
    gpstries = 2
    acc = 999

    from gps3 import gps3
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()

    try:
        gpsd_socket.connect()
        gpsd_socket.watch()

        while True:
            gpserrorcount = 1
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
                            return None, (None, None), None, None, None, None
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

    except KeyboardInterrupt:
        gpsd_socket.close()

    return acc, latlong, timestamp, alt, vel, cog


def get_wifi_location(device=''):
    import wifindme
    acc, latlng = wifindme.locate(device=device, min_aps=2, service='m')
    timestamp = time.mktime(time.localtime())

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (acc, latlng))
    return acc, latlng, timestamp, None, None, None


def report_location(accuracy=None, latlong=(None, None), timestamp=None, alt=None, vel=None, cog=None, sat=None, bat=None):
    from requests import get
    import string

    for service in cfg.receivers:
        if cfg.verbose:
            print("Reporting to %s" % service['name'])

            url = ''

            # Merge data in URL
            if 'phonetrack' == service['name']:
                #  "https://users.no/index.php/apps/phonetrack/log/gpslogger/%PASSWORD/%USERNAME?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT",

                url = string.replace(service['url'], '%LAT', str(latlong[0]))
                url = string.replace(url, '%LON', str(latlong[1]))
                url = string.replace(url, '%ACC', str(accuracy))
                url = string.replace(url, '%TIMESTAMP', str(timestamp))
                url = string.replace(url, '%ACC', str(accuracy))
                url = string.replace(url, '%PASSWORD', service['password'])
                if 0 == len(service['username']):
                    url = string.replace(url, '%USERNAME', hostname)
                else:
                    url = string.replace(url, '%USERNAME', service['username'])
                if alt:
                    url = string.replace(url, '%ALT', alt)
                if bat:
                    url = string.replace(url, '%BAT', bat)
                if sat:
                    url = string.replace(url, '%SAT', sat)
            else:
                print("Unknown reporting service %s. Supported are: 'phonetrack'." % service['name'])
                sys.exit(1)

            if cfg.verbose:
                print(url)
            response = get(url, timeout=cfg.timeout_report)
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


class Timeout:
    """Timeout class using ALARM signal."""

    class Timeout(Exception):
        pass

    def __init__ (self, sec):
        self.sec = sec

    def __enter__ (self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__ (self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout (self, *args):
        raise Timeout.Timeout()


if __name__ == '__main__':
    timestamp = None
    alt = None
    vel = None
    cog = None
    accuracy = None
    latlong = (None, None)

    from socket import gethostname
    hostname = gethostname()

    print("%s v. %s on %s" % (system_name, system_version, hostname))
    read_config()
    check_user()

    if not cfg.use_wifi and not cfg.use_gps:
        print("GPS _and_ wifi is disabled in config...")
        sys.exit(1)

    # Get a quick wifi location first
    if cfg.use_wifi:
        try:
            with Timeout(cfg.timeout_location):
                accuracy, latlong, timestamp, alt, vel, cog = get_wifi_location(cfg.wifi_device)
        except Timeout.Timeout:
            print("Operation timed out due to user set limit.")
        except Exception, message:
            print('General error %s, ignoring.' % message)

    if accuracy:
        report_location(accuracy, latlong, timestamp, alt, vel, cog)

        while True:
            try:
                accuracy = False

                if cfg.use_gps:
                    try:
                        with Timeout(cfg.timeout_location):
                            accuracy, latlong, timestamp, alt, vel, cog = get_gps_location()
                    except Timeout.Timeout:
                        print("Operation timed out due to user set limit.")

                if not accuracy and cfg.use_wifi:
                    try:
                        with Timeout(cfg.timeout_location):
                            accuracy, latlong, timestamp, alt, vel, cog = get_wifi_location(cfg.wifi_device)
                    except Timeout.Timeout:
                        print("Operation timed out due to user set limit.")

                if accuracy:
                    report_location(accuracy, latlong, timestamp, alt, vel, cog)

                time.sleep(cfg.delay_seconds)

            except KeyboardInterrupt:
                print('\nTerminated by user\n')
                sys.exit(0)
            # except Exception, message:
            #     print('General error %s, ignoring.' % message)
