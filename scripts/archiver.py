#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
                File Archiver                
---------------------------------------------
Improved file archiving, correct encoding of
names and symbolic links with progress bar

So far only supports .zip

'''
import os
import time
import zipfile
import multiprocessing
import charset_normalizer

from typing import IO

if os.name == "nt":
    import ctypes


class ProgressBar():
    
    #  ----- Constants -----
    #  Active console screen buffer
    STD_OUTPUT_HANDLE = -11
    #  ANSI escape sequences
    #  Part of common private modes
    ESC_HIDE_CURSOR = "\033[?25l"
    ESC_SHOW_CURSOR = "\033[?25h"

    def __init__(
        self,
        size: int=30,
        unit: str="",
        prefix: str="",
        frames: str="-\|/=",
        timeout: float=0.1
    ):
        '''
        Progress bar for unknown process time        

        Args:
            size (int, optional): Bar length. Defaults to 30.
            unit (str, optional): Task unit. With a negative
                counter can be used as a postfix. Defaults to "".
            prefix (str, optional): Prefix. Defaults to "".
            frames (str, optional): Animation. Last character
                for finished state. Defaults to "-\|/=".
            timeout (float, optional): Pause between renders
                used in start_rendering(). Defaults to 0.1.

        Modify the following special variables to control 
        progress bar:
            counter (int): Number of completed task units.
                Used in start_rendering()
            finished (bool): State that indicates that
                progress bar has completed
        '''
        self.size = size
        self.unit = unit
        self.prefix = prefix
        self.frames = frames
        self.timeout = timeout
        #  Special variables
        self.frame = 0
        self.counter = 0
        self.finished = False
    
    def render(self, counter: int) -> bool:
        '''
        Render progress bar

        Args:
            counter (int): Number of completed task units.
            If the counter is negative, then it is omitted

        Returns:
            bool: Should the next frame of the progress bar
            be rendered (equals to not finished)
        '''
        if counter > 0:
            counter = f" {counter}"
        else:
            counter = ""

        if not self.finished:
            self.frame += 1
            self.frame %= len(self.frames) - 1
            print(
                f"{self.prefix}[{self.frames[self.frame] * self.size}]{counter} {self.unit}",
                end="\r",
                flush=True
            )
            return True
        else:
            print(
                f"{self.prefix}[{self.frames[-1] * self.size}]{counter} {self.unit}",
                end="\n",
                flush=True
            )
            return False

    if os.name == "nt":
        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            '''
            Structure CONSOLE_CURSOR_INFO from WinCon.h
            '''
            _fields_ = [
                ("size",     ctypes.c_int),
                ("visible",  ctypes.c_byte)
            ]

    def change_cursor_visibility(self, visibility: bool):
        '''
        Changes visibility of cursor in terminal

        Args:
            visibility (bool): Visibility of cursor.
            True to show, False to hide.
        '''
        if os.name == "posix":
            ESC_CODE = self.ESC_SHOW_CURSOR if visibility else self.ESC_HIDE_CURSOR
            print(ESC_CODE, end="\r", flush=True)

        hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        lpConsoleCursorInfo = self.CONSOLE_CURSOR_INFO()
        
        if not ctypes.windll.kernel32.GetConsoleCursorInfo(
            hConsoleOutput,
            ctypes.byref(lpConsoleCursorInfo)
        ): return
        
        lpConsoleCursorInfo.visible = visibility
        ctypes.windll.kernel32.SetConsoleCursorInfo(
            hConsoleOutput,
            ctypes.byref(lpConsoleCursorInfo)
        )  
    
    def start_rendering(self):
        '''
        Threading version of start_rendering

        Change counter and finished variables to control
        '''
        self.change_cursor_visibility(False)
        while self.render(self.counter):
            time.sleep(self.timeout)
        self.change_cursor_visibility(True)

    def start_rendering_mp(
        self,
        unit: multiprocessing.Array,
        counter: multiprocessing.Value,
        finished: multiprocessing.Value
    ):
        '''
        Multiprocessing version of start_rendering

        Create counter and finished as multiprocessing.Value
        and change them from MainProcess

        Args:
            unit (multiprocessing.Array, 'c'): Unit or postfix
            counter (multiprocessing.Value, 'i'): Counter
            finished (multiprocessing.Value, 'b'): Finished
        '''
        self.change_cursor_visibility(False)
        while True:
            with (unit.get_lock(), counter.get_lock(), finished.get_lock()):
                self.unit = unit.value.decode()
                self.counter = counter.value
                self.finished = finished.value
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
        self.change_cursor_visibility(True)


class ZipFile(zipfile.ZipFile):

    def __init__(
        self,
        file: str | IO,
        mode: str="r",
        compression: int=zipfile.ZIP_STORED,
        allowZip64: bool=True,
        compresslevel: bool | int=None,
        *,
        strict_timestamps: bool=True,
        preferredEncoding: str="cp866",
        ignore: list[str]=[],
        progressbar: bool=False
    ):
        '''
        Better ZipFile with proper filename decoding & progressbar

        Args:
            file (str | IO): Either the path to the file, 
                or a file-like object
            mode (str, optional): File mode. Defaults to "r".
            compression (int, optional): ZIP_STORED (no compression),
                ZIP_DEFLATED (requires zlib), ZIP_BZIP2 (requires bz2)
                or ZIP_LZMA (requires lzma). Defaults to zipfile.ZIP_STORED.
            allowZip64 (bool, optional): if True ZipFile will create files
                with ZIP64 extensions when needed, otherwise it will raise
                an exception when this would be necessary. Defaults to True.
            compresslevel (bool | int, optional): None (default for the given
                compression type) or an integer specifying the level to pass
                to the compressor. When using ZIP_STORED or ZIP_LZMA this
                keyword has no effect. When using ZIP_DEFLATED integers 0
                through 9 are accepted. When using ZIP_BZIP2 integers 1
                through 9 are accepted. Defaults to None.
            strict_timestamps (bool, optional): Strict timestamps.
                Defaults to True.
            preferredEncoding (str, optional): Encoding to use when
                guessing the original. Defaults to "cp866".
            ignore (list[str], optional): Filenames to ignore.
                Defaults to [].
            progressbar (bool, optional): Render progress bar while
                running or not. Defaults to False.
        '''
        super().__init__(
            file=file,
            mode=mode,
            compression=compression,
            allowZip64=allowZip64,
            compresslevel=compresslevel,
            strict_timestamps=strict_timestamps
        )
        self.latestCharset = None
        self.preferredEncoding = preferredEncoding
        self.ignore = ignore
        self.progressbar = progressbar

        if progressbar:
            unit = multiprocessing.Array("c", 6)
            unit.value = b"files"
            self.counter = multiprocessing.Value("i", 0)
            self.finished = multiprocessing.Value("b", False)
            self.renderingProcess = multiprocessing.Process(
                target=ProgressBar(40).start_rendering_mp,
                args=(unit, self.counter, self.finished)
            )
            self.renderingProcess.start()
    
    def guess_encoding(self, binaryText: bytes) -> tuple[str, str]:
        '''
        Guesses encoding and decodes text using it

        Args:
            binaryText (bytes): Text to decode

        Returns:
            tuple[str, str]: Pair of encoding and decoded string
        '''
        for attempt in range(3):
            try:
                #  Guess encoding
                if not self.latestCharset:
                    encoding = charset_normalizer.detect(binaryText)["encoding"]
                    text = binaryText.decode(encoding)
                    self.latestCharset = encoding
                #  Use last guessed
                else:
                    encoding = self.latestCharset
                    text = binaryText.decode(self.latestCharset)
                #  Checking to make sure the encoding is guessed correctly
                text.encode(encoding)
                break
            except (UnicodeDecodeError, UnicodeEncodeError):
                #  Can't guess and decode with preferred & last
                #  Use historical ZIP filename encoding
                if not self.latestCharset:
                    encoding = "cp437"
                    text = binaryText.decode("cp437")
                    break
                else:
                    #  First attempt can't decode with last
                    #  Use preferred filename encoding
                    if attempt == 0 and self.latestCharset != self.preferredEncoding:
                        self.latestCharset = self.preferredEncoding
                    #  Second attempt can't decode with preferred
                    #  Try to guess
                    else:
                        self.latestCharset = None
        
        return encoding, text

    def decode_filename(self, filename: bytes) -> str:
        '''
        Decodes a filename, splitting it into parts.
        This is necessary in order to reduce the number 
        of charset_normalizer errors

        Args:
            filename (bytes): Encoded filename

        Returns:
            str: Decoded filename
        '''
        filenames = []
        for filename in filename.split(b"/"):
            __, filename = self.guess_encoding(filename)
            filenames.append(filename)
        
        filename = "/".join(filenames)
        return filename

    def open(self, name, mode="r", pwd=None, *, force_zip64=False):
        if mode not in {"r", "w"}:
            raise ValueError('open() requires mode "r" or "w"')
        if pwd and not isinstance(pwd, bytes):
            raise TypeError("pwd: expected bytes, got %s" % type(pwd).__name__)
        if pwd and (mode == "w"):
            raise ValueError("pwd is only supported for reading files")
        if not self.fp:
            raise ValueError(
                "Attempt to use ZIP archive that was already closed")

        # Make sure we have an info object
        if isinstance(name, zipfile.ZipInfo):
            # 'name' is already an info object
            zinfo = name
        elif mode == 'w':
            zinfo = zipfile.ZipInfo(name)
            zinfo.compress_type = self.compression
            zinfo._compresslevel = self.compresslevel
        else:
            # Get info object for name
            zinfo = self.getinfo(name)

        if mode == 'w':
            return self._open_to_write(zinfo, force_zip64=force_zip64)

        if self._writing:
            raise ValueError("Can't read from the ZIP file while there "
                    "is an open writing handle on it. "
                    "Close the writing handle before trying to read.")

        # Open for reading:
        self._fileRefCnt += 1
        zef_file = zipfile._SharedFile(
            self.fp,
            zinfo.header_offset,
            self._fpclose,
            self._lock,
            lambda: self._writing
        )

        try:
            # Skip the file header:
            fheader = zef_file.read(zipfile.sizeFileHeader)
            if len(fheader) != zipfile.sizeFileHeader:
                raise zipfile.BadZipFile("Truncated file header")
            fheader = zipfile.struct.unpack(zipfile.structFileHeader, fheader)
            if fheader[zipfile._FH_SIGNATURE] != zipfile.stringFileHeader:
                raise zipfile.BadZipFile("Bad magic number for file header")

            fname = zef_file.read(fheader[zipfile._FH_FILENAME_LENGTH])
            if fheader[zipfile._FH_EXTRA_FIELD_LENGTH]:
                zef_file.read(fheader[zipfile._FH_EXTRA_FIELD_LENGTH])

            if zinfo.flag_bits & 0x20:
                # Zip 2.7: compressed patched data
                raise NotImplementedError("compressed patched data (flag bit 5)")

            if zinfo.flag_bits & 0x40:
                # strong encryption
                raise NotImplementedError("strong encryption (flag bit 6)")

            if fheader[zipfile._FH_GENERAL_PURPOSE_FLAG_BITS] & 0x800:
                # UTF-8 filename
                fname_str = fname.decode("utf-8")
            else:
                #  Fix broken filenames due to incorrect encoding
                fname_str = self.decode_filename(fname)

            if fname_str != zinfo.orig_filename:
                raise zipfile.BadZipFile(
                    'File name in directory %r and header %r differ.'
                    % (zinfo.orig_filename, fname))

            # check for encrypted flag & handle password
            is_encrypted = zinfo.flag_bits & 0x1
            if is_encrypted:
                if not pwd:
                    pwd = self.pwd
                if not pwd:
                    raise RuntimeError("File %r is encrypted, password "
                                       "required for extraction" % name)
            else:
                pwd = None

            return zipfile.ZipExtFile(zef_file, mode, zinfo, pwd, True)
        except:
            zef_file.close()
            raise
    
    def extractall(self, path=None, members=None, pwd=None):
        super().extractall(path, members, pwd)
        if self.progressbar:
            with self.finished.get_lock():
                self.finished.value = True

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)
        #  Change to historical ZIP filename encoding
        member.filename = member.filename.encode("cp437")
        member.orig_filename = member.orig_filename.encode("cp437")
        #  Guess real encoding and decode
        member.filename = self.decode_filename(member.filename)
        member.orig_filename = member.filename
        #  Check if not in ignore
        if frozenset(member.filename.split("/")).intersection(self.ignore):
            return
        #  Extract member
        super()._extract_member(member, targetpath, pwd)
        #  Update progressbar if needed
        if self.progressbar and not member.is_dir():
            with self.counter.get_lock():
                self.counter.value += 1
