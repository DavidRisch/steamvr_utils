#!/usr/bin/python3

import os
import pathlib


def print_launch_options(steamvr_utils_path):
    launch_options = 'python3 {steamvr_utils_path} daemon  >>/tmp/steamvr_utils.out 2>&1; %command%;'.format(
        steamvr_utils_path=steamvr_utils_path)

    print(
        'INSTRUCTIONS: Paste the following line in the launch options of SteamVR (Library | right click on SteamVR | Properties... | General | Set launch options...):\n' + launch_options)


def test_imports():
    try:
        import bluepy
    except ModuleNotFoundError:
        print('''
WARNING: 'bluepy' was not found but is required to use bluetooth to connect to Base Stations. Execute these commands to install it:
sudo apt install pip3 libglib2.0-dev
sudo pip3 install bluepy
        ''')

    # make sure all imports work
    # noinspection PyUnresolvedReferences
    import steamvr_utils


def create_desktop_file(action, steamvr_utils_path):
    command = 'python3 {} {}'.format(steamvr_utils_path, action)
    image_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'icon_{}.png'.format(action))
    image_path = os.path.realpath(image_path)

    content = '''[Desktop Entry]
Name=steamvr_utils {action}
GenericName=Hardware utility
Keywords=VR;Base Station;Light House
Exec={command}
Terminal=false
Type=Application
Icon={image_path}
'''.format(action=action, command=command, image_path=image_path)

    desktop_file_path = os.path.join(pathlib.Path.home(), '.local/share/applications/',
                                     'steamvr_utils_{}.desktop'.format(action))

    with open(desktop_file_path, "w") as desktop_file:
        desktop_file.write(content)


def main():
    steamvr_utils_path = os.path.join(os.path.dirname(__file__), 'steamvr_utils.py')
    steamvr_utils_path = os.path.realpath(steamvr_utils_path)

    print_launch_options(steamvr_utils_path)

    test_imports()

    create_desktop_file('on', steamvr_utils_path)
    create_desktop_file('off', steamvr_utils_path)


if __name__ == '__main__':
    main()
