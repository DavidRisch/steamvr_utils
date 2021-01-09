import subprocess

import log


class Sink:
    def __init__(self, line):
        self.name = line.split('\t')[1]

    def set_suspend_state(self, config, state):
        if config.dry_run():
            log.w('Skipping because of dry run')
            return

        if state:
            state = "true"
        else:
            state = "false"

        arguments = ['pactl', 'suspend-sink', self.name, state]
        log.d('set_suspend_state {}'.format(' '.join(arguments)))
        process = subprocess.run(arguments, stderr=subprocess.PIPE)

        if process.returncode != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), process.stderr.decode()))

    @classmethod
    def get_all_sinks(cls, audio_switcher):
        arguments = ['pactl', 'list', 'short', 'sinks']
        process = subprocess.run(arguments, stdout=subprocess.PIPE)

        if audio_switcher.last_pactl_sinks is None:
            log.d('\'{}\':\n{}'.format(" ".join(arguments), process.stdout.decode()))
        audio_switcher.last_pactl_sinks = process.stdout.decode()

        sinks_lines = process.stdout.decode().split('\n')[:-1]

        sinks = [cls(line) for line in sinks_lines]
        return sinks
