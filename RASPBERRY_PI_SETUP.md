# Raspberry Pi 4 Kiosk Setup for Lucas' Game

This guide will help you set up a Raspberry Pi 4 that boots directly into Lucas' Game.

## Two Setup Methods

### Method 1: Pre-configured Image (Recommended)
Create one master SD card, then clone it for all other Pis. **No internet required after initial setup.**

### Method 2: Custom Image Building (Advanced)
Build a complete custom image on your Mac that's ready to boot. **No internet ever required.**

---

## Method 1: Pre-configured Image (Recommended)

This approach requires internet access for the initial setup, but creates a reusable image.

## Hardware Requirements

- Raspberry Pi 4 (2GB+ RAM recommended)
- MicroSD card (16GB+ recommended)
- HDMI display
- USB keyboard
- Power supply
- Optional: USB speakers for audio

## Step 1: Prepare the SD Card

1. Download **Raspberry Pi OS Lite (64-bit)** from https://www.raspberrypi.com/software/
   - Use the "Lite" version (no desktop) for better performance
   
2. Use Balena Etcher to write the image to your microSD card

3. After writing, remount the SD card and create a file named `ssh` (no extension) in the boot partition to enable SSH:
   ```bash
   touch /Volumes/bootfs/ssh
   ```

4. Optionally, set up WiFi by creating `wpa_supplicant.conf` in the boot partition:
   ```
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1
   
   network={
       ssid="YOUR_PRIVATE_WIFI_NAME"
       psk="YOUR_WIFI_PASSWORD"
   }
   ```
   **Note:** Use your private WiFi network. The Pi doesn't need internet access, just local network connectivity for SSH.

## Alternative: Create a WiFi Access Point (Optional)

If you want the Pi to create its own WiFi network (so you can connect directly without a router):

1. After initial setup via Ethernet, install required packages:
   ```bash
   sudo apt install hostapd dnsmasq
   ```

2. Configure the access point (detailed instructions in the "WiFi Access Point Setup" section below)

## Step 2: Initial Boot and Configuration

1. Insert the SD card into the Raspberry Pi and power it on

2. Find the Pi's IP address (check your router or use `ping raspberrypi.local`)

3. SSH into the Pi:
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry
   ```

4. Run the initial configuration:
   ```bash
   sudo raspi-config
   ```
   - Change password
   - Set locale/timezone
   - Expand filesystem
   - Enable auto-login to console (System Options > Boot / Auto Login > Console Autologin)

5. Update the system:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

## Step 3: Transfer and Set Up the Game

1. On your Mac, from the lucas_game directory, copy the setup script to the Pi:
   ```bash
   scp pi_setup.sh pi@raspberrypi.local:~/
   ```

2. Copy the game files:
   ```bash
   scp -r random_color_screen.py requirements.txt pi@raspberrypi.local:~/lucas_game/
   ```

3. SSH back into the Pi and run the setup script:
   ```bash
   ssh pi@raspberrypi.local
   chmod +x pi_setup.sh
   ./pi_setup.sh
   ```

## Step 4: Configure Auto-start

The setup script will configure the game to start automatically on boot. The Pi will:

1. Boot to console
2. Auto-login as the `pi` user
3. Automatically start Lucas' Game in fullscreen
4. Restart the game if it exits (unless ESC is pressed)

## Manual Configuration (if needed)

If you need to manually configure auto-start:

1. Edit the bash profile:
   ```bash
   nano ~/.bashrc
   ```

2. Add at the end:
   ```bash
   # Auto-start Lucas' Game on console login
   if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
       cd ~/lucas_game
       source venv/bin/activate
       python random_color_screen.py
   fi
   ```

## Troubleshooting

### No display output
- Make sure HDMI cable is connected before powering on
- Try adding to `/boot/firmware/config.txt`:
  ```
  hdmi_force_hotplug=1
  hdmi_drive=2
  ```

### No sound
- Check audio output:
  ```bash
  sudo raspi-config
  # System Options > Audio > Select audio device
  ```
- Test sound:
  ```bash
  speaker-test -t wav -c 2
  ```

### Game doesn't start automatically
- Check logs:
  ```bash
  journalctl -xe
  ```
- Test manually:
  ```bash
  cd ~/lucas_game
  source venv/bin/activate
  python random_color_screen.py
  ```

### Need to exit to shell
- Press ESC to exit the game
- To prevent auto-restart, comment out the auto-start line in `~/.bashrc`

## Accessing the Pi After Setup

1. SSH from another computer:
   ```bash
   ssh pi@raspberrypi.local
   ```

2. Or connect a keyboard and press ESC to exit the game

## Updating the Game

1. SSH into the Pi
2. Stop the game (ESC or Ctrl+C)
3. Update files:
   ```bash
   cd ~/lucas_game
   source venv/bin/activate
   git pull  # if using git
   # or copy new files via scp
   ```
4. Reboot or restart the game

## Performance Tips

1. Overclock the Pi for better performance (optional):
   ```bash
   sudo raspi-config
   # Performance Options > Overclock
   ```

2. Reduce GPU memory if not needed:
   ```bash
   sudo raspi-config
   # Performance Options > GPU Memory > 16
   ```

## Creating a Backup Image

Once everything is working, create a backup of your SD card:

```bash
# On Mac
# 1. Insert the SD card and find its device
diskutil list

