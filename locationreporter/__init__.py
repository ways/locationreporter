#!/usr/bin/env python3

"""
Find location from GPS or wifi triangulation, and post to web
"""

import sys, time
from threading import Thread, Event # https://dreamix.eu/blog/webothers/timeout-function-in-python-3
from socket import gethostname
hostname=gethostname()
verbose=True
single=False
fail_url='https://graph.no/' + hostname + '_failed/'

gpsloggerurl="https://h.users.no/api/gpslogger?"
#latitude=%LAT&longitude=%LON&device=%SER&accuracy=%ACC&battery=%BATT&speed=%SPD&direction=%DIR&altitude=%ALT&provider=%PROV&activity=%ACT

phonetrackurl="https://users.no/index.php/apps/phonetrack/log/gpslogger/31434b2f4f6c3e826310e2e87ae53812/" + hostname + "?"
#phonetrackurl="https://users.no/index.php/apps/phonetrack/log/gpslogger/31434b2f4f6c3e826310e2e87ae53812/tracker01?lat=%LAT&lon=%LON&sat=%SAT&alt=%ALT&acc=%ACC&timestamp=%TIMESTAMP&bat=%BATT"

def report_fail ():
    from requests import get
    if verbose: print("No location")
    response = get(fail_url)
    if verbose: print(response)
    sys.exit(1)


if __name__ == '__main__':
    gpserrorcount=0
    
    from gps3 import gps3 # https://github.com/wadda/gps3/ http://www.catb.org/gpsd/gpsd_json.html
    gpsd_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()
    
    try:
        gpsd_socket.connect()
        gpsd_socket.watch()
        
        while True:
        
            for new_data in gpsd_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    if verbose:
                        print('Reading gps data (%s/20)' % gpserrorcount)
                    if 'n/a' == data_stream.TPV['lat']:
                        gpserrorcount+=1
                        if 20<gpserrorcount: # Die if no GPS
                            if verbose: print('No valid gps data!')
                            report_fail()
                            sys.exit(2)
                    else:
                        break
            
            timestamp = time.mktime(time.strptime(data_stream.TPV['time'], '%Y-%m-%dT%H:%M:%S.000Z'))
            accuracy = 999
            if 'n/a' != data_stream.TPV['epx']:
                accuracy = str((int(data_stream.TPV['epx'] + data_stream.TPV['epy']))/2)
            
            alt = data_stream.TPV['alt']
            cog = data_stream.TPV['track']
            vel = data_stream.TPV['speed']
            sat = data_stream.TPV['satellites']
            
            if verbose: print(accuracy, data_stream.TPV['lat'], data_stream.TPV['lon'])  # e.g. 25, (50.1234567, -1.234567)
            
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
            
            from requests import get
            #report to phonetrack
            url="%slat=%s&lon=%s&acc=%s&timestamp=%s&sat=%s&alt=%s" % (phonetrackurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), str(accuracy), str(time.time()), sat, alt)
            
            if verbose: print(url)
            response = get(url)
            if verbose: print(response)
            
            #report to gpslogger
            url="%slatitude=%s&longitude=%s&device=%s&accuracy=%s&provider=gps" % (gpsloggerurl, str(data_stream.TPV['lat']), str(data_stream.TPV['lon']), hostname, str(accuracy))
            if apipassword:
                url=url + "&api_password=" + apipassword
            
            if verbose: print(url)
            response = get(url)
            if verbose: print(response)
            
            # Exit will be based on last response (gpslogger)
            if 200 == response.status_code:
                if single: sys.exit(0)
            else:
                sys.exit(1)
        
    except KeyboardInterrupt:
        gpsd_socket.close()
        print('\nTerminated by user\n')
