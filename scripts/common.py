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

    ANSI codes are available from Windows 10
    version 1511, but must be enabled in the
    registry, there are also a few bugs

    Escape codes are available by default
    in Windows version 1909 or newer
    '''
    if os.name == "nt":
        version = platform.win32_ver()[1]
        version = tuple(int(num) for num in version.split("."))
        if version < (10, 0, 18363):
            return True

    return False