# 2. Unmount (but don't eject) the SD card
# Replace diskX with your SD card device (e.g., disk4)
diskutil unmountDisk /dev/diskX

# 3. Create the image (this takes 10-30 minutes)
sudo dd if=/dev/rdiskX of=~/lucas-game-pi.img bs=4m

# 4. Compress the image to save space (optional)
gzip ~/lucas-game-pi.img
```

### Cloning the Image to New SD Cards

To create additional SD cards with the same setup:

```bash
# 1. Decompress if needed
gunzip ~/lucas-game-pi.img.gz

# 2. Write to new SD card
diskutil unmountDisk /dev/diskX
sudo dd if=~/lucas-game-pi.img of=/dev/rdiskX bs=4m

# 3. Eject
diskutil eject /dev/diskX
```

Now you can create unlimited copies without internet access or manual setup!

---

## Method 2: Custom Image Building (Advanced)

Build a completely pre-configured image on your Mac. **No internet required on the Pi, ever.**

### Prerequisites

- Docker Desktop for Mac (or Podman)
- 20GB+ free disk space
- 2-4 hours for first build

### Option A: Using pi-gen (Raspberry Pi's Official Tool)

1. Clone the pi-gen repository:
   ```bash
   git clone https://github.com/RPi-Distro/pi-gen.git
   cd pi-gen
   ```

2. Create a custom stage:
   ```bash
   mkdir -p stage-lucas/00-lucas-game/files
   ```

3. Copy your game files:
   ```bash
   cp -r ~/path/to/lucas_game stage-lucas/00-lucas-game/files/home/pi/
   ```

4. Create installation script `stage-lucas/00-lucas-game/01-run.sh`:
   ```bash
   #!/bin/bash -e
   
   # Install system dependencies
   on_chroot << EOF
   apt-get update
   apt-get install -y python3-pip python3-venv libsdl2-2.0-0 \
       libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 \
       libportaudio2
   
   # Set up as pi user
   cd /home/pi/lucas_game
   sudo -u pi python3 -m venv venv
   sudo -u pi venv/bin/pip install numpy sounddevice
   sudo -u pi venv/bin/pip install pygame --no-binary :all:
   
   # Configure auto-start
   echo '
   if [ -z "\$DISPLAY" ] && [ "\$(tty)" = "/dev/tty1" ]; then
       cd ~/lucas_game
       source venv/bin/activate
       python random_color_screen.py
   fi' >> /home/pi/.bashrc
   
   # Enable auto-login
   systemctl set-default multi-user.target
   ln -fs /etc/systemd/system/autologin@.service \
       /etc/systemd/system/getty.target.wants/getty@tty1.service
   EOF
   ```

5. Configure the build in `config`:
   ```bash
   IMG_NAME='lucas-game'
   ENABLE_SSH=1
   STAGE_LIST="stage0 stage1 stage2 stage-lucas"
   ```

6. Build the image:
   ```bash
   sudo ./build-docker.sh
   ```

7. Find your image in `deploy/`:
   ```bash
   ls -lh deploy/*.img
   ```

### Option B: Using Packer (Simpler Alternative)

1. Install Packer ARM plugin:
   ```bash
   brew install packer
   packer plugins install github.com/mkaczanowski/packer-plugin-arm
   ```

2. Create `lucas-game.pkr.hcl`:
   ```hcl
   source "arm" "lucas-game" {
     file_urls             = ["https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64-lite.img.xz"]
     file_checksum_url     = "https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-11-19/2024-11-19-raspios-bookworm-arm64-lite.img.xz.sha256"
     file_checksum_type    = "sha256"
     file_target_extension = "xz"
     file_unarchive_cmd    = ["xz", "-d", "$ARCHIVE_PATH"]
     image_build_method    = "resize"
     image_path            = "lucas-game.img"
     image_size            = "8G"
     image_type            = "dos"
     image_partitions {
       name         = "boot"
       type         = "c"
       start_sector = "8192"
       filesystem   = "fat"
       size         = "256M"
       mountpoint   = "/boot"
     }
     image_partitions {
       name         = "root"
       type         = "83"
       start_sector = "532480"
       filesystem   = "ext4"
       size         = "0"
       mountpoint   = "/"
     }
     image_chroot_env     = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]
     qemu_binary_source_path      = "/opt/homebrew/bin/qemu-aarch64-static"
     qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
   }
   
   build {
     sources = ["source.arm.lucas-game"]
     
     provisioner "shell" {
       inline = [
         "apt-get update",
         "apt-get upgrade -y",
         "apt-get install -y python3-pip python3-venv libsdl2-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 libportaudio2"
       ]
     }
     
     provisioner "file" {
       source      = "lucas_game"
       destination = "/home/pi/"
     }
     
     provisioner "shell" {
       inline = [
         "cd /home/pi/lucas_game",
         "sudo -u pi python3 -m venv venv",
         "sudo -u pi venv/bin/pip install numpy sounddevice",
         "sudo -u pi venv/bin/pip install pygame --no-binary :all:",
         "echo 'if [ -z \"$DISPLAY\" ] && [ \"$(tty)\" = \"/dev/tty1\" ]; then cd ~/lucas_game; source venv/bin/activate; python random_color_screen.py; fi' >> /home/pi/.bashrc",
         "systemctl enable getty@tty1",
         "mkdir -p /etc/systemd/system/getty@tty1.service.d",
         "echo -e '[Service]\\nExecStart=\\nExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM' > /etc/systemd/system/getty@tty1.service.d/autologin.conf"
       ]
     }
   }
   ```

3. Build:
   ```bash
   packer build lucas-game.pkr.hcl
   ```

### Option C: Manual Image Modification (Most Control)

1. Download Raspberry Pi OS Lite image

2. Mount and modify using Docker:
   ```bash
   # Pull image manipulation tool
   docker pull mkaczanowski/packer-builder-arm
   
   # Mount the image
   docker run --rm --privileged -v /dev:/dev -v $(pwd):/build \
       mkaczanowski/packer-builder-arm \
       bash -c "kpartx -av raspios.img && mount /dev/mapper/loop0p2 /mnt"
   ```

3. Chroot and install:
   ```bash
   docker exec -it <container_id> chroot /mnt /bin/bash
   # Run installation commands
   ```

### Comparison of Methods

| Method | Complexity | Build Time | Flexibility | Internet Required |
|--------|-----------|------------|-------------|-------------------|
| Pre-configured Image (Method 1) | Low | 30 min + 30 min clone | Medium | Once (initial) |
| pi-gen | High | 2-4 hours | High | No |
| Packer | Medium | 1-2 hours | Medium | No |
| Manual | Very High | Variable | Very High | No |

**Recommendation:** Start with Method 1 (pre-configured image). It's the simplest and most reliable. Only use Method 2 if you need to deploy many Pis and want a fully automated build process.

---

## WiFi Access Point Setup (Optional)

This allows the Pi to create its own WiFi network that you can connect to directly.

### 1. Install Required Packages

```bash
sudo apt install hostapd dnsmasq
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

### 2. Configure Static IP for wlan0

Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

### 3. Configure DHCP Server (dnsmasq)

Backup and create new config:
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

Add:
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=local
address=/raspberrypi.local/192.168.4.1
```

### 4. Configure Access Point (hostapd)

Create config file:
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add:
```
interface=wlan0
driver=nl80211
ssid=LucasGame
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=lucasgame2025
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

**Change `wpa_passphrase` to your desired password (minimum 8 characters).**

Point hostapd to the config:
```bash
sudo nano /etc/default/hostapd
```

Change:
```
#DAEMON_CONF=""
```
To:
```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

### 5. Enable and Start Services

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo reboot
```

### 6. Connect to Your Pi's WiFi

After reboot:
1. Look for WiFi network named "LucasGame"
2. Connect using the password you set
3. SSH to the Pi:
   ```bash
   ssh pi@192.168.4.1
   ```

### Switching Back to Client Mode

To connect to a regular WiFi network instead:

1. Stop and disable the access point:
   ```bash
   sudo systemctl stop hostapd
   sudo systemctl stop dnsmasq
   sudo systemctl disable hostapd
   sudo systemctl disable dnsmasq
   ```

2. Remove static IP from `/etc/dhcpcd.conf`

3. Configure WiFi client in `/etc/wpa_supplicant/wpa_supplicant.conf`:
   ```
   network={
       ssid="YOUR_WIFI_NAME"
       psk="YOUR_WIFI_PASSWORD"
   }
   ```

4. Reboot:
   ```bash
   sudo reboot
   ```
