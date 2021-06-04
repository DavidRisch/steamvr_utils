import pactl_interface

from .stream_switcher import StreamSwitcher


# tested with pactl version 13.99.1

class SourceSwitcher(StreamSwitcher):
    def __init__(self, config):
        super().__init__(config, StreamSwitcher.StreamType.source)

    def get_vr_stream_regex(self):
        return self.config.audio_vr_source_regex()

    def get_normal_stream_regex(self):
        return self.config.audio_normal_source_regex()

    def get_all_streams(self):
        return pactl_interface.Source.get_all_sources(self.output_logger)

    def get_all_stream_connections(self):
        return pactl_interface.SourceOutput.get_all_source_outputs(self.output_logger)

    def get_move_stream_connection_command(self):
        return 'move-source-output'

    def switch_to_stream(self, stream, device_type):
        self.set_stream_for_all_stream_connections(stream)
