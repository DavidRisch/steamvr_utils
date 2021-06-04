from .sink_switcher import SinkSwitcher
from .source_switcher import SourceSwitcher


class AudioSwitcher:
    def __init__(self, config):
        self.sink_switcher = None
        if config.audio_change_sink():
            self.sink_switcher = SinkSwitcher(config)

        self.source_switcher = None
        if config.audio_change_source():
            self.source_switcher = SourceSwitcher(config)

    def switch_to_vr(self):
        if self.sink_switcher is not None:
            self.sink_switcher.switch_to_vr()
        if self.source_switcher is not None:
            self.source_switcher.switch_to_vr()

    def switch_to_normal(self):
        if self.sink_switcher is not None:
            self.sink_switcher.switch_to_normal()
        if self.source_switcher is not None:
            self.source_switcher.switch_to_normal()
