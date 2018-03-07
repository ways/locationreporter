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
            print("* %s" % entry['name'])


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
    sat = None

    from gps3 import gps3
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()

    try:
        gpsd_socket.connect()
        gpsd_socket.watch()

        gpsd_tries = 1
        for new_data in gpsd_socket:
            if new_data:
                data_stream.unpack(new_data)
                print('Reading gps data (%s/%s), epx %s' % (gpsd_tries, gpsd_tries_max, data_stream.TPV['epx']))

                if 'n/a' == data_stream.TPV['lat']:  # No data
                    gpsd_tries += 1
                    if gpsd_tries_max <= gpsd_tries:
                        if cfg.verbose:
                            print('No valid gps data!')
                        return acc, latlong, tst, alt, vel, cog
                else:
                    tst = time.mktime(time.strptime(data_stream.TPV['time'], '%Y-%m-%dT%H:%M:%S.000Z'))
                    if 'n/a' != data_stream.TPV['epx']:
                        acc = (int(data_stream.TPV['epx'] + data_stream.TPV['epy'])) / 2

                    alt = round(data_stream.TPV['alt'], 0)
                    cog = round(data_stream.TPV['track'], 0)
                    vel = round(data_stream.TPV['speed'], 0)
                    sat = data_stream.SKY['satellites']

                    if cfg.verbose:
                        print(acc, data_stream.TPV['lat'], data_stream.TPV['lon'])  # ie. 25, (50.1234567,-1.234567)
                    break

    except socketerror, err:
        print("Error: Unable to connect to gpsd. Is it installed and enabled? (%s)" % err)
    except KeyboardInterrupt:
        gpsd_socket.close()

    return acc, latlong, tst, alt, vel, cog, sat


def get_wifi_location(device=''):
    import wifindme
    acc, latlng = wifindme.locate(device=device, min_aps=2, service='m')
    tst = time.mktime(time.localtime())

    if cfg.verbose:
        print('Wifi location: %s, %s.' % (acc, latlng))
    return acc, latlng, tst, None, None, None


def report_location(acc=None, pos=(None, None), tst=None, alt=None, vel=None, cog=None, sat=None, bat=None, prov=None):
    from requests import get
    import string

    for service in cfg.receivers:
        url = ''

        if cfg.verbose:
            print("-> Reporting to %s: " % service['name'])

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
                url = string.replace(url, '%ALT', str(alt))
            if bat:
                url = string.replace(url, '%BAT', str(bat))
            if sat:
                url = string.replace(url, '%SAT', str(sat))

        elif 'gpslogger' == service['name']:
            # https://h.users.no/api/gpslogger?latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT
            #   &speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT
            # Never setting activity
            url = string.replace(service['url'], '%LAT', str(pos[0]))
            url = string.replace(url, '%LON', str(pos[1]))
            url = string.replace(url, '%ACC', str(acc))
            url = string.replace(url, '%PROV', prov)
            if 0 == len(service['username']):
                url = string.replace(url, '%SER', hostname)
            else:
                url = string.replace(url, '%USERNAME', service['username'])
            if alt:
                url = string.replace(url, '%ALT', str(alt))
            else:
                url = string.replace(url, '&altitude=%ALT', '')
            if bat:
                url = string.replace(url, '%BAT', str(bat))
            else:
                url = string.replace(url, '&battery=%BATT', '')
            if sat:
                url = string.replace(url, '%SAT', str(sat))
            if vel:
                url = string.replace(url, '%SPD', str(vel))
            else:
                url = string.replace(url, '&speed=%SPD', '')
            if cog:
                url = string.replace(url, '%DIR', str(cog))
            else:
                url = string.replace(url, '&direction=%DIR', '')
            if 0 < len(service['password']):
                url = url + "&api_password=" + service['password']

        else:
            print("Unknown reporting service %s. Supported are: phonetrack and gpslogger." % service['name'])
            sys.exit(1)

        if cfg.verbose:
            print(" %s" % url)
        response = get(url, timeout=cfg.timeout_report)
        if cfg.verbose:
            print(" %s" % response)


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
    satelittes = None
    provider = 'wifi'

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
        report_location(acc=accuracy, pos=latlong, tst=timestamp, alt=altitude, vel=velocity, cog=course, prov=provider)

    while True:
        try:
            accuracy = False

            if cfg.use_gps:
                try:
                    with Timeout(cfg.timeout_location):
                        accuracy, latlong, timestamp, altitude, velocity, course, satelittes = get_gps_location()
                        provider = 'gps'
                except Timeout.Timeout:
                    print("Operation get_gps_location timed out due to user set limit (%s seconds)." % cfg.timeout_location)

            if not accuracy and cfg.use_wifi:
                try:
                    with Timeout(cfg.timeout_location):
                        accuracy, latlong, timestamp, altitude, velocity, course = get_wifi_location(cfg.wifi_device)
                        provider = 'wifi'
                except Timeout.Timeout:
                    print("Operation get_wifi_location timed out due to user set limit (%s seconds)." % cfg.timeout_location)

            if accuracy:
                report_location(acc=accuracy, pos=latlong, tst=timestamp, alt=altitude, vel=velocity, cog=course, prov=provider, sat=satelittes)

            if cfg.verbose:
                print("Next run in %s seconds..." % cfg.delay_seconds)
            time.sleep(cfg.delay_seconds)

        except KeyboardInterrupt:
            print('\nTerminated by user\n')
            sys.exit(0)
#        except Exception, message:  # Keep going, no matter what
#            print('General error %s, ignoring.' % message)
