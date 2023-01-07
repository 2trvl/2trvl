#    ______   ______   __  __   ______   __   __   __   __
#   /\___  \ /\  ___\ /\ \_\ \ /\  ___\ /\ "-.\ \ /\ \ / /
#   \/_/  /__\ \___  \\ \  __ \\ \  __\ \ \ \-.  \\ \ \'/ 
#     /\_____\\/\_____\\ \_\ \_\\ \_____\\ \_\\"\_\\ \__| 
#     \/_____/ \/_____/ \/_/\/_/ \/_____/ \/_/ \/_/ \/_/  
#                                                         

# xdg vars
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_STATE_HOME="$HOME/.local/state"

# zsh home directory
export ZDOTDIR="$XDG_CONFIG_HOME/zsh"

# support 256 colors in XTerm
export TERM=xterm-256color

# default apps
export BROWSER=firefox
export EDITOR=nano
export SUDO_EDITOR=nano
export VISUAL=micro

# nnn setup
export NNN_BMS="h:$HOME;d:$HOME/Downloads"
export NNN_FIFO="/tmp/nnn.fifo"
export NNN_OPENER="$XDG_CONFIG_HOME/nnn/plugins/nuke"
export NNN_OPTS="adeHQ"
export NNN_PLUG="a:mtpmount;d:dragdrop;e:togglex;i:imgview;m:nmount;p:preview-tui;t:treeview"
export NNN_TRASH=1
# auto cd on exit
export NNN_TMPFILE="/tmp/.lastd"
nnn_cd() {
    nnn "$@"
    if [ -f "$NNN_TMPFILE" ]; then
        source "$NNN_TMPFILE"
        rm "$NNN_TMPFILE"
    fi
}
# context
C1="94" C2="87" C3="dd" C4="50" export NNN_COLORS="#$C1$C2$C3$C4"
# files
BLK="dd" CHR="dd" DIR="94" EXE="0f" \
REG="0f" HARDLINK="0f" SYMLINK="87" MISSING="0f" \
ORPHAN="87" FIFO="0f" SOCK="0f" OTHER="50" \
export NNN_FCOLORS="$BLK$CHR$DIR$EXE$REG$HARDLINK$SYMLINK$MISSING$ORPHAN$FIFO$SOCK$OTHER"
