import log

from . import utlis
from .stream import Stream


class Sink(Stream):
    def __init__(self, line):
        super().__init__(line)

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
        return_code, stdout, stderr = utlis.run(arguments, assert_success=False)

        if return_code != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), stderr))

    @classmethod
    def get_all_sinks(cls, output_logger=None):
        return Stream._get_all('sinks', cls, output_logger)
