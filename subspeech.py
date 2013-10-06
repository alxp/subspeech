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
from tempfile import mkdtemp

global currenttime
global basename
global scriptpath
global temppath

# "line" is of the format '00:00:12,487 --> 00:00:14,762'
# Return the number of milliseconds that this time evaluates to.
def get_start_time(line):
    hp = re.compile('[0-9]+:')
    hm = hp.search(line)
    hh = int(hm.group().rstrip(':'))
    mp = re.compile(':[0-9][0-9]')
    minm = mp.search(line)
    mm = int(minm.group().lstrip(':'))
    sp = re.compile(':[0-9][0-9],')
    sm = sp.search(line)
    # The .srt format was developed in France, so commas are used
    # to denote decimal fractions.
    ss = int(sm.group().lstrip(':').rstrip(','))
    ss = hh * 3600 + mm * 60 + ss
    ms = ss * 1000
    msp = re.compile(',[0-9]* ')
    msm = msp.search(line)
    ms += int(msm.group().lstrip(',').rstrip(' '))
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
        return None # If the file isn't formatted well just bail.
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
    # We are generating files at 23.2kHz.
    ticks = timediff / 23.22
    
    filename = basename + '_' + str(seqnum) + '_silence.mp3'
    os.system('dd if=/dev/zero of=' + temppath + '/silence.raw bs=1k count='+str(int(round(ticks))) + '>/dev/null 2>/dev/null')
    os.system('ffmpeg -v 0 -y -f s16le -ac 1 -ar 22050 -i ' + temppath + '/silence.raw -f wav ' + temppath + '/silence.wav >/dev/null 2>/dev/null')

    os.system('lame --quiet -b 32 ' + temppath + "/silence.wav " + temppath + "/" + filename)
    
    return filename

def create_speech_file (snippettext, snippetnumber):
    speechaifffile = basename + '_' + str(snippetnumber) + '_text.aiff'
    speechtxtfile = basename + '_' + str(snippetnumber) + '_text.txt'
    speechfile = basename + '_' + str(snippetnumber) + '_text.mp3'
    txtout = open(temppath + "/" + speechtxtfile, 'w')
    txtout.write(snippettext)
    txtout.close()
    subprocess.call(["say", "-o", temppath + "/" + speechaifffile, '-f', temppath + "/" + speechtxtfile])
    
    subprocess.call(['lame', '--quiet', '-b', '32', temppath + "/" + speechaifffile, temppath + "/" + speechfile])
    
    os.remove(temppath + "/" + speechaifffile)
    os.remove(temppath + "/" + speechtxtfile)
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
        os.system('cat ' + temppath + "/" + silencefile + ' >> ' + os.getcwd() + "/" + basename + '.mp3')
        os.system('cat ' + temppath + "/" + speechfile + ' >> ' + os.getcwd() + "/" + basename + '.mp3')

        # Unfortunately, we need to get the length of the output file
        # every time to avoid audio drift.
        pipe = os.popen(scriptpath + '/mp3len "' + basename + '.mp3"')
        currenttime = int(pipe.readline())
        os.remove(temppath + "/" + silencefile)
        os.remove(temppath + "/" + speechfile)

    os.remove(temppath + '/silence.wav')
    os.remove(temppath + '/silence.raw')


os.environ['PATH'] += ':/usr/local/bin'
scriptpath = os.path.abspath( os.path.dirname( sys.argv[0]) )
temppath = mkdtemp()
basename = os.path.basename(os.path.splitext(sys.argv[1])[0])


parse_subtitles(sys.argv[1])
os.system("ls " + temppath)
os.rmdir(temppath)
    
