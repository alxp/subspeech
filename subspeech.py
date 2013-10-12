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
from optparse import OptionParser
from HTMLParser import HTMLParser

global currenttime
global basename
global scriptpath
global temppath

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, data):
        self.fed.append(data)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def get_yes_or_no(message):
    sys.stdout.write(message + ' (y/n) [default: n] ' )
    answers = {'y': True, 'yes':True, 'n':False, 'no': False}
    while True:
        user_input = raw_input().lower()
        if user_input in ['y', 'yes', 'n', 'no']:
            return answers[user_input]
        elif user_input in ['']:
            # Default to true.
            return False
        else:
            print 'Please enter y for yes or n for no.'


def check_output_file(basename, force_overwrite, quiet):
    mp3file = basename + '.mp3'
    if os.path.isfile(mp3file):
        if (force_overwrite == False):
            
            if (quiet == False):
                user_overwrite = get_yes_or_no('File ' + mp3file + ' exists. Overwite it?')
            else:
                user_overwrite = False
            if (user_overwrite == False):
                print 'Aborting.'
                exit(1)
        
        os.remove(mp3file)


def get_start_time(line):
    """'line' is of the format '00:00:12,487 --> 00:00:14,762'
    Return the number of milliseconds that the start time evaluates to."""
    starttimestamp = re.findall(r'([0-9]+):([0-9]+):([0-9]+),([0-9]+)', line)[0]    
    seconds = int(starttimestamp[0]) * 3600 + int(starttimestamp[1]) * 60 + int(starttimestamp[2])
    ms = seconds * 1000 + int(starttimestamp[3])
    return ms


def get_snippet(f):
    """ Read text starting at the current position in file f.
    Return a tuple containing:
    The line number, read from the file
    The start time
    The text following the time stamp"""
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
    return [snippetnumber, starttime, strip_tags(snippettext)]


def generate_silence(timediff, seqnum):
    """ Returns the filename of a newly-created MP3 file containing silence"""
    # We are generating files at 23.2kHz.
    ticks = timediff / 23.22
    
    filename = basename + '_' + str(seqnum) + '_silence.mp3'
    os.system('dd if=/dev/zero of=' + temppath + '/silence.raw bs=1k count='+str(int(round(ticks))) + '>/dev/null 2>/dev/null')
    os.system('ffmpeg -v 0 -y -f s16le -ac 1 -ar 22050 -i ' + temppath + '/silence.raw -f wav ' + temppath + '/silence.wav >/dev/null 2>/dev/null')

    os.system('lame --quiet -b 32 ' + temppath + "/silence.wav " + temppath + "/" + filename)
    
    return filename

def create_speech_file (snippettext, snippetnumber, voice, rate):
    speechaifffile = basename + '_' + str(snippetnumber) + '_text.aiff'
    speechtxtfile = basename + '_' + str(snippetnumber) + '_text.txt'
    speechfile = basename + '_' + str(snippetnumber) + '_text.mp3'
    txtout = open(temppath + "/" + speechtxtfile, 'w')
    txtout.write(snippettext)
    txtout.close()

    say_params = ["say", "-o", temppath + "/" + speechaifffile, '-f', temppath + "/" + speechtxtfile]

    if (voice):
        say_params += ["-v", voice]

    if (rate):
        say_params += ["-r", rate]

    subprocess.call(say_params)
    
    subprocess.call(['lame', '--quiet', '-b', '32', temppath + "/" + speechaifffile, temppath + "/" + speechfile])
    
    os.remove(temppath + "/" + speechaifffile)
    os.remove(temppath + "/" + speechtxtfile)
    return speechfile

def parse_subtitles(srtfile, quiet, voice, rate):
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
        
        if (quiet == False):
            print snippettext

        speechfile = create_speech_file(snippettext, snippetnumber, voice, rate)
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

def main():
    global basename
    usage = "Usage: %prog [options] subtitlefile"
    description = "Parse .srt (SubRip) format subtitles files and "\
                  + "create a .mp3 file with a text-to-speech rendition "\
                  + "of the content."
    version = "SubSpeech version 1.0"
    parser = OptionParser(usage=usage, description=description,version=version)

    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="Don't print the subtitles as they are read.")
    parser.add_option("-v", "--voice",
                      action="store", dest="voice",
                      help="Which synthesized voice to use. Passed along to "\
                      + "the 'say' command. Run 'say -v ?' for a list of "\
                      + "available voices.")
    parser.add_option("-r", "--rate",
                      action="store", dest="rate",
                      help="Speech rate. Passed along to 'say' directly.\n"\
                      + "100 = Slow, 300 = Fast, 500 = Very Fast")
    parser.add_option("-f", "--force",
                      action="store_true", dest="force_overwrite", default=False,
                      help="Force overwrite if the output file exists.")
    options, arguments = parser.parse_args()
    if len(arguments) != 1:
        parser.error("No subtitles file specified.")
    basename = os.path.basename(os.path.splitext(arguments[0])[0])
    check_output_file(basename, options.force_overwrite, options.quiet)
    parse_subtitles(arguments[0], options.quiet, options.voice, options.rate)
    os.rmdir(temppath)
    
if __name__ == '__main__':
    main()
