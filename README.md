# music_set_first_release
Search song in musicbrainz and set its date to the first found release

Songs can get released years or decades after their first release. Sometimes you want to create playlists based on release dates or decade, etc... so it's nice to be able to do that more accurately.

This script will change your song's date tag to the first found.

To run, make sure you have the necessary libraries:
  musicbrainzngs
  acoustid
  taglib
  argparse
  base64
  glob

Also, make sure you obtain API keys from Acustic ID and change them in the script. The second one I'm not exactly sure what that is or why there is a second one or where to get one, apparently the string can be anything. If you know its use, you can send the info so I can update this Readme.md file. 
