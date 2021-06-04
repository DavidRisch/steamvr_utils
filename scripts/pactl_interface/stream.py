from . import utlis


class Stream:
    def __init__(self, line):
        self.name = line.split('\t')[1]

    @staticmethod
    def _get_all(type_name, python_class, output_logger=None):
        assert type_name in ['sinks', 'sources']

        arguments = ['pactl', 'list', 'short', type_name]
        return_code, stdout, stderr = utlis.run(arguments, assert_success=True)

        if output_logger is not None:
            output_logger.add_output(arguments, stdout, print_first=True)

        streams_lines = stdout.split('\n')[:-1]

        streams = [python_class(line) for line in streams_lines]
        return streams
