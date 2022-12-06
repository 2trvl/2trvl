'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Scripts Common Parts            
---------------------------------------------
Code that cannot be attributed to anything in
particular and is used in several scripts

'''
import functools
import os
import platform

#  Characters not allowed in file names
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


@functools.cache
def WINDOWS_VT_MODE() -> bool:
    '''
    Determines if ANSI escape codes
    are available or Windows API needed
    '''
    if os.name == "nt":
        version = platform.win32_ver()[1]
        version = tuple(int(num) for num in version.split("."))
        if version < (10, 0, 10586):
            return True

    return False
