import log

from . import utlis


class SinkInput:
    def __init__(self, line):
        self.id = int(line.split('\t')[0])
        self.client_id = int(line.split('\t')[2])
        self.client_name = None

    @classmethod
    def get_all_sink_inputs(cls, audio_switcher=None):
        arguments = ['pactl', 'list', 'short', 'sink-inputs']
        return_code, stdout, stderr = utlis.run(arguments)

        if audio_switcher is not None:
            if audio_switcher.last_pactl_sink_inputs is None:
                log.d('\'{}\':\n{}'.format(" ".join(arguments), stdout))
            audio_switcher.last_pactl_sink_inputs = stdout

        sink_inputs_lines = stdout.split('\n')[:-1]

        sink_inputs = [cls(line) for line in sink_inputs_lines]
        return sink_inputs
