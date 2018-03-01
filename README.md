# locationreporter
Find location from GPS or wifi triangulation, and post to web

## Plan

* Read config
* Attempt GPS (unless disabled)
* Attempt Wifi if GPS failed
* Post to each service configured. Buffer if post fails.


Scratch notes:

https://martin-thoma.com/configuration-files-in-python/
https://github.com/wadda/gps3/ http://www.catb.org/gpsd/gpsd_json.html