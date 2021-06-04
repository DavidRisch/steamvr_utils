from . import utlis


class StreamConnection:
    def __init__(self, line):
        self.id = int(line.split('\t')[0])
        client_id_str = line.split('\t')[2]

        if client_id_str == "-":
            self.client_id = None
        else:
            self.client_id = int(client_id_str)

        self.client_name = None

    @staticmethod
    def _get_all(type_name, python_class, output_logger=None):
        assert type_name in ['sink-inputs', 'source-outputs']

        arguments = ['pactl', 'list', 'short', type_name]
        return_code, stdout, stderr = utlis.run(arguments, assert_success=True)

        if output_logger is not None:
            output_logger.add_output(arguments, stdout, print_first=True)

        stream_connections_lines = stdout.split('\n')[:-1]

        stream_connections = [python_class(line) for line in stream_connections_lines]
        return stream_connections
