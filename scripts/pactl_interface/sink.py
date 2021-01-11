import log

from . import utlis


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
        return_code, stdout, stderr = utlis.run(arguments)

        if return_code != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), stderr))

    @classmethod
    def get_all_sinks(cls, audio_switcher):
        arguments = ['pactl', 'list', 'short', 'sinks']
        return_code, stdout, stderr = utlis.run(arguments)

        if audio_switcher.last_pactl_sinks is None:
            log.d('\'{}\':\n{}'.format(" ".join(arguments), stdout))
        audio_switcher.last_pactl_sinks = stdout

        sinks_lines = stdout.split('\n')[:-1]

        sinks = [cls(line) for line in sinks_lines]
        return sinks
