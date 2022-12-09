'''
This file is part of 2trvl/2trvl
Personal repository with scripts and configs
Which is released under MIT License
Copyright (c) 2022 Andrew Shteren
---------------------------------------------
             Widgets For Scripts             
---------------------------------------------
Creates a options menu, dialog or input in a
terminal or dmenu (supported by dmenu, rofi)

'''
import os
from typing import TypeVar

from common import WINDOWS_VT_MODE

if WINDOWS_VT_MODE():
    import ctypes
    from ctypes import wintypes

T = TypeVar('T')
USE_DMENU = os.environ.get("USE_DMENU", "False") == "True"


def show_terminal_menu(
    prompt: str,
    items: list[str],
    indentSize: int=2
) -> set[int]:
    print(f"{prompt} (0,1,2,0-2):")
    
    for index, item in enumerate(items):
        print(f"{' ' * indentSize}{index}. {item}")
    
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


def show_terminal_dialog(question: str) -> bool | None:
    answer = input(f":: {question}? [Y/n] ")
    return parse_answer(answer)


def show_dmenu_dialog(question: str) -> bool | None:
    return False


def parse_answer(value: str) -> bool | None:
    '''
    Parses dialog answer

    Args:
        value (str): User answer

    Returns:
        bool | None: If is positive returns True,
        if not False, if the answer is not clear None
    '''
    value = value.lower()

    if value in ["yes", "y", "да"]:
        return True

    elif value in ["no", "n", "нет"]:
        return False

    return None


def show_terminal_input(prompt: str, valueType: T) -> T:
    return valueType(input(f"{prompt}:\n> "))


def show_dmenu_input(prompt: str, valueType: T) -> T:
    return valueType()


if WINDOWS_VT_MODE():

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
    if not WINDOWS_VT_MODE():
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


def show_dialog(question: str) -> bool:
    '''
    Displays a dialog based on the USE_DMENU
    environment variable

    Args:
        question (str): Closed-ended question

    Returns:
        bool: True for positive and False for
        negative answer
    '''
    while True:
        if USE_DMENU:
            answer = show_dmenu_dialog(question)
            if answer is None:
                continue
        else:
            answer = show_terminal_dialog(question)
            if answer is None:
                clear_terminal(1)
                continue
        
        return answer


def show_input(prompt: str, valueType: T) -> T:
    '''
    Displays an input based on the USE_DMENU
    environment variable

    Args:
        prompt (str): Input message or CTA
        valueType (T): The type of value to return

    Returns:
        T: Value of valueType
    '''
    while True:
        try:
            if USE_DMENU:
                return show_dmenu_input(prompt, valueType)
            return show_terminal_input(prompt, valueType)
        except ValueError:
            if not USE_DMENU:
                clear_terminal(2)
