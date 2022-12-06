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
import argparse
import os

import yt_dlp

from widgets import show_menu

parser = argparse.ArgumentParser(
    description="Video Downloader",
    epilog="Additionally you can use yt_dlp options"
)
parser.add_argument(
    "url",
    help="video url"
)
parser.add_argument(
    "--download-path",
    help="where to download videos"
)
parser.add_argument(
    "--video-with-sound",
    action="store_true",
    help=(
        "if there is no sound in the video, then add to it. "
        "use for sites where video and audio are stored separately"
    )
)
args, ytDlpArgs = parser.parse_known_args()


ytDlpArgs.extend([
    "--quiet",
    "--no-colors",
    "--ignore-errors",
    "--format-sort", "filesize"
])

ydlOpts = yt_dlp.parse_options(ytDlpArgs)[-1]

with yt_dlp.YoutubeDL(ydlOpts) as ydl:
    videoInfo = ydl.extract_info(args.url, download=False)

    sources = {}
    
    for source in videoInfo["formats"][::-1]:
        sourceFormatted = str(source["format_id"])
        
        #  YouTube specific
        if "asr" in source and source["asr"] is None and args.video_with_sound:
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

    if args.download_path:
        os.chdir(args.download_path)

    ydl.extract_info(args.url)
