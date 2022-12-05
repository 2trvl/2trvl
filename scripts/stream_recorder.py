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
import argparse

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
