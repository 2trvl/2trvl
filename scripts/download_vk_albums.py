#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 2trvl
---------------------------------------------
             Vk Album Downloader               
---------------------------------------------
Downloads albums of the specified person or
group in VK. Saves photos at the best
resolution and writes a description 
to the metadata

'''
import os
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

#  Albums owner
OWNER_ID = ""
#  If empty all will be downloaded
ALBUMS_ID: list[int] = []


#---------------------------
#    Vk Album Downloader     
#---------------------------
vkSession = vk_api.VkApi(EMAIL, PASSWORD)
vkSession.auth()

vk = vkSession.get_api()
albums = vk.photos.getAlbums(
    owner_id=OWNER_ID,
    albums_id=ALBUMS_ID,
    need_system=1
)

if ALBUMS_ID:
    album = 0
    while album < albums["count"]:
        if albums["items"][album]["id"] not in ALBUMS_ID:
            albums["items"].pop(album)
            albums["count"] -= 1
        else:
            album += 1

albums = albums["items"]

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
