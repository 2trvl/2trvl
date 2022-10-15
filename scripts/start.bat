: # Cross-platform way to run python in virtual environment
: # Just use it like this:
: # start.bat compare_backups.py
: # Or any other python script in the folder

:<<"::Batch"
    @echo off

    set filepath=%~dp0

    if not exist %filepath%venv\ (
        echo First run, creating a virtual environment..
        python -m venv %filepath%venv --upgrade-deps > nul
        call %filepath%venv\Scripts\activate.bat
        pip install -r %filepath%requirements.txt --quiet
    ) else (
        call %filepath%venv\Scripts\activate.bat
    )

    if "%~1"=="" (
        echo Specify the script to be executed
    ) else (
        if not exist %filepath%%~1 (
            echo No script named "%1"
        ) else (
            python %filepath%%~1
        )
    )

    deactivate
    exit /b
::Batch

filepath="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

if [ ! -d "$filepath/venv" ]; then
    echo -en "\033[?25lFirst run, creating a virtual environment..\r"
    python -m venv $filepath/venv --upgrade-deps > /dev/null
    source $filepath/venv/bin/activate
    pip install -r $filepath/requirements.txt --quiet
    echo -en "\033[2K\033[?25h"
else
    source $filepath/venv/bin/activate
fi

if [ -z "$1" ]; then
    echo "Specify the script to be executed"
elif [ ! -f "$filepath/$1" ]; then
    echo "No script named \"$1\""
else
    python $filepath/$1
fi

deactivate
