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


# TODO:
def report_fail(url, timeout=10):
    from requests import get
    if cfg.verbose:
        print("No location")
    response = get(url)
    if cfg.verbose:
        print(response)
    sys.exit(1)


def get_gps_location():
    from socket import error as socketerror

    gpsd_tries_max = 10
    acc = None
    tst = None
    alt = None
    cog = None
    vel = None

    from gps3 import gps3
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()

    try:
        gpsd_socket.connect()
        gpsd_socket.watch()

        while True:
            gpsd_tries = 1
            for new_data in gpsd_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    if cfg.verbose:
                        print("Connected to gpsd version %s.%s" % (data_stream.VERSION['proto_major'], data_stream.VERSION['proto_minor']))
                        print('Reading gps data (%s/%s), epx %s' % (gpsd_tries, gpsd_tries_max, data_stream.TPV['epx']))
                    if 'n/a' == data_stream.DEVICE['path']:
                        print("No GPS connected")
                        return acc, latlong, tst, alt, vel, cog

                    if 'n/a' == data_stream.TPV['lat']:  # No data
                        gpsd_tries += 1
                        if gpsd_tries_max <= gpsd_tries:
                            if cfg.verbose:
                                print('No valid gps data!')
                            return acc, latlong, tst, alt, vel, cog
                    else:
                        tst = time.mktime(time.strptime(data_stream.TPV['time'], '%Y-%m-%dT%H:%M:%S.000Z'))
                        if 'n/a' != data_stream.TPV['epx']:
                            acc = str((int(data_stream.TPV['epx'] + data_stream.TPV['epy'])) / 2)

                        alt = data_stream.TPV['alt']
                        cog = data_stream.TPV['track']
                        vel = data_stream.TPV['speed']
                        #  sat = data_stream.TPV['satellites']

                        if cfg.verbose:
                            print(
                            acc, data_stream.TPV['lat'], data_stream.TPV['lon'])  # e.g. 25, (50.1234567, -1.234567)
                        break
                time.sleep(1)

    except socketerror, err:
        print("Error: Unable to connect to gpsd. Is it installed and enabled? (%s)" % err)
    except KeyboardInterrupt:
        gpsd_socket.close()

    return acc, latlong, tst, alt, vel, cog


def get_wifi_location(device=''):
    import wifindme
    acc, latlng = wifindme.locate(device=device, min_aps=2, service='m')
    tst = time.mktime(time.localtime())

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (acc, latlng))
    return acc, latlng, tst, None, None, None


def report_location(acc=None, pos=(None, None), tst=None, alt=None, vel=None, cog=None, sat=None, bat=None):
    from requests import get
    import string

    for service in cfg.receivers:
        if cfg.verbose:
            print("Reporting to %s" % service['name'])

            url = ''

            # Merge data in URL
            if 'phonetrack' == service['name']:
                #  "https://users.no/index.php/apps/phonetrack/log/gpslogger/%PASSWORD/%USERNAME?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT",

                url = string.replace(service['url'], '%LAT', str(pos[0]))
                url = string.replace(url, '%LON', str(pos[1]))
                url = string.replace(url, '%ACC', str(acc))
                url = string.replace(url, '%TIMESTAMP', str(tst))
                url = string.replace(url, '%ACC', str(acc))
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

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)  # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


if __name__ == '__main__':
    timestamp = None
    altitude = None
    velocity = None
    course = None
    accuracy = None
    latlong = (None, None)

    from socket import gethostname
    hostname = gethostname()

    print("%s v. %s on %s" % (system_name, system_version, hostname))
    read_config()

    if not cfg.use_wifi and not cfg.use_gps:
        print("GPS _and_ wifi is disabled in config...")
        sys.exit(1)
    elif cfg.use_wifi:
        check_user()

    # Get a quick wifi location first
    if cfg.use_wifi:
        try:
            with Timeout(cfg.timeout_location):
                accuracy, latlong, timestamp, altitude, velocity, course = get_wifi_location(cfg.wifi_device)
        except Timeout.Timeout:
            print("Operation timed out due to user set limit.")
        except Exception, message:
            print('General error %s, ignoring.' % message)

    if accuracy:
        report_location(accuracy, latlong, timestamp, altitude, velocity, course)

    while True:
        try:
            accuracy = False

            if cfg.use_gps:
                try:
                    with Timeout(cfg.timeout_location):
                        accuracy, latlong, timestamp, altitude, velocity, course = get_gps_location()
                except Timeout.Timeout:
                    print("Operation get_gps_location timed out due to user set limit (%s seconds)." % cfg.timeout_location)

            if not accuracy and cfg.use_wifi:
                try:
                    with Timeout(cfg.timeout_location):
                        accuracy, latlong, timestamp, altitude, velocity, course = get_wifi_location(cfg.wifi_device)
                except Timeout.Timeout:
                    print("Operation get_wifi_location timed out due to user set limit (%s seconds)." % cfg.timeout_location)

            if accuracy:
                report_location(accuracy, latlong, timestamp, altitude, velocity, course)

            if cfg.verbose:
                print("Next run in %s seconds..." % cfg.delay_seconds)
            time.sleep(cfg.delay_seconds)

        except KeyboardInterrupt:
            print('\nTerminated by user\n')
            sys.exit(0)
#        except Exception, message:  # Keep going, no matter what
#            print('General error %s, ignoring.' % message)
