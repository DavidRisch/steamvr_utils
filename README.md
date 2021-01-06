# SteamVR Utils for Linux

This project contains scripts to improve the functionally of SteamVR on Linux:
- Turning Base Stations on/off (via Bluetooth)
- Changing the audio output of games to the headset and back to the normal audio device

A deamon can start automatically with SteamVR (via launch options), once SteamVr is closed the Base Stations are turned off again. 
Alternatively the scripts can be executed manually.
  
Currently, this is known to work with a Valve Index and V2 Base Stations. Other headsets and V1 Base Stations might work.
For the basestation component a bluetooth device capable of btle (Bluetooth Low Energy) is required.

This project is not affiliated with SteamVR, Steam or Valve.

## Install
Download:
```bash
git clone https://github.com/DavidRisch/steamvr_utils.git
```
Install dependencies (the last command is required for bluepy to run without root privileges):
```bash
sudo apt install pip3 libglib2.0-dev
sudo pip3 install bluepy
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.?/dist-packages/bluepy/bluepy-helper
```
Get launch options to configure SteamVr with and create desktop shortcuts:
```bash
./scripts/install.py
```

## Usage

#### Start daemon automatically when SteamVr starts:

Follow the instruction returned by `./scripts/install.py`.

#### Start deamon manually:
```bash
./scripts/steamvr_utils.py deamon
```
#### Turn Base Stations on and switch audio to the headset:
```bash
./scripts/steamvr_utils.py on
```

#### Turn Base Stations off and switch audi to the normal device:
```bash
./scripts/steamvr_utils.py off
```

## Configuration
First copy the default config file:
```bash
cp ./config/config_template.yaml ./config/config.yaml
```
If you chose a name other than `config.yaml` you will have to specify its location (`--config` argument).

The default config file contains explanations on each available field.


## Acknowledgments
- Part of `scripts/basestaion_power.py` is based on [a gist by waylonflinn](https://gist.github.com/waylonflinn/d525e08674ec3abb5c98cd41d1fd2f24).
- Part of `scripts/install.py` is based on [a reddit post by Brunfunstudios](https://np.reddit.com/r/virtualreality_linux/comments/g02bi5/automatically_turn_on_and_off_base_stations_when/).
