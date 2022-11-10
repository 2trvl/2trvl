#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
               Stream Recorder               
---------------------------------------------
Download livestreams (Experimental). 
Powered by yt-dlp a youtube-dl fork with
additional features and fixes

'''
import os
import yt_dlp

#----------------------
#    Your Data Here    
#----------------------
STREAM_URL = ""
#  Where to record stream
#  Leave empty to use the current directory
DOWNLOAD_PATH = ""


#-----------------------
#    Stream Recorder    
#-----------------------
#  TODO: Parse yt_dlp arguments from cmd
if DOWNLOAD_PATH:
    os.chdir(DOWNLOAD_PATH)

YoutubeIE = yt_dlp.extractor.get_info_extractor("Youtube")

if YoutubeIE.suitable(STREAM_URL):

    ydl_opts = {
        "quiet": True,
        "no_color": True,
        "noplaylist": True,
        "live_from_start": True,
        "wait_for_video": (0, 60),
        "ignoreerrors": "only_download"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(STREAM_URL)

else:
    from datetime import datetime

    filename = datetime.now()
    filename = filename.strftime("\"%Y-%m-%d %H-%M-%S.mp4\"")

    yt_dlp.utils.Popen.run([
        "ffmpeg",
        "-i",
        STREAM_URL,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        filename
    ])
