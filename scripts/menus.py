#!/usr/bin/env python3

'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
          Options Menus For Scripts          
---------------------------------------------
Creates a options menu in a terminal or dmenu
(supported by dmenu, rofi..)

'''
import os

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

USE_DMENU = os.environ.get("USE_DMENU", "False") == "True"


def show_terminal_menu(prompt: str, items: list[str]) -> set[int]:
    print(f"{prompt} (0,1,2,0-2):")
    
    for index, item in enumerate(items):
        print(f"{index}. {item}")
    
    selection = input("> ")
    return parse_selection(selection)


def show_dmenu_menu(prompt: str, items: list[str]) -> set[int]:
    return set()


def parse_selection(selection: str) -> set[int]:
    '''
    Parses menu selection

    Args:
        selection (str): Selection in format
        0,1,2,0-2

    Returns:
        set[int]: Set of selected options
        {0, 1, 2}
    '''
    selection = selection.split(",")
    indexes = set()
    
    for slice in selection:
        if slice.isnumeric():
            indexes.add(int(slice))
        else:
            slice = slice.split("-")
            indexes.update(range(int(slice[0]), int(slice[1]) + 1))

    return indexes


if os.name == "nt":

    STD_OUTPUT_HANDLE = -11

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        '''
        Structure _CONSOLE_SCREEN_BUFFER_INFO from ConsoleApi2.h
        '''
        _fields_ = [
            ("dwSize",               wintypes._COORD),
            ("dwCursorPosition",     wintypes._COORD),
            ("wAttributes",          wintypes.WORD),
            ("srWindow",             wintypes._SMALL_RECT),
            ("dwMaximumWindowSize",  wintypes._COORD)
        ]


def clear_terminal(rows: int) -> bool:
    '''
    Clears terminal screen partially

    Args:
        rows (int): Rows number to clear

    Returns:
        bool: If function succeeds, the
        return value is True
    '''
    if os.name == "posix":
        print(f"\033[{rows}A \033[0J")
        return True
    
    hConsoleOutput = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    lpConsoleScreenBufferInfo = CONSOLE_SCREEN_BUFFER_INFO()
    
    if not ctypes.windll.kernel32.GetConsoleScreenBufferInfo(
        hConsoleOutput,
        ctypes.byref(lpConsoleScreenBufferInfo)
    ): return False

    lpConsoleScreenBufferInfo.dwCursorPosition.Y -= rows
    if not ctypes.windll.kernel32.SetConsoleCursorPosition(
        hConsoleOutput,
        lpConsoleScreenBufferInfo.dwCursorPosition
    ): return False

    if not ctypes.windll.kernel32.FillConsoleOutputCharacterA(
        hConsoleOutput,
        ctypes.c_char(b' '),
        lpConsoleScreenBufferInfo.dwSize.X * rows,
        lpConsoleScreenBufferInfo.dwCursorPosition,
        ctypes.byref(wintypes.DWORD(0))
    ): return False

    ctypes.windll.kernel32.FillConsoleOutputAttribute(
        hConsoleOutput,
        lpConsoleScreenBufferInfo.wAttributes,
        lpConsoleScreenBufferInfo.dwSize.X * rows,
        lpConsoleScreenBufferInfo.dwCursorPosition,
        ctypes.byref(wintypes.DWORD(0))
    )
    return True


def show_menu(prompt: str, items: list[str]) -> set[int]:
    '''
    Displays a menu based on the USE_DMENU
    environment variable

    Args:
        prompt (str): Menu title or CTA
        items (list[str]): Items to choose

    Returns:
        list[int]: Indexes of selected items
    '''
    while True:
        try:
            if USE_DMENU:
                return show_dmenu_menu(prompt, items)
            return show_terminal_menu(prompt, items)
        except ValueError:
            if not USE_DMENU:
                clear_terminal(2 + len(items))
