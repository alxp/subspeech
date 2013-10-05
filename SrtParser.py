#!/usr/bin/env python

import re, os, random, subprocess, struct, sys, wave
from datetime import datetime
from time import mktime

global currenttime
global basename

def current_unix_time():
    t=datetime.now()
    return int(mktime(t.timetuple())+1e-6*t.microsecond)


# "line" is of the format '00:00:12,487 --> 00:00:14,762'
# Return the number of milliseconds that this time evaluates to.
def get_start_time(line):
    p = re.compile('[0-9]*:')
    m = p.search(line)
    hh = int(m.group().rstrip(':'))
    p = re.compile(':[0-9][0-9]')
    m = p.search(line)
    mm = int(m.group().lstrip(':'))
    p = re.compile(':[0-9][0-9],')
    m = p.search(line)
    ss = int(m.group().lstrip(':').rstrip(','))
    ss = hh * 3600 + mm * 60 + ss
    p = re.compile(',[0-9]* ')
    m = p.search(line)
    ms = int(m.group().lstrip(',').rstrip(' '))
    ms += ss * 1000
    return ms

# Read text starting at the current position in file f.
# Return a tuple containing:
#   The line number, read from the file
#   The start time
#   The text following the time stamp
def get_snippet(f):
    snippetnumber = 0
    starttime = 0
    snippettext = ''
    l = f.readline()
    while l != 'BLAHOHFUCK':
        if l == '':
            return None
        line = l.split()
        if len(line) == 0:
            l = f.readline()
            continue
        if len(line) > 1 or line[0].isdigit() == False:
            l = f.readline()
            continue
        snippetnumber = int(line[0])
        break
    starttime = f.readline()
    starttime = get_start_time(starttime)
    if type( starttime ) != int:
        return None #screw it, if the file isn't formatted well just bail.
    l = f.readline()
    while len(l.split()) != 0:
        line = l.split()
        if len(line) == 0:
            break
        snippettext = snippettext + ' ' + l
        l = f.readline()
    return [snippetnumber, starttime, snippettext]


# returns the filename of a newly-created mp3 file containing silence
def generate_silence(timediff, seqnum):
    ticks = timediff / 23.22
    
    filename = basename + '_' + str(seqnum) + '_silence.mp3'
    os.system('dd if=/dev/zero of=silence.raw bs=1k count='+str(int(round(ticks))) + '>/dev/null 2>/dev/null')
    os.system('ffmpeg -v 0 -y -f s16le -ac 1 -ar 22050 -i silence.raw -f wav silence.wav >/dev/null 2>/dev/null')

    os.system('lame --quiet -b 32 silence.wav ' + filename)
    
    return filename


os.environ['PATH'] += ':/usr/local/bin'
scriptpath = os.path.abspath( os.path.dirname( sys.argv[0]) )
currenttime = 0
basename = os.path.basename(os.path.splitext(sys.argv[1])[0])
f = open(sys.argv[1], 'r')
done = False
while done == False:
    snippet = get_snippet(f)
    if snippet == None:
        done = True
        break
    snippetnumber = snippet[0]
    starttime = snippet[1]
    snippettext = snippet[2]
    gap = starttime - currenttime
    generate_silence(gap, snippetnumber)
    currenttime = starttime
    speechaifffile = basename + '_' + str(snippetnumber) + '_text.aiff'
    speechtxtfile = basename + '_' + str(snippetnumber) + '_text.txt'
    speechfile = basename + '_' + str(snippetnumber) + '_text.mp3'
    silencefile = basename + '_' + str(snippetnumber) + '_silence.mp3'
    print snippettext
    txtout = open(speechtxtfile, 'w')
    txtout.write(snippettext)
    txtout.close()
    subprocess.call(["say", "-o", speechaifffile, '-f', speechtxtfile])
    
    subprocess.call(['lame', '--quiet', '-b', '32', speechaifffile, speechfile])
    pipe = os.popen(scriptpath + '/mp3len "' + speechfile + '"')
    speechlen = int(pipe.readline())
    pipe.close()
    os.system('cat ' + silencefile + ' >> ' + basename + '.mp3')
    os.system('cat ' + speechfile + ' >> ' + basename + '.mp3')

    # Unfortunately, we need to get the length of the output file
    # every time to avoid audio drift.
    pipe = os.popen(scriptpath + '/mp3len "' + basename + '.mp3"')
    currenttime = int(pipe.readline())
    os.remove(silencefile)
    os.remove(speechaifffile)
    os.remove(speechtxtfile)
    os.remove(speechfile)
os.remove('silence.wav')
os.remove('silence.raw')
    
    
