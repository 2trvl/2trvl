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
