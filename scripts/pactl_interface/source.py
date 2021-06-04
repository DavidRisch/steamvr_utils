from .stream import Stream


class Source(Stream):
    def __init__(self, line):
        super().__init__(line)

    @classmethod
    def get_all_sources(cls, output_logger=None):
        return Stream._get_all('sources', cls, output_logger)
