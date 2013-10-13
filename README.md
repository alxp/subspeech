SubSpeech
=========

Copyright &copy; 2010-2013 [Alexander O'Naill](https://github.com/alxp)

Reads a SubRip-format subtitles file and creates a text-to-speech rendition of the text, obeying the embedded timing tags. This is hopefully of use to vision-impaired or otherwise print-disabled users who can listen to the speech track while watching a film with subtitled dialogue.

Requirements
------------

 - Mac OS X
 - LAME
 - FFmpeg
 - A C++ compiler

This script relies on Mac OS X's 'say' command, as such it will only run on Mac OS X. Microsoft Windows users should check out http://subtitle-to-speech.blogspot.com/ for a GUI application that does the same thing.

In addition, it relies on [LAME](http://lame.sourceforge.net/) and [FFmpeg](http://www.ffmpeg.org/) for audio file wrangling. If you have [Homebrew](http://brew.sh/) installed, you can get tehse by running

    $ brew install lame ffmpeg

You will also need a C++ compiler to compile the mp3len.c. Homebrew requires the Mac OS X command-line tools to be installed, so you should already have a compiler if you are running Homebrew.

Compile
-------

The included C++ file must be compiled before you can run SubSpeech. Just run make to execute the included Makefile. From the subspeech directory, run:

    $ make

Run
---
  
Execute SubSpeech by running it with Python.

    $ python /path/to/subspeech.py <subtitle_file.srt>

SubSpeech creates an MP3 file with the same base filename as the supplied subtitle file. You can then add this file to your iTunes library and sync to your mobile device for later listening while watching the film or TV show.

See Also
--------

 - [SubRip](http://zuggy.wz.cz/): The utility for Microsoft Windows that rips subtitles into .srt format.

Acknowledgements
----------------

The code to determine the length of an MP3 file is based on a code snippet from [Matt Blaine](https://github.com/mblaine) in [this StackOverflow answer](http://stackoverflow.com/a/119616/19513). All user-generated content on StackOverflow is published under a Creative Commons [CC-WIKI](http://creativecommons.org/licenses/by-sa/3.0/) licence.
