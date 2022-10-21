#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Vk Album Downloader               
---------------------------------------------
Downloads albums of the specified person or
group in VK. Saves photos at the best
resolution and writes a description 
to the metadata

'''
import os
import sys
import math
import vk_api
import pyexiv2

from urllib.parse import urlparse
from urllib.request import urlretrieve

#----------------------
#    Your Data Here    
#----------------------
EMAIL = ""
PASSWORD = ""
#  Albums owner id or username
OWNER_ID = ""
#  If empty all will be downloaded
#  Use None to select albums to download in terminal
ALBUMS_ID: list[int] | None = None
#  Where to download albums
#  Leave empty to use the current directory
DOWNLOAD_PATH = ""


#---------------------------
#    Vk Album Downloader     
#---------------------------
vkSession = vk_api.VkApi(EMAIL, PASSWORD)
vkSession.auth()

vk = vkSession.get_api()

#  Username to id
if not OWNER_ID.replace("-", "", 1).isnumeric():
    OWNER_ID = vk.utils.resolveScreenName(
        screen_name=OWNER_ID
    )
    OWNER_ID["object_id"] = str(OWNER_ID["object_id"])
    #  Group id must must be indicated with the sign "-"
    if OWNER_ID["type"] == "group":
        OWNER_ID["object_id"] = f"-{OWNER_ID['object_id']}"
    OWNER_ID = OWNER_ID["object_id"]

try:
    albums = vk.photos.getAlbums(
        owner_id=OWNER_ID,
        albums_id=ALBUMS_ID,
        need_system=1
    )
except vk_api.exceptions.ApiError as ApiError:
    print(ApiError)
    sys.exit(0)

#  Albums selection mode
if ALBUMS_ID is None:
    ALBUMS_ID = []
    for index, album in enumerate(albums["items"]):
        print(f"{index}. {album['title']}")
    selection = input("\nEnter album numbers to download (0,1,2,0-2): ")
    selection = selection.split(",")
    for slice in selection:
        if slice.isnumeric():
            ALBUMS_ID.append(albums["items"][int(slice)]["id"])
        else:
            slice = slice.split("-")
            for index in range(int(slice[0]), int(slice[1]) + 1):
                ALBUMS_ID.append(albums["items"][index]["id"])

if ALBUMS_ID:
    album = 0
    while album < albums["count"]:
        if albums["items"][album]["id"] not in ALBUMS_ID:
            albums["items"].pop(album)
            albums["count"] -= 1
        else:
            album += 1

albums = albums["items"]

if DOWNLOAD_PATH:
    os.chdir(DOWNLOAD_PATH)

if OWNER_ID.startswith("-"):
    ownerName = vk.groups.getById(
        group_id=OWNER_ID[1:]
    )[0]["name"]
else:
    ownerName = vk.users.get(
        user_ids=OWNER_ID
    )[0]
    ownerName = f"{ownerName['first_name']} {ownerName['last_name']}"

ownerName = f"{OWNER_ID} {ownerName}"
os.makedirs(ownerName, exist_ok=True)
os.chdir(ownerName)

#  Characters not allowed in folder names
charsForbidden = {
    "<":  "",
    ">":  "",
    ":":  "",
    "\"": "",
    "/":  "",
    "\\": "",
    "|":  "",
    "?":  "",
    "*":  ""
}
charsForbidden = str.maketrans(charsForbidden)

for album in albums:
    print(f"Downloading \"{album['title']}\" {album['size']} photos")
    
    album["title"] = album["title"].translate(charsForbidden)
    os.makedirs(album["title"], exist_ok=True)
    os.chdir(album["title"])
    
    #  Maximum number of photos returned by photos.get is 1000
    for chunk in range(math.ceil(album["size"] / 1000)):
        photos = vk.photos.get(
            owner_id=OWNER_ID,
            album_id=album["id"],
            photo_sizes=1,
            count=1000,
            offset=chunk*1000
        )["items"]

        for photo in photos:
            #  Find photo with maximum resolution
            originalPhoto = {"width": 0, "url": ""}
            
            for size in photo["sizes"]:
                if size["width"] > originalPhoto["width"]:
                    originalPhoto["width"] = size["width"]
                    originalPhoto["url"] = size["url"]
            
            filename = urlparse(originalPhoto["url"])
            filename = filename.path.rsplit("/", 1)[1]
            filename = f"{photo['album_id']}_{filename}"
            
            urlretrieve(originalPhoto["url"], filename)
            
            #  Write description to image
            with pyexiv2.Image(filename) as image:
                image.modify_iptc({ "Iptc.Application2.Caption": photo["text"] })

            print(filename)

    os.chdir("..")
