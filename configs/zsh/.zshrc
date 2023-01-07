#    ______   ______   __  __   ______   ______   
#   /\___  \ /\  ___\ /\ \_\ \ /\  == \ /\  ___\  
#   \/_/  /__\ \___  \\ \  __ \\ \  __< \ \ \____ 
#     /\_____\\/\_____\\ \_\ \_\\ \_\ \_\\ \_____\
#     \/_____/ \/_____/ \/_/\/_/ \/_/ /_/ \/_____/
#                                                 
# dependencies (2): curl, unzip

echo -n "Loading.."
failed=()

# simple package management XD
declare -a dependencies=(
    "spaceship-prompt"
    "zsh-autosuggestions"
    "zsh-completions"
    "zsh-autopair"
    "zsh-syntax-highlighting"
)
declare -A resources=(
	[spaceship-prompt-url]=https://github.com/spaceship-prompt/spaceship-prompt/archive/refs/heads/master.zip
    [spaceship-prompt-path]="$ZDOTDIR/themes"
    [zsh-autosuggestions-url]=https://github.com/zsh-users/zsh-autosuggestions/archive/refs/heads/master.zip
    [zsh-autosuggestions-path]="$ZDOTDIR/plugins"
    [zsh-completions-url]=https://github.com/zsh-users/zsh-completions/archive/refs/heads/master.zip
    [zsh-completions-path]="$ZDOTDIR/plugins"
    [zsh-autopair-url]=https://github.com/hlissner/zsh-autopair/archive/refs/heads/master.zip
    [zsh-autopair-path]="$ZDOTDIR/plugins"
    [zsh-syntax-highlighting-url]=https://github.com/zsh-users/zsh-syntax-highlighting/archive/refs/heads/master.zip
    [zsh-syntax-highlighting-path]="$ZDOTDIR/plugins"
)
# downloader url path
downloader() {
	ping -q -c1 github.com > /dev/null

    # try to download url
	if [ $? -eq 0 ]; then
	    if [ $(curl -o /dev/null -I -L -s -w "%{http_code}" $1) != "200" ]; then
	        return 1
	    else
	        curl -o "$2" -L -s -f --create-dirs $1 > /dev/null
	    fi
	fi
}

# theme
for item in ${dependencies[@]::1}; do
    if [ -z "$DISPLAY" ]; then
        (exit 1)
    elif [ ! -d "${resources[$item-path]}/$item" ]; then
        downloader "${resources[$item-url]}" "${resources[$item-path]}/$item.zip"
    else
        continue
    fi
    
    # set defaults if failed or without X
    if [ $? -ne 0 ]; then
        PS1=$'\n'"%F{green}%n@%m%f %F{magenta}%d%f"$'\n'"> "
        PS2=""
        # right prompt git integration
        autoload -Uz vcs_info
        precmd_vcs_info() { vcs_info }
        precmd_functions+=( precmd_vcs_info )
        setopt prompt_subst
        RPS1='${vcs_info_msg_0_}'
        zstyle ':vcs_info:git:*' formats '%F{magenta}%r (%b)%f'
        zstyle ':vcs_info:*' enable git
        failed+=($item)
        break
    else
        unzip -o -q -d "${resources[$item-path]}" "${resources[$item-path]}/$item.zip"
        mv "${resources[$item-path]}/$item-master" "${resources[$item-path]}/$item"
        rm "${resources[$item-path]}/$item.zip"
    fi
