# locationreporter
Find location from GPS or wifi triangulation, and post to web. Originally made to run on Raspberry Pi for car locaiton reporting.

# Hardware

* Any RPi
* Network, i.e. via a GPRS dongle
* Preferably wifi
* Preferably a USB GPS dongle

# Software dependencies

* gpsd set up and working. Option "-n" recommended.
* The rest should be covered by requirements.txt

# Servers

Supports logging to the following via GET:
* gpslogger https://home-assistant.io/components/device_tracker.gpslogger/
* PhoneTrack https://gitlab.com/eneiluj/phonetrack-oc/wikis/home

## Code structure

* Read config.
* Attempt Wifi first, because it's fast.
* Loop:
  * Attempt GPS.
  * Attempt Wifi, if GPS failed.
  * Post to each service configured.
  * Wait configured time

## TODO

* &speed= coming soon to phonetrac
* Add timing info to see what takes long time
* Deploy to PIP
* Buffer failed reports?
* Read battery?
  $ cat /sys/class/power_supply/BAT0/uevent
  POWER_SUPPLY_NAME=BAT0
  POWER_SUPPLY_STATUS=Unknown
  POWER_SUPPLY_PRESENT=1
  POWER_SUPPLY_TECHNOLOGY=Li-poly
  POWER_SUPPLY_CYCLE_COUNT=0
  POWER_SUPPLY_VOLTAGE_MIN_DESIGN=15200000
  POWER_SUPPLY_VOLTAGE_NOW=16270000
  POWER_SUPPLY_POWER_NOW=0
  POWER_SUPPLY_ENERGY_FULL_DESIGN=50080000
  POWER_SUPPLY_ENERGY_FULL=44760000
  POWER_SUPPLY_ENERGY_NOW=35900000
  POWER_SUPPLY_CAPACITY=80
  POWER_SUPPLY_CAPACITY_LEVEL=Normal
  POWER_SUPPLY_MODEL_NAME=00HW003
  POWER_SUPPLY_MANUFACTURER=SMP
  POWER_SUPPLY_SERIAL_NUMBER=   81


## Example run

```bash
$ sudo ./locationreporter/__init__.py                                               
locationreporter.py v. 0.1 on laptop
Configured receivers:
* {'url': 'https://example.com/index.php/apps/phonetrack/log/gpslogger/%PASSWORD/%USERNAME?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT', 'username': '', 'failurl': 'https://h.users.no/fail/url_to_hit_if_no_position_found', 'password': '030b524dcb3143c49c5a5944dde1b989', 'name': 'phonetrack'}
Wifi location: 12.3451886, (12.3458822, 12.3453381).
Reporting to phonetrack
https://example.com/index.php/apps/phonetrack/log/gpslogger/12345cb3143c49c5a5944dde1b989/laptop?lat=12.3458822&lon=12.3453381&sat=%SAT&alt=%ALT&acc=12.3451886&timestamp=1520197960.0&bat=%BATT
<Response [200]>
Reading gps data (1/2)
Reading gps data (2/2)
No valid gps data!
Wifi location: 12.3451886, (12.3458822, 12.3453381).
Reporting to phonetrack
https://users.no/index.php/apps/phonetrack/log/gpslogger/12345cb3143c49c5a5944dde1b989/laptop?lat=12.3458855&lon=12.3453253&sat=%SAT&alt=%ALT&acc=12.3451834&timestamp=1520197962.0&bat=%BATT
<Response [200]>
...
```

Scratch notes:

* https://martin-thoma.com/configuration-files-in-python/
* https://github.com/wadda/gps3/
* http://www.catb.org/gpsd/gpsd_json.html
* https://pythonadventures.wordpress.com/2012/12/08/raise-a-timeout-exception-after-x-seconds/
