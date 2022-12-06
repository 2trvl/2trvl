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
import argparse
import os

import yt_dlp

parser = argparse.ArgumentParser(
    description="Stream Recorder",
    epilog="Additionally you can use yt_dlp options"
)
parser.add_argument(
    "url",
    help="stream url"
)
parser.add_argument(
    "--download-path",
    help="where to record stream"
)
args, ytDlpArgs = parser.parse_known_args()


if args.download_path:
    os.chdir(args.download_path)

try:
    ydlOpts = yt_dlp.parse_options(ytDlpArgs)[-1]

    #  Sites specific args
    YoutubeIE = yt_dlp.extractor.get_info_extractor("Youtube")
    TwitchStreamIE = yt_dlp.extractor.get_info_extractor("TwitchStream")
    
    if YoutubeIE.suitable(args.url):
        ydlOpts.update({
            "noplaylist": True,
            "live_from_start": True,
            "wait_for_video": (0, 60)
        })

    elif TwitchStreamIE.suitable(args.url):
        ydlOpts.update({ "fixup": "never" })

    with yt_dlp.YoutubeDL(ydlOpts) as ydl:
        ydl.extract_info(args.url)

except yt_dlp.utils.DownloadError:
    from datetime import datetime

    filename = datetime.now()
    filename = filename.strftime("\"%Y-%m-%d %H-%M-%S.mp4\"")

    yt_dlp.utils.Popen.run([
        "ffmpeg",
        "-i",
        args.url,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        filename
    ])