done
# set theme if it's in the system
if ! declare -f precmd_vcs_info > /dev/null; then
    # custom prompt order
    SPACESHIP_PROMPT_ORDER=(
        user                     # time stamps section
        host                     # username section
        dir                      # current directory section
        git                      # git section (git_branch + git_status)
        hg                       # mercurial section (hg_branch  + hg_status)
        package                  # package version
        node                     # node.js section
        bun                      # bun section
        deno                     # deno section
        ruby                     # ruby section
        python                   # python section
        elm                      # elm section
        elixir                   # elixir section
        xcode                    # xcode section
        swift                    # swift section
        golang                   # go section
        perl                     # perl section
        php                      # php section
        rust                     # rust section
        haskell                  # haskell Stack section
        scala                    # scala section
        kotlin                   # kotlin section
        java                     # java section
        lua                      # lua section
        dart                     # dart section
        julia                    # julia section
        crystal                  # crystal section
        docker                   # docker section
        docker_compose           # docker section
        aws                      # amazon Web Services section
        gcloud                   # google Cloud Platform section
        azure                    # azure section
        venv                     # virtualenv section
        conda                    # conda virtualenv section
        dotnet                   # .net section
        ocaml                    # ocaml section
        vlang                    # v section
        zig                      # zig section
        purescript               # pureScript section
        erlang                   # erlang section
        kubectl                  # kubectl context section
        ansible                  # ansible section
        terraform                # terraform workspace section
        pulumi                   # pulumi stack section
        ibmcloud                 # ibm cloud section
        nix_shell                # nix shell
        gnu_screen               # gnu screen section
        exec_time                # execution time
        async                    # async jobs indicator
        line_sep                 # line break
        battery                  # battery level and status
        jobs                     # background jobs indicator
        exit_code                # exit code section
        sudo                     # sudo indicator
        char                     # prompt character
    )
    # username
    SPACESHIP_USER_COLOR="green"
    SPACESHIP_USER_SHOW=always
    SPACESHIP_USER_SUFFIX=""
    # hostname
    SPACESHIP_HOST_COLOR="green"
    SPACESHIP_HOST_PREFIX='@'
    SPACESHIP_HOST_SHOW=always
    # directory
    SPACESHIP_DIR_COLOR="green"
    SPACESHIP_DIR_PREFIX=""
    SPACESHIP_DIR_TRUNC=0
    # char
    SPACESHIP_CHAR_SUFFIX=" "
    SPACESHIP_CHAR_SYMBOL="❯"
    # load theme
    source "$ZDOTDIR/themes/spaceship-prompt/spaceship.zsh"
fi

# plugins
for item in ${dependencies[@]:1}; do
    if [ ! -d "${resources[$item-path]}/$item" ]; then
        downloader "${resources[$item-url]}" "${resources[$item-path]}/$item.zip"

        if [ $? -ne 0 ]; then
            failed+=($item)
        else
            unzip -o -q -d "${resources[$item-path]}" "${resources[$item-path]}/$item.zip"
            mv "${resources[$item-path]}/$item-master" "${resources[$item-path]}/$item"
            rm "${resources[$item-path]}/$item.zip"
            # rebuild zcompdump for the first time
            if [ "$item" = "zsh-completions" ]; then
                rm -f "$ZDOTDIR/.zcompdump"
            fi
            # clear url to find out that plugin has been downloaded
            resources[$item-url]=""
        fi
    else
        resources[$item-url]=""
    fi
    
    if [ -z "${resources[$item-url]}" ]; then
        case $item in
            zsh-autosuggestions)
                source "${resources[$item-path]}/zsh-autosuggestions/zsh-autosuggestions.zsh"
                ;;
            zsh-completions)
                fpath=("${resources[$item-path]}/zsh-completions/src" $fpath)
                ;;
            zsh-autopair)
                source "${resources[$item-path]}/zsh-autopair/autopair.zsh"
                autopair-init
                ;;
            zsh-syntax-highlighting)
                source "${resources[$item-path]}/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
                ;;
        esac
    fi
done

# remove all installed dependencies
uninstall() {
    rm -rf "$ZDOTDIR/themes"
    rm -rf "$ZDOTDIR/plugins"
    rm -f "$ZDOTDIR/.zcompdump"
    echo Uninstalled
}

# clear package manager vars
unset dependencies
unset resources

