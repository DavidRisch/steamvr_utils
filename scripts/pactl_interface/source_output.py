from .stream_connection import StreamConnection


class SourceOutput(StreamConnection):
    def __init__(self, line):
        super().__init__(line)

    @classmethod
    def get_all_source_outputs(cls, output_logger=None):
        return StreamConnection._get_all('source-outputs', cls, output_logger)
