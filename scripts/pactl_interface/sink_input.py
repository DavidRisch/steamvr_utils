from . import utlis
from .stream_connection import StreamConnection


class SinkInput(StreamConnection):
    def __init__(self, line):
        super().__init__(line)

    @classmethod
    def get_all_sink_inputs(cls, output_logger=None):
        arguments = ['pactl', 'list', 'short', 'sink-inputs']
        return_code, stdout, stderr = utlis.run(arguments)

        if output_logger is not None:
            output_logger.add_output(arguments, stdout, print_first=True)

        sink_inputs_lines = stdout.split('\n')[:-1]

        sink_inputs = [cls(line) for line in sink_inputs_lines]
        return sink_inputs
