# Packages

Firmware, VA-API and Vulkan

## Arch Linux

intel:
```
sudo pacman -S xf86-video-intel
sudo pacman -S libva libva-utils libva-intel-driver vulkan-intel
sudo pacman -S lib32-libva lib32-libva-intel-driver lib32-vulkan-intel
sudo pacman -S intel-ucode linux-headers
```

nvidia (390xx, 470xx, etc):
```
yay -S nvidia-390xx nvidia-390xx-utils nvidia-390xx-settings nvidia-390xx-dkms opencl-nvidia-390xx
yay -S lib32-nvidia-390xx-utils lib32-opencl-nvidia-390xx
sudo pacman -S dkms
```

for nvidia geforce 620-900, quadro/tesla/tegra k series and newer install:
```
sudo pacman -S nvidia nvidia-utils nvidia-settings nvidia-dkms opencl-nvidia libvdpau
sudo pacman -S lib32-nvidia-utils lib32-opencl-nvidia lib32-libvdpau
sudo pacman -S dkms
```

amd:
```
sudo pacman -S xf86-video-amdgpu
sudo pacman -S libva-mesa-driver mesa-vdpau vulkan-radeon
sudo pacman -S lib32-libva-mesa-driver lib32-mesa-vdpau lib32-vulkan-radeon
sudo pacman -S dkms
```

## Void Linux

intel:
```
sudo xbps-install xf86-video-intel linux-firmware-intel intel-video-accel
sudo xbps-install libva libva-utils libva-intel-driver vulkan-loader
sudo xbps-install libva-32bit libva-intel-driver-32bit vulkan-loader-32bit
sudo xbps-install intel-ucode linux-headers
```

nvidia:
```
sudo xbps-install nvidia nvidia-dkms nvidia-libs nvidia-opencl
sudo xbps-install nvidia-libs-32bit nvidia-opencl-32bit
sudo xbps-install dkms
```

amd:
```
sudo xbps-install xf86-video-amdgpu linux-firmware-amd
sudo xbps-install mesa-vaapi mesa-vdpau mesa-vulkan-radeon vulkan-loader
sudo xbps-install mesa-vaapi-32bit mesa-vdpau-32bit mesa-vulkan-radeon-32bit vulkan-loader-32bit
sudo xbps-install dkms
```

# Initframs

Add needed kernel modules to your initramfs build system

### Mkinitcpio /etc/mkinitcpio.conf
```
MODULES=(nvidia nvidia_modeset nvidia_uvm nvidia_drm ... amdgpu radeon ... i915)
```

Then:
```
sudo mkinitcpio -p linux
```

### Dracut /etc/dracut.conf
```
add_drivers+=" nvidia nvidia_modeset nvidia_uvm nvidia_drm ... amdgpu radeon ... i915 "
```

Then:
```
sudo dracut --force --kver <x.x.xx_x>
sudo xbps-reconfigure -f linux<x.x>
```

# Boot

Set the necessary kernel settings in your bootloader

### Grub /etc/default/grub
```
GRUB_CMDLINE_LINUX_DEFAULT="nvidia-drm.modeset=1 ... amdgpu.modeset=1 ... i915.modeset=1"
```

Then:
```
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### UEFI /boot/loader/entries/arch.conf
```
options root=/dev/sdaX rw nvidia-drm.modeset=1 ... amdgpu.modeset=1 ... i915.modeset=1
```

Then: rebuild initframs

# Setting kernel module options

/etc/modprobe.d/module_name.conf
```
options module_name parameter_name=parameter_value
```

For example, to disable open source nvidia driver:
/etc/modprobe.d/blacklist-nvidia-nouveau.conf
```
blacklist nouveau
options nouveau modeset=0
```

# Disable intel, use nvidia only

Add the following commands to your xinitrc
```
xrandr --setprovideroutputsource modesetting NVIDIA-0
xrandr --auto
```

If you are using login managers copy this lines to:

### GDM /usr/share/grm/greeter/autostart/optimus.desktop
```
[Desktop Entry]
Type=Application
Name=Optimus
Exec=sh -c "xrandr --setprovideroutputsource modesetting NVIDIA-0; xrandr --auto"
NoDisplay=true
X-GNOME-Autostart-Phase=DisplayServer
```

### KDM /usr/share/config/kdm/Xsetup

### LightDM /etc/lightdm/display_setup.sh

Make it executable
```
chmod +x /etc/lightdm/display_setup.sh
```

Add line to /etc/lightdm/lightdm.conf
```
[Seat:*]
display-setup-script=/etc/lightdm/display_setup.sh
```

### SDDM /usr/share/sddm/scripts/Xsetup
