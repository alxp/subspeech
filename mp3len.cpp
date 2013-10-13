/*
 * This is a modified version of the code snippet from this
 * StackOverflow answer:
 *
 * http://stackoverflow.com/a/119616/19513
 * by Matt Blaine (https://github.com/mblaine)
 *
 * All StackOverflow user content is published under cc-wiki with
 * attribution required licence.
 * See: http://creativecommons.org/licenses/by-sa/3.0/
 */

// determines the duration, in milliseconds, of an MP3;
// assumes MPEG 1 (not 2 or 2.5) Audio Layer 3 (not 1 or 2)
// constant bit rate (not variable)

#include <iostream>
#include <iomanip>
#include <fstream>
#include <cstdlib>

using namespace std;

//Bitrates, assuming MPEG 1 Audio Layer 3
const int bitrates[16] = {
  0,  32000,  40000,  48000,  56000,  64000,  80000,   96000,
  112000, 128000, 160000, 192000, 224000, 256000, 320000,       0
};


// Intel processors are little-endian;
// see: http://en.wikipedia.org/wiki/Endian
int reverse(int i) {
  int toReturn = 0;
  toReturn |= ((i & 0x000000FF) << 24);
  toReturn |= ((i & 0x0000FF00) << 8);
  toReturn |= ((i & 0x00FF0000) >> 8);
  toReturn |= ((i & 0xFF000000) >> 24);
  return toReturn;
}

// In short, data in ID3v2 tags are stored as
// "syncsafe integers". This is so the tag info
// isn't mistaken for audio data, and attempted to
// be "played".
int syncsafe(int i) {
  int toReturn = 0;
  toReturn |= ((i & 0x7F000000) >> 24);
  toReturn |= ((i & 0x007F0000) >>  9);
  toReturn |= ((i & 0x00007F00) <<  6);
  toReturn |= ((i & 0x0000007F) << 21);
  return toReturn;
}

// How much room does ID3 version 1 tag info
// take up at the end of this file (if any)?
int id3v1size(ifstream& infile) {
  streampos savePos = infile.tellg();

  // get to 128 bytes from file end
  infile.seekg(0, ios::end);
  streampos length = infile.tellg() - (streampos)128;
  infile.seekg(length);

  int size;
  char buffer[3] = {0};
  infile.read(buffer, 3);
  if (buffer[0] == 'T' && buffer[1] == 'A' && buffer[2] == 'G')
    size = 128; //found tag data
  else
    size = 0; //nothing there

  infile.seekg(savePos);

  return size;
}

// How much room does ID3 version 2 tag info
// take up at the beginning of this file (if any)
int id3v2size(ifstream& infile) {
  streampos savePos = infile.tellg();
  infile.seekg(0, ios::beg);

  char buffer[6] = {0};
  infile.read(buffer, 6);
  if (buffer[0] != 'I' || buffer[1] != 'D' || buffer[2] != '3' ) {
    //no tag data
    infile.seekg(savePos);
    return 0;
  }

  int size = 0;
  infile.read(reinterpret_cast<char*>(&size), sizeof(size));
  size = syncsafe(size);

  infile.seekg(savePos);
  // "size" doesn't include the 10 byte ID3v2 header
  return size + 10;
}

int main(int argCount, char* argValues[]) {

  ifstream infile( argValues[1], ios::binary );

  if (!infile.is_open()) {
    infile.close();
    return 1;
  }

  // determine beginning and end of primary frame data (not ID3 tags)
  infile.seekg(0, ios::end);
  streampos dataEnd = infile.tellg();

  infile.seekg(0, ios::beg);
  streampos dataBegin = 0;

  dataEnd -= id3v1size(infile);
  dataBegin += id3v2size(infile);

  infile.seekg(dataBegin,ios::beg);

  // determine bitrate based on header for first frame of audio data
  int headerBytes = 0;
  infile.read(reinterpret_cast<char*>(&headerBytes),sizeof(headerBytes));

  headerBytes = reverse(headerBytes);

  // Hardcoded since output of LAME is set to 32kbps
  int bitrate = 32;
  float duration = (dataEnd - dataBegin)/(bitrate/8);

  infile.close();
  cout.setf(ios::fixed);
  // Print a long integer without scientific notation.
  cout << setprecision(0) << duration << endl;
  return 0;
}
