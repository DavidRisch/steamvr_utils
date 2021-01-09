#!/usr/bin/python3

import datetime
import os

import yaml


class Config:
    def __init__(self, config_path=None, dry_run_overwrite=False):
        self.dry_run_overwrite = dry_run_overwrite  # force a dry_run (value in config file is ignored)

        if config_path is None:
            config_directory = os.path.join(os.path.dirname(__file__), '..', 'config')
            config_path = os.path.join(config_directory, 'config.yaml')

            if not os.path.isfile(config_path):
                config_path = os.path.join(config_directory, 'config_template.yaml')

        if not os.path.isfile(config_path):
            raise RuntimeError('Config file not found: {}'.format(config_path))

        with open(config_path, 'r') as config_file:
            self.data = yaml.load(config_file, Loader=yaml.Loader)

    def log_path(self):
        if 'log' in self.data and 'enabled' in self.data['log'] and not self.data['log']['enabled']:
            return None

        if 'log' in self.data and 'path' in self.data['log']:
            log_directory = self.data['log']['path']
        else:
            log_directory = os.path.join(os.path.dirname(__file__), '..', 'log')

        if not os.path.isdir(log_directory):
            print('creating missing log directory: {}'.format(log_directory))
            os.mkdir(log_directory)

        file_name = '{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        log_path = os.path.join(log_directory, file_name)
        return log_path

    def basestation_enabled(self):
        if 'basestation' in self.data and 'enabled' in self.data['basestation']:
            return bool(self.data['basestation']['enabled'])

        return False

    def basestation_attempt_count_scan(self):
        if 'basestation' in self.data and 'attempt_count_scan' in self.data['basestation']:
            return int(self.data['basestation']['attempt_count_scan'])

        return 5

    def basestation_attempt_count_set(self):
        if 'basestation' in self.data and 'attempt_count_set' in self.data['basestation']:
            return int(self.data['basestation']['attempt_count_set'])

        return 5

    def audio_enabled(self):
        if 'audio' in self.data and 'enabled' in self.data['audio']:
            return bool(self.data['audio']['enabled'])

        return False

    def audio_vr_sink_regex(self):
        if 'audio' in self.data and 'vr_sink_regex' in self.data['audio']:
            return self.data['audio']['vr_sink_regex']

        return '.*hdmi.'

    def audio_normal_sink_regex(self):
        if 'audio' in self.data and 'normal_sink_regex' in self.data['audio']:
            return self.data['audio']['normal_sink_regex']

        return None

    def audio_excluded_clients_regexes(self):
        if 'audio' in self.data and 'excluded_clients_regexes' in self.data['audio']:
            return list(self.data['audio']['excluded_clients_regexes'])

        return []

    def audio_set_card_port(self):
        if 'audio' in self.data and 'set_card_port' in self.data['audio']:
            return bool(self.data['audio']['set_card_port'])

        return True

    def audio_card_port_product_name_regex(self):
        if 'audio' in self.data and 'card_port_product_name_regex' in self.data['audio']:
            return self.data['audio']['card_port_product_name_regex']

        return '(Index HMD)|(VIVE)'

    def audio_card_rescan_pause_time(self):
        if 'audio' in self.data and 'card_rescan_pause_time' in self.data['audio']:
            return float(self.data['audio']['card_rescan_pause_time'])

        return 10.0

    def daemon_watch_process_name(self):
        if 'daemon' in self.data and 'watch_process_name' in self.data['daemon']:
            return self.data['daemon']['watch_process_name']

        return 'vrcompositor'

    def daemon_wait_after_quit(self):
        if 'daemon' in self.data and 'wait_after_quit' in self.data['daemon']:
            return self.data['daemon']['wait_after_quit']

        return 40

    def dry_run(self):
        if self.dry_run_overwrite:
            return True

        if 'dry_run' in self.data:
            return bool(self.data['dry_run'])

        return False


if __name__ == '__main__':
    c = Config()
    print(c.log_path())