# history
HISTFILE="$ZDOTDIR/.zsh_history"
HISTSIZE=10000
SAVEHIST=10000
setopt hist_expire_dups_first    # expire duplicate entries first when trimming history
setopt hist_ignore_dups          # don't record an entry that was just recorded again
setopt hist_ignore_space         # ignore commands that start with space
setopt hist_verify               # show command with history expansion to user before running it
setopt inc_append_history        # write to the history file immediately, not when the shell exits
setopt share_history             # share command history data

# auto-complete
autoload -Uz compinit
# define completers
zstyle ':completion:*' completer _extensions _complete _approximate
zstyle ':completion:*:*:*:*:corrections' format '%F{yellow}!- %d (errors: %e) -!%f'
zstyle ':completion:*:*:*:*:descriptions' format '%F{blue}-- %D %d --%f'
zstyle ':completion:*:*:*:*:messages' format ' %F{purple} -- %d --%f'
zstyle ':completion:*:*:*:*:warnings' format ' %F{red}-- no matches found --%f'
# enable cache
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "$ZDOTDIR/.zsh_cache"
# colored menu
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' menu select 
zmodload zsh/complist
# case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
# group items
zstyle ':completion:*' group-name ''
# initialize completion
if [ ! -f "$ZDOTDIR/.zcompdump" ]; then
    compinit -u -d "$ZDOTDIR/.zcompdump"
fi
# include hidden files
_comp_options+=(globdots)
# make the alias a distinct command for completion
setopt complete_aliases

# keybinds
typeset -g -A keys
# load key codes
keys[Alt-E]="^[e"
keys[Alt-O]="^[o"
keys[Ctrl-Backspace]="^H"
keys[Ctrl-A]="^A"
keys[Ctrl-E]="^E"
keys[Ctrl-F]="^F"
keys[Delete]="${terminfo[kdch1]}"
keys[End]="${terminfo[kend]}"
keys[Home]="${terminfo[khome]}"
keys[Insert]="${terminfo[kich1]}"
keys[PgDn]="${terminfo[knp]}"
keys[PgUp]="${terminfo[kpp]}"
keys[Shift-Tab]="${terminfo[kcbt]}"
# extended keys from user_caps
keys[Ctrl-Down]="${terminfo[kDN5]}"
keys[Ctrl-Left]="${terminfo[kLFT5]}"
keys[Ctrl-Right]="${terminfo[kRIT5]}"
keys[Ctrl-Up]="${terminfo[kUP5]}"
# editing command in micro
autoload -Uz edit-command-line
zle -N edit-command-line
# better word-navigation
autoload -Uz select-word-style
select-word-style bash
# better history-beginning-search
autoload -Uz history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
# setup key accordingly
[ -n "${keys[Ctrl-Down]}"  ] && bindkey -- "${keys[Ctrl-Down]}"   history-beginning-search-forward-end
[ -n "${keys[Ctrl-Left]}"  ] && bindkey -- "${keys[Ctrl-Left]}"   backward-word
[ -n "${keys[Ctrl-Right]}" ] && bindkey -- "${keys[Ctrl-Right]}"  forward-word
[ -n "${keys[Ctrl-Up]}"    ] && bindkey -- "${keys[Ctrl-Up]}"     history-beginning-search-backward-end
[ -n "${keys[Delete]}"     ] && bindkey -- "${keys[Delete]}"      delete-char
[ -n "${keys[End]}"        ] && bindkey -- "${keys[End]}"         end-of-line
[ -n "${keys[Home]}"       ] && bindkey -- "${keys[Home]}"        beginning-of-line
[ -n "${keys[Insert]}"     ] && bindkey -- "${keys[Insert]}"      overwrite-mode
[ -n "${keys[PgDn]}"       ] && bindkey -- "${keys[PgDn]}"        end-of-buffer-or-history
[ -n "${keys[PgUp]}"       ] && bindkey -- "${keys[PgUp]}"        beginning-of-buffer-or-history
[ -n "${keys[Shift-Tab]}"  ] && bindkey -- "${keys[Shift-Tab]}"   reverse-menu-complete
bindkey -- "${keys[Alt-E]}"             edit-command-line
bindkey -s "${keys[Alt-O]}"             'nnn_cd\n'
bindkey -- "${keys[Ctrl-Backspace]}"    backward-kill-word
bindkey -- "${keys[Ctrl-A]}"            beginning-of-line
bindkey -- "${keys[Ctrl-E]}"            end-of-line
bindkey -- "${keys[Ctrl-F]}"            history-incremental-search-backward
# apply zsh line editor configuration, so terminfo values are valid
autoload -Uz add-zle-hook-widget
function zle_application_mode_start { echoti smkx }
function zle_application_mode_stop { echoti rmkx }
add-zle-hook-widget -Uz zle-line-init zle_application_mode_start
add-zle-hook-widget -Uz zle-line-finish zle_application_mode_stop
# clear keybinds var
unset keys

