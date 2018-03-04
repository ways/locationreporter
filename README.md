# locationreporter
Find location from GPS or wifi triangulation, and post to web

## Plan

* Read config.
* Attempt Wifi first, because it's fast.
* Attempt GPS (unless disabled).
* Attempt Wifi, if GPS failed.
* Post to each service configured. Buffer if post fails?
* Return to step 3.


## TODO

* Timeout on all operations
* Allow multiple report receivers

Scratch notes:

https://martin-thoma.com/configuration-files-in-python/
https://github.com/wadda/gps3/ http://www.catb.org/gpsd/gpsd_json.html