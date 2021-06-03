#!/usr/bin/python3

import argparse
import enum

import basestation_interface
import log
from audio_switcher import AudioSwitcher
from config import Config
from config_helper import ConfigHelper
from steamvr_daemon import SteamvrDaemon
from version import __version__


class SteamvrUtils:
    class Action(enum.Enum):
        ON = enum.auto()
        OFF = enum.auto()
        DAEMON = enum.auto()
        CONFIG_HELP = enum.auto()

    def __init__(self, config):
        self.config = config

        self.streamvr_running = None
        self.turn_off_at = None  # time at which self.turn_of() will be executed (see --wait)

        self.basestation_power_interface = None
        self.audio_switcher = None

        if self.config.basestation_enabled():
            basestation_type = self.config.basestation_type()
            if basestation_type == 'v1':
                self.basestation_power_interface = basestation_interface.V1BasestationInterface(config)
            elif basestation_type == 'v2':
                self.basestation_power_interface = basestation_interface.V2BasestationInterface(config)
            elif basestation_type == 'cmd':
                self.basestation_power_interface = basestation_interface.CmdBasestationInterface(config)
            else:
                raise NotImplementedError()

        if self.config.audio_enabled():
            self.audio_switcher = AudioSwitcher(config)

    def action(self, action):
        if action == self.Action.ON:
            self.turn_on()
        elif action == self.Action.OFF:
            self.turn_off()
        elif action == self.Action.DAEMON:
            self.start_daemon()
        else:
            raise NotImplementedError('Action: {}'.format(action))

    def start_daemon(self):
        log.i('SteamvrUtils stating daemon:')
        SteamvrDaemon.create_daemon(self)

    def turn_off(self):
        log.i('SteamvrUtils turning off:')

        if self.basestation_power_interface is not None:
            self.basestation_power_interface.action(basestation_interface.Action.OFF)

        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_normal()

    def turn_on(self):
        log.i('SteamvrUtils turning on:')

        if self.basestation_power_interface is not None:
            self.basestation_power_interface.action(basestation_interface.Action.ON)

        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_vr()

    def turn_on_iteration(self):
        if self.audio_switcher is not None:
            self.audio_switcher.switch_to_vr()


def main():
    actions = {
        SteamvrUtils.Action.ON: ['on', '1'],
        SteamvrUtils.Action.OFF: ['off', '0'],
        SteamvrUtils.Action.DAEMON: ['daemon', 'd'],
        SteamvrUtils.Action.CONFIG_HELP: ['config-help', 'c']
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('action',
                        choices=[
                            keyword
                            for _, keywords in actions.items()
                            for keyword in keywords
                        ],
                        help='action to perform on the Base Stations')
    parser.add_argument('--dry-run',
                        help='Do not modify anything (bluetooth connections are still made, but never used to write).',
                        action='store_true')
    parser.add_argument('--config',
                        default=None,
                        help='Path to a config file.')
    parser.add_argument('--version',
                        action='version',
                        version='steamvr_utils {version}'.format(version=__version__))
    args = parser.parse_args()

    config = Config(config_path=args.config, dry_run_overwrite=args.dry_run)

    log.initialise(config)

    # noinspection PyBroadException
    try:

        selected_action = None
        for action in SteamvrUtils.Action:
            if args.action in actions[action]:
                selected_action = action

        if selected_action == SteamvrUtils.Action.CONFIG_HELP:
            config_helper = ConfigHelper(config)
            config_helper.print_help()
            return

        log.i('steamvr_utils version: {}'.format(__version__))
        log.d('dry_run: {}'.format(config.dry_run()))

        steamvr_utils = SteamvrUtils(
            config=config
        )

        steamvr_utils.action(selected_action)
    except Exception:
        log.e('', exc_info=True)
        exit(1)


if __name__ == '__main__':
    main()
