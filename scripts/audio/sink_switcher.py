import re
import time

import log
import pactl_interface

from .stream_switcher import StreamSwitcher


# tested with pactl version 13.99.1, 14.2

class SinkSwitcher(StreamSwitcher):
    def __init__(self, config):
        super().__init__(config, StreamSwitcher.StreamType.sink)

    def get_vr_stream_regex(self):
        return self.config.audio_vr_sink_regex()

    def get_normal_stream_regex(self):
        return self.config.audio_normal_sink_regex()

    def get_all_streams(self):
        return pactl_interface.Sink.get_all_sinks(self)

    def get_all_stream_connections(self):
        return pactl_interface.SinkInput.get_all_sink_inputs(self)

    def switch_to_stream(self, stream, device_type):
        if self.config.audio_set_card_port():
            port = self.get_port(device_type)

            if port is not None:
                port.card.set_profile(self.config, port.profiles[0])
            else:
                stream.set_suspend_state(self.config, True)
                time.sleep(self.config.audio_card_rescan_pause_time())
                # Causes a rescan of connected ports, only works if time passes between suspend and resume
                stream.set_suspend_state(self.config, False)

        self.set_stream_for_all_stream_connections(stream)

    def get_port(self, device_type):
        if device_type == "vr":
            card_port_product_name_regex = self.config.audio_card_port_vr_product_name_regex()
        elif device_type == "normal":
            card_port_product_name_regex = self.config.audio_card_port_normal_product_name_regex()
        else:
            raise NotImplementedError()

        if card_port_product_name_regex is None:
            log.d(
                "Skipping port selection for {device_type} device because card_port_{device_type}_product_name_regex is not set.".format(
                    device_type=device_type))
            return None

        cards = pactl_interface.Card.get_all_cards()
        for card in cards:
            for port in card.ports:
                if port.product_name is not None:
                    if re.match(card_port_product_name_regex, port.product_name):
                        return port

        debug_output = ''
        for card in cards:
            debug_output += card.name + '\n'
            for port in card.ports:
                debug_output += '    {}\n'.format(port.product_name if port.product_name is not None else '-')
        log.w('Failed to find any port on any card matching "{}". Name of the product at every port:\n{}'.format(
            card_port_product_name_regex, debug_output
        ))

        return None
