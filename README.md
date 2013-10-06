SubSpeech
=========

Version 0.8

Copyright (c) 2010-2013 Alexander O'Naill

Requirements
------------

This script relies on Mac OS X's 'say' command, as such it will only
run on Mac OS X.

In addition, it relies on [LAME](http://lame.sourceforge.net/) and [FFmpeg](http://www.ffmpeg.org/). If you have [Homebrew](http://brew.sh/) installed, you can get tehse by running

    $ brew install lame ffmpeg

You will also need a C++ compiler to compile the mp3len executable. Homebrew requires the Mac OS X command-line tools to be installed, so you should already have a compiler if you have successfully installed Homebrew.

Compile
-------

The included C++ file must be compiled before you can run SubSpeech. Just run make to compile using the included Makefile, from the subspeech directory, run:

    $ make

Run
---
  
You execute the script by running it through Python.

    $ python subspeech.py <subtitle_file.srt>

The program will output an MP3 file matching the same base filename as the subtitle file.

See Also
--------

 - [SubRip](http://zuggy.wz.cz/): The utility for Microsoft Windows that rips subtitles into .srt format.

