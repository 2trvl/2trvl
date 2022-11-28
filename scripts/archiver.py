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
import shutil
import zipfile
import itertools
import multiprocessing
import charset_normalizer

from typing import IO, Iterator
from operator import attrgetter

from common import WINDOWS_VT_MODE
from widgets import clear_terminal

if WINDOWS_VT_MODE:
    import ctypes


class ProgressBar():

    def __init__(
        self,
        size: int=30,
        unit: str="",
        prefix: str="",
        frames: str="-\|/=",
        timeout: float=0.1,
        clearMode: bool=False
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
            clearMode (bool, optional): Redraws each frame of
                the progress bar, clearing the previous one.
                It makes sense to activate this option if you
                are changing the prefix, unit, or even the size.
                Otherwise, characters of previous frame will remain
                in the terminal if it was longer. Defaults to False.

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
        self.clearMode = clearMode
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
        if counter >= 0:
            counter = f" {counter}"
        else:
            counter = ""

        if self.clearMode:
            end = "\n"
        else:
            end = "\r"

        if self.finished:
            end = "\n"
            self.frame = -1
        else:
            self.frame += 1
            self.frame %= len(self.frames) - 1

        print(
            f"{self.prefix}[{self.frames[self.frame] * self.size}]{counter} {self.unit}",
            end=end,
            flush=True
        )

        return not self.finished

    if WINDOWS_VT_MODE:
        #  Active console screen buffer
        STD_OUTPUT_HANDLE = -11

        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            '''
            Structure CONSOLE_CURSOR_INFO from WinCon.h
            '''
            _fields_ = [
                ("size",     ctypes.c_int),
                ("visible",  ctypes.c_byte)
            ]
    else:
        #  ANSI escape sequences
        #  Part of common private modes
        ESC_HIDE_CURSOR = "\033[?25l"
        ESC_SHOW_CURSOR = "\033[?25h"

    def change_cursor_visibility(self, visibility: bool):
        '''
        Changes visibility of cursor in terminal

        Args:
            visibility (bool): Visibility of cursor.
            True to show, False to hide.
        '''
        if not WINDOWS_VT_MODE:
            ESC_CODE = self.ESC_SHOW_CURSOR if visibility else self.ESC_HIDE_CURSOR
            print(ESC_CODE, end="\r", flush=True)
            return

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

        Might be unsafe without locks, but it shouldn't be
        If you change variables in one thread
        But if in several, then manage locks yourself
        '''
        self.change_cursor_visibility(False)
        while True:
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
            if self.clearMode:
                clear_terminal(1)
        self.change_cursor_visibility(True)

    def start_rendering_mp(
        self,
        prefix: multiprocessing.Array,
        counter: multiprocessing.Value,
        unit: multiprocessing.Array,
        finished: multiprocessing.Value
    ):
        '''
        Multiprocessing version of start_rendering

        Create counter and finished as multiprocessing.Value
        and change them from MainProcess

        Args:
            prefix (multiprocessing.Array, 'c'): Prefix
            counter (multiprocessing.Value, 'i'): Counter
            unit (multiprocessing.Array, 'c'): Unit or postfix
            finished (multiprocessing.Value, 'b'): Finished
        '''
        self.change_cursor_visibility(False)
        while True:
            with (
                prefix.get_lock(),
                counter.get_lock(),
                unit.get_lock(),
                finished.get_lock()
            ):
                self.prefix = prefix.value.decode()
                self.counter = counter.value
                self.unit = unit.value.decode()
                self.finished = finished.value
            if not self.render(self.counter):
                break
            time.sleep(self.timeout)
            if self.clearMode:
                clear_terminal(1)
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
        overwriteDuplicates: bool=False,
        progressbar: bool=False,
        useBarPrefix: bool=True,
        clearBarAfterFinished: bool=False
    ):
        '''
        Better ZipFile with proper names and symlinks encoding & progressbar

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
            overwriteDuplicates (bool, optional): Overwrite if file exists
                or write filename with number in it. If you are going to
                enable this option - open archive in 'a' mode.
                Defaults to False
            progressbar (bool, optional): Render progress bar while
                running or not. Defaults to False.
            useBarPrefix (bool, optional): Show progress bar prefix, disable
                this option if your program itself prints events to the terminal.
                Defaults to True
            clearBarAfterFinished (bool, optional): Clears progress bar after it's
                finished. Defaults to False

        If you use progressbar option on Windows - run your code in the
        "if __name__ == '__main__'" statement
        '''
        self.latestCharset = None
        self.preferredEncoding = preferredEncoding
        
        super().__init__(
            file=file,
            mode=mode,
            compression=compression,
            allowZip64=allowZip64,
            compresslevel=compresslevel,
            strict_timestamps=strict_timestamps
        )

        self.ignore = ignore
        self.overwriteDuplicates = overwriteDuplicates
        
        self.progressbar = progressbar

        if progressbar:
            self.prefix = multiprocessing.Array("c", 272)
            self.prefix.value = b""
            self.counter = multiprocessing.Value("i", 0)
            self.unit = multiprocessing.Array("c", 6)
            self.unit.value = b"files"
            self.finished = multiprocessing.Value("b", False)
            self._start_progressbar(createOnly=True)
        
        self.useBarPrefix = useBarPrefix
        self.clearBarAfterFinished = clearBarAfterFinished

    def _start_progressbar(self, createOnly: bool=False):
        '''
        Start progress bar
        Because we cannot restart a terminated process.
        We need to instantiate a new.

        Args:
            createOnly (bool, optional): Don't start renderingProcess
            after creating. Defaults to False.
        '''
        self.renderingProcess = multiprocessing.Process(
            target=ProgressBar(40).start_rendering_mp,
            args=(self.prefix, self.counter, self.unit, self.finished)
        )
        if not createOnly:
            self.renderingProcess.start()

    def _reset_progressbar(self):
        '''
        Reset progress bar values to defaults
        '''
        self.prefix.value = b""
        self.counter.value = 0
        self.unit.value = b"files"
        self.finished.value = False

    def _finish_progressbar(self):
        '''
        Finish progressbar
        '''
        if self.progressbar and self.renderingProcess.is_alive():
            with self.finished.get_lock():
                self.finished.value = True
            self.renderingProcess.join()
            if self.clearBarAfterFinished:
                clear_terminal(1)
            self._reset_progressbar()
    
    def _RealGetContents(self):
        '''
        Read in the table of contents for the ZIP file.
        '''
        fp = self.fp
        try:
            endrec = zipfile._EndRecData(fp)
        except OSError:
            raise zipfile.BadZipFile("File is not a zip file")
        if not endrec:
            raise zipfile.BadZipFile("File is not a zip file")
        if self.debug > 1:
            print(endrec)
        size_cd = endrec[zipfile._ECD_SIZE]             # bytes in central directory
        offset_cd = endrec[zipfile._ECD_OFFSET]         # offset of central directory
        self._comment = endrec[zipfile._ECD_COMMENT]    # archive comment

        # "concat" is zero, unless zip was concatenated to another file
        concat = endrec[zipfile._ECD_LOCATION] - size_cd - offset_cd
        if endrec[zipfile._ECD_SIGNATURE] == zipfile.stringEndArchive64:
            # If Zip64 extension structures are present, account for them
            concat -= (zipfile.sizeEndCentDir64 + zipfile.sizeEndCentDir64Locator)

        if self.debug > 2:
            inferred = concat + offset_cd
            print("given, inferred, offset", offset_cd, inferred, concat)
        # self.start_dir:  Position of start of central directory
        self.start_dir = offset_cd + concat
        fp.seek(self.start_dir, 0)
        data = fp.read(size_cd)
        fp = zipfile.io.BytesIO(data)
        total = 0
        while total < size_cd:
            centdir = fp.read(zipfile.sizeCentralDir)
            if len(centdir) != zipfile.sizeCentralDir:
                raise zipfile.BadZipFile("Truncated central directory")
            centdir = zipfile.struct.unpack(zipfile.structCentralDir, centdir)
            if centdir[zipfile._CD_SIGNATURE] != zipfile.stringCentralDir:
                raise zipfile.BadZipFile("Bad magic number for central directory")
            if self.debug > 2:
                print(centdir)
            filename = fp.read(centdir[zipfile._CD_FILENAME_LENGTH])
            flags = centdir[5]
            if flags & 0x800:
                # UTF-8 file names extension
                filename = filename.decode('utf-8')
            else:
                #------------------------------------------------------
                #    Fix broken filenames due to incorrect encoding    
                #------------------------------------------------------
                filename = self.decode_filename(filename)
            # Create ZipInfo instance to store file information
            x = zipfile.ZipInfo(filename)
            x.extra = fp.read(centdir[zipfile._CD_EXTRA_FIELD_LENGTH])
            x.comment = fp.read(centdir[zipfile._CD_COMMENT_LENGTH])
            x.header_offset = centdir[zipfile._CD_LOCAL_HEADER_OFFSET]
            (x.create_version, x.create_system, x.extract_version, x.reserved,
             x.flag_bits, x.compress_type, t, d,
             x.CRC, x.compress_size, x.file_size) = centdir[1:12]
            if x.extract_version > zipfile.MAX_EXTRACT_VERSION:
                raise NotImplementedError("zip file version %.1f" %
                                          (x.extract_version / 10))
            x.volume, x.internal_attr, x.external_attr = centdir[15:18]
            # Convert date/time code to (year, month, day, hour, min, sec)
            x._raw_time = t
            x.date_time = ( (d>>9)+1980, (d>>5)&0xF, d&0x1F,
                            t>>11, (t>>5)&0x3F, (t&0x1F) * 2 )

            x._decodeExtra()
            x.header_offset = x.header_offset + concat
            self.filelist.append(x)
            self.NameToInfo[x.filename] = x

            # update total bytes read from central directory
            total = (total + zipfile.sizeCentralDir + centdir[zipfile._CD_FILENAME_LENGTH]
                     + centdir[zipfile._CD_EXTRA_FIELD_LENGTH]
                     + centdir[zipfile._CD_COMMENT_LENGTH])

            if self.debug > 2:
                print("total", total)
    
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

    def get_unique_filename(self, filename: str) -> Iterator[str]:
        '''
        Unique name generator: adds a number to the filename
        
        Used to rename duplicates if the overwriteDuplicates
        parameter is disabled

        Args:
            filename (str): Filename

        Yields:
            Iterator[str]: filename (1), filename (2) ...
        '''
        filename, extension = os.path.splitext(filename)
        number = itertools.count(1)
        
        while True:
            yield f"{filename} ({next(number)}){extension}"

    def open(self, name, mode="r", pwd=None, *, force_zip64=False):
        '''
        Return file-like object for 'name'.

        name is a string for the file name within the ZIP file, or a ZipInfo
        object.

        mode should be 'r' to read a file already in the ZIP file, or 'w' to
        write to a file newly added to the archive.

        pwd is the password to decrypt files (only used for reading).

        When writing, if the file size is not known in advance but may exceed
        2 GiB, pass force_zip64 to use the ZIP64 format, which can handle large
        files.  If the size is known in advance, it is best to pass a ZipInfo
        instance for name, with zinfo.file_size set.
        '''
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
                #------------------------------------------------------
                #    Fix broken filenames due to incorrect encoding    
                #------------------------------------------------------
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
    
    def extract(self, member, path=None, pwd=None) -> str:
        '''
        Extract a member from the archive to the current working directory,
        using its full name. Its file information is extracted as accurately
        as possible. `member' may be a filename or a ZipInfo object. You can
        specify a different directory using `path'.
        '''
        if isinstance(member, zipfile.ZipInfo):
            member = member.filename

        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        if self.progressbar and not self.renderingProcess.is_alive():
            if self.useBarPrefix:
                filename = os.path.basename(member.rstrip("/"))
                self.prefix.value = f"Extracting \"{filename}\" : ".encode()
            if not member.endswith("/"):
                self.counter.value = -1
                self.unit.value = b""
            self._start_progressbar()

        targetpath = self._extract_member(member, path, pwd)
        #  extract directory contents
        if targetpath != path and os.path.isdir(targetpath):
            members = [ name for name in self.namelist() if member in name ][1:]
            self.extractall(path, members)

        self._finish_progressbar()

        return targetpath

    def extractall(self, path=None, members=None, pwd=None):
        '''
        Extract all members from the archive to the current working
        directory. `path' specifies a different directory to extract to.
        `members' is optional and must be a subset of the list returned
        by namelist().
        '''
        if self.progressbar and not self.renderingProcess.is_alive():
            if self.useBarPrefix:
                self.prefix.value = f"Extracting \"{self.filename}\" : ".encode()
            self._start_progressbar()
        
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        skip = ""
        for zipinfo in members:
            #  skip nested files if any
            if skip:
                if skip in zipinfo:
                    continue
                else:
                    skip = ""
            targetpath = self._extract_member(zipinfo, path, pwd)
            #  name was found in ignore, add path to skip
            if targetpath == path:
                skip = zipinfo
        
        self._finish_progressbar()

    def _extract_member(self, member, targetpath, pwd) -> str:
        '''
        Extract the ZipInfo object 'member' to a physical
        file on the path targetpath.
        '''
        #  Extract filename
        if isinstance(member, str):
            filename = member
        elif isinstance(member, zipfile.ZipInfo):
            filename = member.filename
        
        #  Check if not in ignore
        if frozenset(filename.split("/")).intersection(self.ignore):
            return targetpath
        
        #  Extract member, original _extract_member() code
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        # build the destination pathname, replacing
        # forward slashes to platform specific separators.
        arcname = member.filename.replace('/', os.path.sep)

        if os.path.altsep:
            arcname = arcname.replace(os.path.altsep, os.path.sep)
        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        invalid_path_parts = ('', os.path.curdir, os.path.pardir)
        arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                   if x not in invalid_path_parts)
        if os.path.sep == '\\':
            # filter illegal characters on Windows
            arcname = self._sanitize_windows_name(arcname, os.path.sep)

        targetpath = os.path.join(targetpath, arcname)
        targetpath = os.path.normpath(targetpath)
        
        #  Deal with duplicates
        if os.path.exists(targetpath):
            if self.overwriteDuplicates:
                if member.is_dir():
                    shutil.rmtree(targetpath)
                else:
                    os.remove(targetpath)
            else:
                #  Don't rename dirs only files
                if not member.is_dir():
                    targetpath, name = os.path.split(targetpath)
                    for name in self.get_unique_filename(name):
                        name = os.path.join(targetpath, name)
                        if not os.path.exists(name):
                            targetpath = name
                            break

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if member.is_dir():
            if not os.path.isdir(targetpath):
                os.mkdir(targetpath)
            return targetpath

        with self.open(member, pwd=pwd) as source, \
             open(targetpath, "wb") as target:
            shutil.copyfileobj(source, target)
        
        #  TODO: if '__SYMLINK__' in filename -> unpack properly

        #  Update progressbar if needed
        if self.progressbar and self.counter.value != -1:
            with self.counter.get_lock():
                self.counter.value += 1
        
        return targetpath

    def write(
        self,
        filename,
        arcname=None,
        compress_type=None,
        compresslevel=None
    ):
        '''
        Better zipfile.write which supports writing
        symlinks and directories

        Put the bytes from filename into the archive under the name
        arcname.
        '''
        if arcname is None:
            arcname = "{}/{}".format(
                os.path.splitext(self.filename)[0],
                os.path.basename(filename.rstrip("/"))
            )

        if self.progressbar and not self.renderingProcess.is_alive():
            if self.useBarPrefix:
                self.prefix.value = f"Writing \"{arcname}\" : ".encode()
            if os.path.isfile(filename):
                self.counter.value = -1
                self.unit.value = b""
            self._start_progressbar()
        
        self._write(filename, arcname, compress_type, compresslevel)

        self._finish_progressbar()

    def _write(
        self,
        filename,
        arcname,
        compress_type=None,
        compresslevel=None
    ):
        '''
        Real zipfile.write, recursive
        '''
        if frozenset(arcname.split("/")).intersection(self.ignore):
            return

        #  Check for dir trailing slash
        if os.path.isfile(filename):
            trailingSlash = ""
        else:
            trailingSlash = "/"
            if not arcname.endswith("/"):
                arcname += "/"

        #  Deal with duplicates
        if arcname in self.namelist():
            if self.overwriteDuplicates:
                self.remove(arcname)
            else:
                arcname, name = os.path.split(arcname.rstrip("/"))
                for name in self.get_unique_filename(name):
                    name = f"{arcname}/{name}{trailingSlash}"
                    if name not in self.namelist():
                        arcname = name
                        break

        if not trailingSlash:
            #  TODO: Make symlinks convertor
            #  if os.path.islink -> super().writestr()
            super().write(filename, arcname, compress_type, compresslevel)

            if self.progressbar and self.counter.value != -1:
                with self.counter.get_lock():
                    self.counter.value += 1
        
        else:
            super().write(filename, arcname, compress_type, compresslevel)
            
            for file in sorted(os.listdir(filename)):
                self._write(
                    filename=os.path.join(filename, file),
                    arcname=os.path.join(arcname, file),
                    compress_type=compress_type,
                    compresslevel=compresslevel
                )
    
    def remove(self, member):
        '''
        Remove a file from the archive. The archive must be open with mode 'a'
        
        CPython commit 659eb048cc9cac73c46349eb29845bc5cd630f09
        '''

        if self.mode != 'a':
            raise RuntimeError("remove() requires mode 'a'")
        if not self.fp:
            raise ValueError(
                "Attempt to write to ZIP archive that was already closed")
        if self._writing:
            raise ValueError(
                "Can't write to ZIP archive while an open writing handle exists."
            )

        # Make sure we have an info object
        if isinstance(member, zipfile.ZipInfo):
            # 'member' is already an info object
            zinfo = member
        else:
            # get the info object
            zinfo = self.getinfo(member)

        return self._remove_member(zinfo)

    def _remove_member(self, member):
        # get a sorted filelist by header offset, in case the dir order
        # doesn't match the actual entry order
        fp = self.fp
        entry_offset = 0
        filelist = sorted(self.filelist, key=attrgetter('header_offset'))
        for i in range(len(filelist)):
            info = filelist[i]
            # find the target member
            if info.header_offset < member.header_offset:
                continue

            # get the total size of the entry
            entry_size = None
            if i == len(filelist) - 1:
                entry_size = self.start_dir - info.header_offset
            else:
                entry_size = filelist[i + 1].header_offset - info.header_offset

            # found the member, set the entry offset
            if member == info:
                entry_offset = entry_size
                continue

            # Move entry
            # read the actual entry data
            fp.seek(info.header_offset)
            entry_data = fp.read(entry_size)

            # update the header
            info.header_offset -= entry_offset

            # write the entry to the new position
            fp.seek(info.header_offset)
            fp.write(entry_data)
            fp.flush()

        # update state
        self.start_dir -= entry_offset
        self.filelist.remove(member)
        del self.NameToInfo[member.filename]
        self._didModify = True

        # seek to the start of the central dir
        fp.seek(self.start_dir)
