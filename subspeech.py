#!/usr/bin/env python

# Copyright 2010-2013 by Alexander O'Neill

# Project home page: http://github.com/alxp/subspeech.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re, os, random, subprocess, struct, sys, wave
from datetime import datetime
from time import mktime

global currenttime
global basename
global scriptpath

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
    # The .srt format was developed in France, so commas are used
    # to denote decimal fractions.
    ss = int(m.group().lstrip(':').rstrip(','))
    ss = hh * 3600 + mm * 60 + ss
    ms = ss * 1000
    p = re.compile(',[0-9]* ')
    m = p.search(line)
    ms += int(m.group().lstrip(',').rstrip(' '))
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

    # Eat blank or invalid lines until a line number is found.
    while True:
        l = f.readline()
        if l == '':
            return None
        line = l.split()
        # We are expecting a line number, ignore anything that isn't a number.
        if len(line) == 0 or len(line) > 1 or line[0].isdigit() == False:
            continue
        snippetnumber = int(line[0])
        break

    starttime = get_start_time(f.readline())
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


# Returns the filename of a newly-created MP3 file containing silence
def generate_silence(timediff, seqnum):
    ticks = timediff / 23.22
    
    filename = basename + '_' + str(seqnum) + '_silence.mp3'
    os.system('dd if=/dev/zero of=silence.raw bs=1k count='+str(int(round(ticks))) + '>/dev/null 2>/dev/null')
    os.system('ffmpeg -v 0 -y -f s16le -ac 1 -ar 22050 -i silence.raw -f wav silence.wav >/dev/null 2>/dev/null')

    os.system('lame --quiet -b 32 silence.wav ' + filename)
    
    return filename

def create_speech_file (snippettext, snippetnumber):
    speechaifffile = basename + '_' + str(snippetnumber) + '_text.aiff'
    speechtxtfile = basename + '_' + str(snippetnumber) + '_text.txt'
    speechfile = basename + '_' + str(snippetnumber) + '_text.mp3'
    txtout = open(speechtxtfile, 'w')
    txtout.write(snippettext)
    txtout.close()
    subprocess.call(["say", "-o", speechaifffile, '-f', speechtxtfile])
    
    subprocess.call(['lame', '--quiet', '-b', '32', speechaifffile, speechfile])
    
    os.remove(speechaifffile)
    os.remove(speechtxtfile)
    return speechfile

def parse_subtitles(srtfile):
    f = open(srtfile)
    currenttime = 0
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
        silencefile = generate_silence(gap, snippetnumber)
        currenttime = starttime

        print snippettext
    
        speechfile = create_speech_file(snippettext, snippetnumber)

        os.system('cat ' + silencefile + ' >> ' + basename + '.mp3')
        os.system('cat ' + speechfile + ' >> ' + basename + '.mp3')

        # Unfortunately, we need to get the length of the output file
        # every time to avoid audio drift.
        pipe = os.popen(scriptpath + '/mp3len "' + basename + '.mp3"')
        currenttime = int(pipe.readline())
        os.remove(silencefile)
        os.remove(speechfile)

    os.remove('silence.wav')
    os.remove('silence.raw')


os.environ['PATH'] += ':/usr/local/bin'
scriptpath = os.path.abspath( os.path.dirname( sys.argv[0]) )
basename = os.path.basename(os.path.splitext(sys.argv[1])[0])

parse_subtitles(sys.argv[1])
    
    
