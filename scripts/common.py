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
import os
import tempfile
import contextlib

from typing import Any, Callable
from urllib.parse import _splittype
from urllib.error import ContentTooShortError
from urllib.request import urlopen, _url_tempfiles


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


def urlretrieve(
    url: str,
    filename: str=None,
    reporthook: Callable[[int, int, int], Any]=None,
    data: bytes=None,
    blockSize: int=1024*8
) -> tuple[str, dict]:
    '''
    urllib.request.urlretrieve with block size parameter

    Args:
        url (str): Url
        filename (str, optional): Filename. Defaults to None.
        reporthook (Callable[[int, int, int], Any], optional): Report hook. 
            Defaults to None.
        data (bytes, optional): Additional data to send. Defaults to None.
            blockSize (int, optional): Block size in bytes. Increasing this
            parameter with a good connection increases the download speed.
            Defaults to 1024*8.

    Raises:
        ContentTooShortError: Downloaded size does not match content-length

    Returns:
        tuple[str, dict]: Filename and url headers
    '''
    url_type, path = _splittype(url)

    with contextlib.closing(urlopen(url, data)) as fp:
        headers = fp.info()

        # Just return the local path and the "headers" for file://
        # URLs. No sense in performing a copy unless requested.
        if url_type == "file" and not filename:
            return os.path.normpath(path), headers

        # Handle temporary file setup.
        if filename:
            tfp = open(filename, 'wb')
        else:
            tfp = tempfile.NamedTemporaryFile(delete=False)
            filename = tfp.name
            _url_tempfiles.append(filename)

        with tfp:
            result = filename, headers
            bs = blockSize
            size = -1
            read = 0
            blocknum = 0
            if "content-length" in headers:
                size = int(headers["Content-Length"])

            if reporthook:
                reporthook(blocknum, bs, size)

            while True:
                block = fp.read(bs)
                if not block:
                    break
                read += len(block)
                tfp.write(block)
                blocknum += 1
                if reporthook:
                    reporthook(blocknum, bs, size)

    if size >= 0 and read < size:
        raise ContentTooShortError(
            "retrieval incomplete: got only %i out of %i bytes"
            % (read, size), result)

    return result
