#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
               Video Downloader              
---------------------------------------------
Downloads videos from more than a thousand
websites. Powered by yt-dlp a youtube-dl fork
with additional features and fixes

'''
import os
import yt_dlp

from widgets import show_menu

#----------------------
#    Your Data Here    
#----------------------
VIDEO_URL = ""
#  Where to download videos
#  Leave empty to use the current directory
DOWNLOAD_PATH = ""
#  If there is no sound in the video
#  Then add to it or not
VIDEO_WITH_SOUND = True


#------------------------
#    Video Downloader    
#------------------------
ydl_opts = {
    "quiet": True,
    "no_color": True,
    "format_sort": ["filesize"],
    "ignoreerrors": "only_download"
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    videoInfo = ydl.extract_info(VIDEO_URL, download=False)

    sources = {}
    
    for source in videoInfo["formats"][::-1]:
        sourceFormatted = str(source["format_id"])
        
        #  YouTube specific
        if "asr" in source and source["asr"] is None and VIDEO_WITH_SOUND:
            sourceFormatted += "+ba"

        sources["[ {} ] [ {} ] [ {} ]".format(
            source["format"].split(" - ")[1],
            source["ext"],
            yt_dlp.utils.format_bytes(source.get("filesize", None))
        )] = sourceFormatted

    indexes = show_menu(
        "Choose sources to download",
        sources.keys()
    )
    sources = list(sources.values())

    ydl.params["format"] = ",".join([sources[index] for index in indexes])
    ydl.format_selector = ydl.build_format_selector(ydl.params["format"])

    if DOWNLOAD_PATH:
        os.chdir(DOWNLOAD_PATH)

    ydl.extract_info(VIDEO_URL)
