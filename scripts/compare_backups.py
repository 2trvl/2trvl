#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
          Backup comparison utility          
---------------------------------------------
Detects backups on connected drives and
compares them with the current state located
at BACKUP_DESTINATION

'''
import os
import time
import shutil
import filecmp
import zipfile
import tempfile
import multiprocessing
import charset_normalizer

from typing import IO
from itertools import filterfalse

if os.name == "nt":
    import ctypes

#----------------------
#    Your Data Here    
#----------------------
#  Filename with extension to look for on drives
#  Directory:   shterenscode
#  Compressed:  shterenscode.zip
BACKUP_FILENAME = ""
#  Path of backup with which to compare
#  /home/shteren/Desktop/shterenscode
BACKUP_DESTINATION = ""
#  Path of detailed report
REPORT_FILEPATH = "compared.txt"
#  Encoding to use when guessing the original
PREFERRED_ENCODING = "cp866"
#  Filenames to ignore in backup
IGNORE = [".git"]


#------------------------
#    Backups Comparer    
#------------------------
class dircmp(filecmp.dircmp):

    def __init__(
        self,
        leftPath: str,
        rightPath: str,
        ignore: list[str]=None,
        hide: list[str]=None,
        subdirMode: bool=False,
        leftBasePath: str="",
        rightBasePath: str="",
        progressbar: bool=False
    ):
        '''
        Better dircmp with subdirs indexing

        Args:
            leftPath (str): Left directory path
            rightPath (str): Right directory path
            ignore (list[str], optional): List of names to ignore.
                Defaults to filecmp.DEFAULT_IGNORES.
            hide (list[str], optional): List of names to hide.
                Defaults to [os.curdir, os.pardir].
            subdirMode (bool, optional): System argument indicating
                that the current comparison is for a subdirectory.
                Defaults to False.
            leftBasePath (str, optional): System argument, points
                to the root of the left directory. Needed to 
                calculate names. Defaults to "".
            rightBasePath (str, optional): System argument, points
                to the root of the right directory. Needed to 
                calculate names. Defaults to "".
            progressbar (bool, optional): Render progress bar while
                running or not. If True an object of type ProgressBar
                is created, to stop it set the finished variable to True.
                Defaults to False.
        '''
        super().__init__(leftPath, rightPath, ignore, hide)
        self.subdirMode = subdirMode
        
        if not subdirMode:
            self.leftBasePath = self.left
            self.rightBasePath = self.right
        else:
            self.leftBasePath = leftBasePath
            self.rightBasePath = rightBasePath
    
        if progressbar:
            self.postfix = multiprocessing.Array("c", 11)
            self.postfix.value = b"in process"
            self.finished = multiprocessing.Value("b", False)
            #  This class is designed in such way that when
            #  accessing a variable, make multiple function
            #  calls, so we omit counter, since it is impossible
            #  to track number of indexed files for sure
            self.renderingProcess = multiprocessing.Process(
                target=ProgressBar(40).start_rendering_mp,
                args=(self.postfix, multiprocessing.Value("i", -1), self.finished)
            )
            self.renderingProcess.start()

    def phase1(self):
        '''
        Compute common names but with subdirs
        '''
        left = dict(zip(map(os.path.normcase, self.left_list), self.left_list))
        right = dict(zip(map(os.path.normcase, self.right_list), self.right_list))
        self.common = list(map(left.__getitem__, filter(right.__contains__, left)))
        self.left_only = list(map(left.__getitem__, filterfalse(right.__contains__, left)))
        self.right_only = list(map(right.__getitem__, filterfalse(left.__contains__, right)))
        
        #  SubdirMode : Convert filenames to subdir/names
        if self.subdirMode:
            subdir = os.path.relpath(self.left, self.leftBasePath)
            #  Need to access vars in this order
            #  otherwise there will be errors
            #  common needed for common_files
            #  common_files needed for diff_files, funny_files
            dircmp.join_subdir(subdir, self.left_only)
            dircmp.join_subdir(subdir, self.right_only)
            dircmp.join_subdir(subdir, self.left_list)
            dircmp.join_subdir(subdir, self.right_list)
            dircmp.join_subdir(subdir, self.diff_files)
            dircmp.join_subdir(subdir, self.same_files)
            dircmp.join_subdir(subdir, self.funny_files)
            dircmp.join_subdir(subdir, self.common_files)
            dircmp.join_subdir(subdir, self.common_funny)
            dircmp.join_subdir(subdir, self.common)

        #  Convert to format {"filename": "filepath"}
        self.left_only = dircmp.list_to_dict(self.left_only, self.left)
        self.right_only = dircmp.list_to_dict(self.right_only, self.right)

        #  Recursively parse common dirs
        for dir in self.common_dirs:
            left = os.path.join(self.leftBasePath, dir)
            right = os.path.join(self.rightBasePath, dir)
            compared = dircmp(
                leftPath=left,
                rightPath=right,
                subdirMode=True,
                leftBasePath=self.leftBasePath,
                rightBasePath=self.rightBasePath
            )
            #  Load subdirs values
            self.left_only_dirs.update(compared.left_only_dirs)
            self.right_only_dirs.update(compared.right_only_dirs)
            self.left_only.update(compared.left_only)
            self.right_only.update(compared.right_only)
            #  Prevent adding same values when recursing
            dircmp.update_list(compared.left_list, self.left_list)
            dircmp.update_list(compared.right_list, self.right_list)
            dircmp.update_list(compared.diff_files, self.diff_files)
            dircmp.update_list(compared.same_files, self.same_files)
            dircmp.update_list(compared.funny_files, self.funny_files)
            dircmp.update_list(compared.common_dirs, self.common_dirs)
            dircmp.update_list(compared.common_files, self.common_files)
            dircmp.update_list(compared.common_funny, self.common_funny)
            dircmp.update_list(compared.common, self.common)
        
        #  Force parse left_only_dirs and right_only_dirs
        #  Cast dir names to dir/ format
        if not self.common_dirs:
            self.phase5()
    
    def phase2(self):
        '''
        Add conversion dir names to dir/ format
        '''
        super().phase2()
        common_dirs = {}
        
        dircmp.parse_dirs(
            files=self.common_dirs,
            rootPath=self.left,
            dirs=common_dirs,
            recursive=False,
            basePath=self.leftBasePath
        )
        
        self.common_dirs = dircmp.dict_to_list(common_dirs)
        
        for dir in self.common_dirs:
            oldDir = dir.split(os.sep)[-2]
            self.common.remove(oldDir)
            self.common.append(dir)

            oldDir = dir[:-1]
            self.left_list.remove(oldDir)
            self.right_list.remove(oldDir)
            
            self.left_list.append(dir)
            self.right_list.append(dir)

    def phase3(self):
        '''
        Compare files content, not only os.stat attributes
        '''
        xx = filecmp.cmpfiles(
            a=self.left,
            b=self.right,
            common=self.common_files,
            shallow=False
        )
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self):
        '''
        Find out all subdirectories not only common
        '''
        common_dirs = dircmp.list_to_dict(
            self.common_dirs,
            self.left
        )
        self.subdirs = {
            **common_dirs,
            **self.left_only_dirs,
            **self.right_only_dirs
        }

    def phase5(self):
        '''
        left_only_dirs and right_only_dirs with subdirs
        also update left_only and right_only files
        '''
        self.left_only_dirs = {}
        dircmp.parse_dirs(
            dircmp.dict_to_list(self.left_only),
            self.left,
            self.left_only_dirs,
            self.left_only,
            True,
            self.leftBasePath
        )
        #  Remove old dir names without /
        for dir in self.left_only_dirs.keys():
            self.left_only.pop(dir[:-1], None)
            if dir[:-1] in self.left_list:
                self.left_list.remove(dir[:-1])
        self.left_only.update(self.left_only_dirs)
        dircmp.update_list(
            dircmp.dict_to_list(self.left_only_dirs),
            self.left_list
        )
        
        self.right_only_dirs = {}
        dircmp.parse_dirs(
            dircmp.dict_to_list(self.right_only),
            self.right,
            self.right_only_dirs,
            self.right_only,
            True,
            self.rightBasePath
        )
        for dir in self.right_only_dirs.keys():
            self.right_only.pop(dir[:-1], None)
            if dir[:-1] in self.right_list:
                self.right_list.remove(dir[:-1])
        self.right_only.update(self.right_only_dirs)
        dircmp.update_list(
            dircmp.dict_to_list(self.right_only_dirs),
            self.right_list
        )
    
    @staticmethod
    def parse_dirs(
        files: list[str],
        rootPath: str,
        dirs: dict=None,
        dirsFiles: dict=None,
        recursive: bool=True,
        basePath: str = ""
    ):
        '''
        Parse dirs from given files in format
        {"dirname": "rootPath", "dirname/subdirname": "subdirPath"}

        And files
        {"subdir/filename": "filepath"}

        Args:
            files (list[str]): Folder files
            rootPath (str): Folder path
            dirs (dict, optional): Dict, where 
                to write dirs found among folder
                files. Defaults to None
            dirsFiles (dict, optional): Dict, 
                where to write files found 
                among folder files. Defaults
                to None
            recursive (bool, optional): Parse
                dirs recursively. Defaults to
                True
            basePath (str, optional): Indicates
                that rootPath is a subdirectory of
                another directory, allows to calculate
                the full prefix to the file:
                subdir/file vs subdir/subdir/.../file
        '''
        for file in files:
            file = file.rstrip(os.sep)
            file = file.split(os.sep)[-1]
            filepath = os.path.join(rootPath, file)
            #  Calculate full subdir prefix
            if basePath:
                file = os.path.relpath(filepath, basePath)
            
            #  Fix layering of multiple calls
            if os.path.exists(filepath):

                if os.path.isdir(filepath):
                    
                    if dirs is not None:
                        dirs[f"{file}{os.sep}"] = rootPath
                        
                        #  Recursively extract subdirs and files
                        if recursive:
                            subdirs = {}
                            subdirsFiles = {}

                            dircmp.parse_dirs(
                                os.listdir(filepath),
                                filepath,
                                subdirs,
                                subdirsFiles,
                                True,
                                basePath
                            )

                            #  Convert names to subdir/name
                            #  If basePath defined, then name calculations already done
                            if not basePath:
                                for name, filepath in subdirs.copy().items():
                                    subdir = os.path.split(filepath)[1]
                                    subdirs[f"{subdir}{os.sep}{name}"] = subdirs.pop(name)
                                for name, filepath in subdirsFiles.copy().items():
                                    subdir = os.path.split(filepath)[1]
                                    subdirsFiles[f"{subdir}{os.sep}{name}"] = subdirsFiles.pop(name)

                            dirs.update(subdirs)

                            if dirsFiles is not None:
                                dirsFiles.update(subdirsFiles)
                
                elif dirsFiles is not None:
                    dirsFiles[file] = rootPath

            elif dirsFiles:
                dirsFiles.pop(file, None)
    
    @staticmethod
    def list_to_dict(files: list[str], path) -> dict[str, str]:
        '''
        Convert filenames list to dict
        {"filename": "filepath"}

        Args:
            path (str): Filepath
            files (list[str): Filenames

        Returns:
            dict[str, str]: Converted dict
        '''
        return dict((file, path) for file in files)
    
    @staticmethod
    def dict_to_list(files: dict[str, str]) -> list[str]:
        '''
        Convert filenames dict to list
        ["filename", "subdirname/filename"]

        Args:
            files (dict[str, str]): Filenames

        Returns:
            list[str]: Converted list
        '''
        return list(files.keys())

    @staticmethod
    def join_subdir(subdir: str, files: list[str]):
        '''
        Convert filenames to subdir/name format

        Args:
            subdir (str): Subdir name to join
            files (list[str]): Filenames to convert

        Overwrites files list with changes
        '''
        for file in files.copy():
            files.append(f"{subdir}{os.sep}{file}")
            files.remove(file)
    
    @staticmethod
    def update_list(values: list, target: list):
        '''
        dictionary.update for list
        Adds values to the list only if they are not in it

        Args:
            values (list): Values to add
            target (list): List
        '''
        for value in values:
            if value not in target:
                target.append(value)

    methodmap = dict(
        subdirs=phase4,
        same_files=phase3,
        diff_files=phase3,
        funny_files=phase3,
        common_dirs=phase2,
        common_files=phase2,
        common_funny=phase2,
        common=phase1,
        left_only=phase1,
        left_only_dirs=phase5,
        right_only=phase1,
        right_only_dirs=phase5,
        left_list=filecmp.dircmp.phase0,
        right_list=filecmp.dircmp.phase0
    )


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
            _, filename = self.guess_encoding(filename)
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
                ("size", ctypes.c_int),
                ("visible", ctypes.c_byte)]

    def change_cursor_visibility(self, visibility: bool):
        '''
        Changes visibility of cursor in terminal

        Args:
            visibility (bool): Visibility of cursor.
            True to show, False to hide.
        '''
        if os.name == "nt":
            lpConsoleCursorInfo = self.CONSOLE_CURSOR_INFO()
            handle = ctypes.windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
            ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(lpConsoleCursorInfo))
            lpConsoleCursorInfo.visible = visibility
            ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(lpConsoleCursorInfo))
        else:
            ESC_CODE = self.ESC_SHOW_CURSOR if visibility else self.ESC_HIDE_CURSOR
            print(ESC_CODE, end="\r", flush=True)
    
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


def contains_only(
    string: str,
    substring: str,
    exclude: list[str]=[]
) -> bool:
    '''
    Check if a string contains a substring
    and does not contain any other substrings

    Args:
        string (str): String
        substring (str): Substring to look for in the string
        exclude (list[str], optional): Substrings that should
            not be in the string. Defaults to [].

    Returns:
        bool: A substring was found in a string and no
            substrings were found from exclude
    '''
    if not substring in string:
        return False
    if exclude:
        if any(substring in string for substring in exclude):
            return False
    return True


def insert_to_sorted(strings: list[str], sortedStrings: list[str]):
    '''
    Insert strings into an already sorted list

    Args:
        strings (list[str]): Strings to insert
        sortedStrings (list[str]): Sorted list

    Overwrites sortedStrings with inserted strings into it
    '''
    for string in strings:
        for sortedString in sortedStrings:
            if sortedString > string:
                index = sortedStrings.index(sortedString)
                sortedStrings.insert(index, string)
                break


def sorted_paths(files: list[str]) -> list[str]:
    '''
    Sort files by dirs

    Args:
        files (list[str]): Files to sort

    Returns:
        list[str]: Sorted files
    '''
    files = files.copy()
    files.sort()
    dirs = []

    #  Find dirs
    for file in files.copy():
        if file.endswith(os.sep):
            files.remove(file)
            dirs.append(file)
    
    if not dirs:
        return files

    dirs.sort()
    sortedFiles = []

    for dir in dirs.copy():
        sortedFiles.append(dir)
        dirs.remove(dir)
        for file in files.copy():
            if contains_only(file, dir, dirs):
                files.remove(file)
                sortedFiles.append(file)
    
    insert_to_sorted(files, sortedFiles)
    return sortedFiles


def print_files(title: str, files: list[str], output: IO):
    '''
    Print files list

    Args:
        title (str): List title
        files (list[str]): Files names
        output (IO): Output source. Use sys.stdout for printing in terminal
    '''
    if files:
        print(f"{title}:", file=output, flush=True)
        for file in sorted_paths(files):
            print(f"    {file}", file=output, flush=True)


def get_storage_drives() -> list[str]:
    '''
    Get available storage drives, but not system

    Returns:
        list[str]: Storage drives paths
    '''
    drives = []

    if os.name == "nt":
        bufferSize = ctypes.windll.kernel32.GetLogicalDriveStringsW(0, None)
        buffer = ctypes.create_string_buffer(bufferSize * 2)
        ctypes.windll.kernel32.GetLogicalDriveStringsW(bufferSize, buffer)
        
        drives = buffer.raw.decode("utf-16-le").split("\0")
        drives = filter(None, drives)
        
        systemDrive = os.environ.get("SYSTEMDRIVE")
        systemDrive = os.path.join(systemDrive, os.sep)
        drives = list(filter(systemDrive.__ne__, drives))
    
    #  Only Linux support (using udev and procfs)
    else:
        systemLabels = ["root", "boot", "home", "opt", "srv", "usr", "var", "tmp"]
        
        for label in os.listdir("/dev/disk/by-label"):
            if label.lower() not in systemLabels:
                device = os.readlink(f"/dev/disk/by-label/{label}")
                device = device.split("/")[-1]
                device = os.path.join(os.sep, "dev", device)
                drives.append(device)
        
        with open("/proc/mounts", "r") as mountsFile:
            mounts = mountsFile.readlines()
            mounts = [ mount.split()[:2] for mount in mounts ]

        for mount in mounts:
            device = mount[0]
            if device in drives:
                drives.remove(device)
                drives.append(mount[1])

        #  Clean up not mounted drives
        drives = list(filter(lambda drive: "/dev" not in drive, drives))

    return drives


def compare_backups():
    '''
    Detects backups on connected drives and
    compares them with the current state located
    at BACKUP_DESTINATION
    '''
    drives = get_storage_drives()
    report = open(REPORT_FILEPATH, "w")
    backupFilename = os.path.splitext(BACKUP_FILENAME)

    for drive in drives.copy():
        try:
            if BACKUP_FILENAME in os.listdir(drive):
                print(f"Found backup in {drive}")
                backupFilepath = os.path.join(drive, BACKUP_FILENAME)
                
                if backupFilename[1]:
                    print(f"Extracting {backupFilepath}")

                    if backupFilename[1] == ".zip":
                        with ZipFile(
                            file=backupFilepath,
                            mode="r",
                            preferredEncoding=PREFERRED_ENCODING,
                            ignore=IGNORE,
                            progressbar=True
                        ) as zip:
                            zip.extractall(tempfile.gettempdir())
                            zip.renderingProcess.join()

                    backupFilepath = os.path.join(tempfile.gettempdir(), backupFilename[0])

                print(f"Comparing with {BACKUP_DESTINATION}")
                compared = dircmp(
                    leftPath=BACKUP_DESTINATION,
                    rightPath=backupFilepath,
                    ignore=IGNORE,
                    progressbar=True
                )

                print(
                    f"( {BACKUP_DESTINATION}, {os.path.join(drive, BACKUP_FILENAME)} ):",
                    end="\n\n",
                    file=report,
                    flush=True
                )
                print_files(
                    "New",
                    dircmp.dict_to_list(compared.right_only),
                    report
                )
                print_files(
                    "Modified",
                    compared.diff_files,
                    report
                )
                print_files(
                    "Removed",
                    dircmp.dict_to_list(compared.left_only),
                    report
                )
                print_files(
                    "Error",
                    compared.funny_files,
                    report
                )
                print(
                    f"\n( new: {len(compared.right_only)}, modified: {len(compared.diff_files)}, removed: {len(compared.left_only)} )",
                    end="\n\n\n",
                    file=report,
                    flush=True
                )
                
                with (compared.postfix.get_lock(), compared.finished.get_lock()):
                    compared.postfix.value = f"finished{' ' * (len(compared.postfix.value) - 8)}".encode()
                    compared.finished.value = True
                
                compared.renderingProcess.join()

                print(
                    f"( new: {len(compared.right_only)}, modified: {len(compared.diff_files)}, removed: {len(compared.left_only)} )",
                    end="\n\n"
                )

                if backupFilename[1]:
                    shutil.rmtree(backupFilepath)

            else:
                raise FileNotFoundError
        
        except (PermissionError, FileNotFoundError):
            drives.remove(drive)
    
    if drives:
        print(f"View {os.path.basename(REPORT_FILEPATH)} for detailed report")
    else:
        print("No backups found")

    report.close()


if __name__ == "__main__":
    compare_backups()
