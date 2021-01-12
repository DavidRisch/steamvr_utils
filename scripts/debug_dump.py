#!/usr/bin/python3

import argparse

import log
import pactl_interface
from config import Config


def debug_dump():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        default=None,
                        help='Path to a config file.')
    args = parser.parse_args()

    config = Config(config_path=args.config)

    log.initialise(config)

    log.i("debug_dump start")

    log.i("config:\n{}".format(config.data))

    commands = [
        ['pactl', 'info'],
        ['pactl', 'list', 'short', 'sinks'],
        ['pactl', 'list', 'short', 'clients'],
        ['pactl', 'list', 'cards'],
    ]

    for command in commands:
        return_code, stdout, stderr = pactl_interface.utlis.run(command)

        log.i("command: {}: return_code: {}\nstdout:\n{}\nstderr:\n{}".format(
            command, return_code, stdout, stderr

        ))

    log.i("debug_dump end")


if __name__ == '__main__':
    debug_dump()
