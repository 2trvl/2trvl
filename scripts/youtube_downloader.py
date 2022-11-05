#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
              YouTube Downloader             
---------------------------------------------
Download YouTube videos without accounts and
APIs, just parsing a web page

'''
import os
import sys
import math
import json

from menus import show_menu
from common import charsForbidden

from urllib.request import (
    Request,
    urlopen,
    urlretrieve
)

#----------------------
#    Your Data Here    
#----------------------
VIDEO_URL = ""
#  Where to download videos
#  Leave empty to use the current directory
DOWNLOAD_PATH = ""
#  Delete video sources after merging
CLEAN_SOURCES = True


#--------------------------
#    YouTube Downloader    
#--------------------------
VIDEO_URL = Request(
    url=VIDEO_URL,
    headers={}
)
webPage = urlopen(VIDEO_URL)
webPage = webPage.read().decode()

#  Find all <script> tags
#  And save their content
scripts = []
searchSlice = [0, 0]

while True:

    searchSlice[0] = webPage.find(
        "<script",
        searchSlice[1]
    )
    if searchSlice[0] == -1:
        break
    
    searchSlice[0] = webPage.find(
        ">",
        searchSlice[0]
    )
    searchSlice[0] += 1

    searchSlice[1] = webPage.find(
        "</script>",
        searchSlice[0]
    )

    script = webPage[searchSlice[0]:searchSlice[1]]
    script = script.rstrip("\n")
    
    if script:
        scripts.append(script)
    
    searchSlice[1] += 9

#  Find video data in scripts
videoData = {}

for script in scripts:

    if "videoplayback" in script:
        searchSlice[0] = script.find("=") + 2
        searchSlice[1] = script.find("};")
        if searchSlice[1] != -1:
            searchSlice[1] += 2
        script = script[searchSlice[0]:searchSlice[1]]
        script = script.replace(";", "")
        videoData = json.loads(script)
        break

#  Parse video and audio formats
videos = {}
audios = {}

for source in videoData["streamingData"]["adaptiveFormats"]:

    #  Fix: recently uploaded videos and streams
    if not "url" in source:
        continue
    
    if "contentLength" in source:
        sourceSize = [ int(source["contentLength"]) ]
        sourceSize.append(int(math.log(sourceSize[0], 1024)))
        sourceSize.append([
            "B",
            "KB",
            "MB",
            "GB",
            "TB",
            "PB",
            "EB"
        ][sourceSize[1]])
        
        sourceSize = "{} {}".format(
            round(sourceSize[0] / 1024 ** sourceSize[1], 3),
            sourceSize[2]
        )
    else:
        sourceSize = "Unknown Size"

    if "video" in source["mimeType"]:
        videos["[ {} ] [ {} ] [ {} ]".format(
            source["qualityLabel"],
            source["mimeType"],
            sourceSize
        )] = [
            source["url"],
            source["qualityLabel"],
            source["mimeType"]
        ]

    elif "audio" in source["mimeType"]:
        audios["[ {} ] [ {} ] [ {} ]".format(
            source["audioQuality"],
            source["mimeType"],
            sourceSize
        )] = [
            source["url"],
            source["audioQuality"],
            source["mimeType"]
        ]

#  Choose sources to download
#  Only one video and audio
if not videos:
    print("No video with supported format and MIME type found.")
    sys.exit(0)

video = show_menu(
    "Choose video to download",
    videos.keys()
).pop()
video = list(videos.values())[video]

audio = show_menu(
    "Choose audio to download",
    audios.keys()
).pop()
audio = list(audios.values())[audio]

#  Download sources
if DOWNLOAD_PATH:
    os.chdir(DOWNLOAD_PATH)

videoData["videoDetails"]["title"] = videoData["videoDetails"]["title"].translate(charsForbidden)

#  Audio
searchSlice[0] = audio[2].find("\"") + 1
searchSlice[1] = audio[2].find(".")

if searchSlice[1] == -1:
    searchSlice[1] = audio[2].rfind("\"")

extension = audio[2][searchSlice[0]:searchSlice[1]]

audioFilename = "{} {}.{}".format(
    videoData["videoDetails"]["title"],
    audio[1],
    extension
)

print(audioFilename)
urlretrieve(audio[0], audioFilename)

#  Video
searchSlice[0] = video[2].find(" ")
extension = video[2][6:searchSlice[0]]
videoFilename = "{} {}.{}".format(
    videoData["videoDetails"]["title"],
    video[1],
    extension
)

print(videoFilename)
urlretrieve(video[0], videoFilename)

#  Merge with ffmpeg
os.system("ffmpeg -i \"{}\" -i \"{}\" -shortest \"{}.{}\"".format(
    videoFilename,
    audioFilename,
    videoData["videoDetails"]["title"],
    extension
))

#  Clean sources
if CLEAN_SOURCES:
    os.remove(videoFilename)
    os.remove(audioFilename)
