from .stream_connection import StreamConnection


class SinkInput(StreamConnection):
    def __init__(self, line):
        super().__init__(line)

    @classmethod
    def get_all_sink_inputs(cls, output_logger=None):
        return StreamConnection._get_all('sink-inputs', cls, output_logger)