# directory stack
setopt auto_pushd                # push the current directory visited on the stack
setopt pushd_ignore_dups         # do not store duplicates in the stack
setopt pushd_silent              # do not print the directory stack after pushd or popd
# view and traversing
alias d='dirs -v'
for index ({1..9}) alias "$index"="cd +${index}"; unset index

# other options
setopt auto_cd                   # cd by typing directory name
setopt extended_glob             # treat the '#', '~' and '^' characters as part of patterns
setopt nomatch                   # save argument in history despite no match
setopt notify                    # report the status of background jobs immediately
setopt numeric_glob_sort         # sort filenames numerically when it makes sense

# disable stop/start scheme on ctrl+s/ctrl+d
stty -ixon

# aliases for ls
alias ll='ls -l'
alias la='ls -A'
alias lh='ls -lh'

# load scripts
if [ -d "$HOME/scripts" ]; then
    for pyScript in "$HOME/scripts"/*.py~(*widgets.py|*common.py)
    do
        pyScript=$(basename $pyScript)
        alias ${pyScript::-3}="$HOME/scripts/start.bat $pyScript"
    done
    unset pyScript

    for shellScript in "$HOME/scripts"/*.sh
    do
        shellScript=$(basename $shellScript)
        alias ${shellScript::-3}="$HOME/scripts/$shellScript"
    done
    unset shellScript
fi

# create dir and move to it
cm () {
    mkdir $1
    cd $1
}

# extract archive.extension
extract () {
    if [ -f $1 ]; then
        case $1 in
            *.7z)         7z x $1 ;;
            *.Z)          uncompress $1 ;;
            *.bz2)        bunzip2 $1 ;;
            *.gz)         gunzip $1 ;;
            *.rar)        unrar x $1 ;;
            *.tar)        tar xf $1 ;;
            *.tar.bz2)    tar xjf $1 ;;
            *.tar.gz)     tar xzf $1 ;;
            *.tbz)        tar -xjvf $1 ;;
            *.tbz2)       tar xjf $1 ;;
            *.tgz)        tar xzf $1 ;;
            *.xz)         tar xvf $1 ;;
            *.zip)        unzip $1 ;;
            *.zst)        tar --zstd -xf $1 ;;
            *)            echo "I don't know how to extract '$1'..." ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# pack extension file
pack () {
    if [ $1 ]; then
        case $1 in
            7z)     7z a $2.7z $2 ;;
            bz2)    bzip $2 ;;
            gz)     gzip -c -9 -n $2 > $2.gz ;;
            tar)    tar cpvf $2.tar  $2 ;;
            tbz)    tar cjvf $2.tar.bz2 $2 ;;
            tgz)    tar czvf $2.tar.gz  $2 ;;
            xz)     tar cJf $2.tar.xz $2 ;;
            zip)    zip -r $2.zip $2 ;;
            zst)    tar --zstd -cf $2.tar.zst $2 ;;
            *)      echo "'$1' cannot be packed via pack()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# print dependencies that failed to load
echo -en "\033[1K \r"
if [ -n "$DISPLAY" ]; then
    for item in ${failed[@]}; do
        echo failed: $item
    done
fi
# clear failed
unset item
unset failed

# start X server on login (tty1)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    startx
fi
