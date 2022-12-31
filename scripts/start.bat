: # Cross-platform way to run python in virtual environment
: # Just use it like this:
: # start.bat archiver.py args
: # Or any other python script in the folder
: # https://stackoverflow.com/q/17510688
: # Also loads environment variables from .env file if it exists
: #!/bin/bash

:<<"::Batch"
    @echo off
    setlocal EnableDelayedExpansion

    set filepath=%~dp0

    if not exist "%filepath%venv\" (
        echo First run, creating a virtual environment..
        python -m venv "%filepath%venv" --upgrade-deps > nul
        call "%filepath%venv\Scripts\activate.bat"
        pip install -r "%filepath%requirements.txt" --quiet
    ) else (
        call "%filepath%venv\Scripts\activate.bat"
    )

    if exist "%filepath%.env" (
        for /f "tokens=* eol=#" %%i in ('type "%filepath%.env"') do set %%i
    )

    if "%~1"=="" (
        echo Specify the script to be executed
    ) else (
        if not exist "%filepath%%~1" (
            echo No script named "%1"
        ) else (
            set args=%*
            call set args=%%args:*%1=%%
            python "%filepath%%~1" !args!
        )
    )

    deactivate
    endlocal
    exit /b
::Batch

filepath="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

if [ ! -d "$filepath/venv" ]; then
    echo -en "\033[?25lFirst run, creating a virtual environment..\r"
    python -m venv "$filepath/venv" --upgrade-deps > /dev/null
    source "$filepath/venv/bin/activate"
    pip install -r "$filepath/requirements.txt" --quiet
    echo -en "\033[2K\033[?25h"
else
    source "$filepath/venv/bin/activate"
fi

if [ -f "$filepath/.env" ]; then
    export $(grep -v "^#" "$filepath/.env" | xargs -d "\n")
fi

if [ -z "$1" ]; then
    echo "Specify the script to be executed"
elif [ ! -f "$filepath/$1" ]; then
    echo "No script named \"$1\""
else
    python "$filepath/$1" "${@:2}"
fi

if [ -f "$filepath/.env" ]; then
    unset $(grep -v "^#" "$filepath/.env" | sed -E "s/(.*)=.*/\1/" | xargs)
fi

deactivate
