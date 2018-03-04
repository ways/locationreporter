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

Scratch notes:

https://martin-thoma.com/configuration-files-in-python/
https://github.com/wadda/gps3/ http://www.catb.org/gpsd/gpsd_json.html
https://pythonadventures.wordpress.com/2012/12/08/raise-a-timeout-exception-after-x-seconds/
