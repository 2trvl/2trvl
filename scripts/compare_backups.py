#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 2trvl
---------------------------------------------
          Backup comparison utility          
---------------------------------------------
Detects backups on connected drives and
compares them with the current state located
at BACKUP_DESTINATION

'''
import os
import filecmp
import zipfile
import tempfile
from itertools import filterfalse

if os.name == "nt":
    import ctypes

#----------------------
#    Your Data Here    
#----------------------
#  Filename with extension to look for on drives
#  Directory:   shterenscode
#  Compressed:  shterenscode.zip
BACKUP_FILENAME = "shterenscode.zip"
#  Path of backup with which to compare
#  /home/shteren/Desktop/shterenscode
BACKUP_DESTINATION = r"C:\\Users\\2trvl\\Desktop\\shterenscode"


#------------------------
#    Backups Comparer    
#------------------------
class dircmp(filecmp.dircmp):
    '''
    Better dircmp with subdirs indexing
    '''
    def __init__(self, a, b, ignore=None, hide=None, subdirMode=False):
        super().__init__(a, b, ignore, hide)
        self.subdirMode = subdirMode

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
            subdir = os.path.split(self.left)[1]
            #  Need to access vars in this order
            #  otherwise there will be errors
            #  common needed for common_dirs, common_files
            #  common_files needed for diff_files, funny_files
            dircmp.join_subdir(subdir, self.left_only)
            dircmp.join_subdir(subdir, self.right_only)
            dircmp.join_subdir(subdir, self.left_list)
            dircmp.join_subdir(subdir, self.right_list)
            dircmp.join_subdir(subdir, self.diff_files)
            dircmp.join_subdir(subdir, self.same_files)
            dircmp.join_subdir(subdir, self.funny_files)
            dircmp.join_subdir(subdir, self.common_dirs)
            dircmp.join_subdir(subdir, self.common_files)
            dircmp.join_subdir(subdir, self.common_funny)
            dircmp.join_subdir(subdir, self.common)

        #  Convert to format {"filename": "filepath"}
        self.left_only = dircmp.list_to_dict(self.left_only, self.left)
        self.right_only = dircmp.list_to_dict(self.right_only, self.right)

        #  Recursively parse common dirs
        for dir in self.common_dirs:
            dir = dir.split("/")[-2]
            left = os.path.join(self.left, dir)
            right = os.path.join(self.right, dir)
            compared = dircmp(left, right, subdirMode=True)
            #  Load subdirs values
            self.left_only_dirs.update(compared.left_only_dirs)
            self.right_only_dirs.update(compared.right_only_dirs)
            self.left_only.update(compared.left_only)
            self.right_only.update(compared.right_only)
            self.left_list.extend(compared.left_list)
            self.right_list.extend(compared.right_list)
            self.diff_files.extend(compared.diff_files)
            self.same_files.extend(compared.same_files)
            self.funny_files.extend(compared.funny_files)
            self.common_dirs.extend(compared.common_dirs)
            self.common_files.extend(compared.common_files)
            self.common_funny.extend(compared.common_funny)
            self.common.extend(compared.common)
        
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
            recursive=False
        )
        
        self.common_dirs = dircmp.dict_to_list(common_dirs)
        
        for dir in self.common_dirs:
            self.common.remove(dir[:-1])
            self.common.append(dir)

            #  Get full /subdir/subdir/dir name
            dir = dircmp.remove_if_contains(dir[:-1], self.left_list)
            self.right_list.remove(dir)
            
            dir = f"{dir}/"
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
            self.left_only
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
            self.right_only
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
        recursive: bool=True
    ):
        '''
        Parse dirs from given files in format
        {"dirname": "rootPath", "subdirname": "subdirPath"}

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
        '''
        for file in files:
            #  Fix layering of multiple calls
            file = file.rstrip("/")
            filepath = os.path.join(rootPath, file)
            
            if os.path.isdir(filepath):
                
                if dirs is not None:
                    dirs[f"{file}/"] = rootPath
                    
                    #  Recursively extract subdirs and files
                    if recursive:
                        subdirs = {}
                        subdirsFiles = {}

                        dircmp.parse_dirs(
                            os.listdir(filepath),
                            filepath,
                            subdirs,
                            subdirsFiles
                        )

                        #  Convert names to subdir/name
                        for name, filepath in subdirs.copy().items():
                            subdir = os.path.split(filepath)[1]
                            subdirs[f"{subdir}/{name}"] = subdirs.pop(name)
                        for name, filepath in subdirsFiles.copy().items():
                            subdir = os.path.split(filepath)[1]
                            subdirsFiles[f"{subdir}/{name}"] = subdirsFiles.pop(name)

                        dirs.update(subdirs)

                        if dirsFiles is not None:
                            dirsFiles.update(subdirsFiles)
            
            elif dirsFiles is not None:
                dirsFiles[file] = rootPath
    
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
            files.append(f"{subdir}/{file}")
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

    @staticmethod
    def remove_if_contains(substring: str, strings: list[str]) -> str:
        '''
        Remove string from a list that contain a substring

        Args:
            substring (str): Substring to look
            strings (list[str]): List of strings

        Returns:
            (str): Removed string
        '''
        for string in strings.copy():
            if substring in string:
                strings.remove(string)
                return string

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
            if sortedString < string:
                index = sortedStrings.index(sortedString) + 1
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
        if file.endswith("/"):
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


def print_files(title: str, files: list[str]):
    '''
    Print files list
    Args:
        title (str): List title
        files (list[str]): Files names
    '''
    if files:
        print(f"{title}:")
        for file in sorted_paths(files):
            print(f"    {file}")


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
    
    #  Only Linux support
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

    for drive in drives:
        try:
            if BACKUP_FILENAME in os.listdir(drive):
                print(f"Found backup in {drive}")
                filepath = os.path.join(drive, BACKUP_FILENAME)
                filename = os.path.splitext(BACKUP_FILENAME)
                
                if filename[1]:
                    print(f"Extracting {BACKUP_FILENAME}")
                    '''
                    if filename[1] == ".zip":
                        with zipfile.ZipFile(filepath, "r") as zip:
                            zip.extractall(tempfile.gettempdir())
                    '''
                    filepath = os.path.join(tempfile.gettempdir(), filename[0])

                compared = dircmp(BACKUP_DESTINATION, filepath)
                
                print_files(
                    "New",
                    dircmp.dict_to_list(compared.right_only)
                )
                print_files(
                    "Modified",
                    compared.diff_files
                )
                print_files(
                    "Removed",
                    dircmp.dict_to_list(compared.left_only)
                )
                print_files(
                    "Error",
                    compared.funny_files
                )

                if filename[1]:
                    os.rmdir(filepath)
        
        except PermissionError:
            pass


if __name__ == "__main__":
    compare_backups()
