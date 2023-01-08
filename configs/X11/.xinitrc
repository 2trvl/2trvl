#    __  __   __   __   __   __   ______  ______   ______   
#   /\_\_\_\ /\ \ /\ "-.\ \ /\ \ /\__  _\/\  == \ /\  ___\  
#   \/_/\_\/_\ \ \\ \ \-.  \\ \ \\/_/\ \/\ \  __< \ \ \____ 
#     /\_\/\_\\ \_\\ \_\\"\_\\ \_\  \ \_\ \ \_\ \_\\ \_____\
#     \/_/\/_/ \/_/ \/_/ \/_/ \/_/   \/_/  \/_/ /_/ \/_____/
#                                                           

setxkbmap -layout us,ru -option grp:caps_toggle,grp_led:caps
xrandr --auto
# picom &
# feh bg
pgrep -x redshift > /dev/null || redshift -l 59.9343:30.3351 -b 1.0:0.8 &
exec dbus-launch bspwm
