# locationreporter
Find location from GPS or wifi triangulation, and post to web. Originally made to run on Raspberry Pi for car locaiton reporting.

# Hardware

* Any RPi
* Network, i.e. via a GPRS dongle
* Preferably wifi
* Preferably a USB GPS dongle


## Code structure

* Read config.
* Attempt Wifi first, because it's fast.
* Attempt GPS (unless disabled).
* Attempt Wifi, if GPS failed.
* Post to each service configured. Buffer if post fails?
* Return to step 3.


## TODO

* Allow multiple report receivers
* Streamline
* Deploy to PIP


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

https://martin-thoma.com/configuration-files-in-python/
https://github.com/wadda/gps3/ http://www.catb.org/gpsd/gpsd_json.html
https://pythonadventures.wordpress.com/2012/12/08/raise-a-timeout-exception-after-x-seconds/
