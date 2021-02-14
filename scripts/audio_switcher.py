#!/usr/bin/python3

import re
import time

import log
import pactl_interface

# tested with pactl version 14.2

class AudioSwitcher:
    class Failure:
        def __init__(self, sink_input_id):
            self.sink_input_id = sink_input_id
            self.failure_count = 1
            self.last_failure = time.time()

        def add_attempt(self):
            self.failure_count += 1
            self.last_failure = time.time()

        def try_again(self):
            if self.failure_count > 10:
                return False

            if self.last_failure + 0.5 > time.time():
                return False

            return True

    def __init__(self, config):
        self.config = config

        self.last_pactl_sinks = None
        self.last_pactl_sink_inputs = None
        self.last_pactl_clients = None

        self.failed_sink_inputs = []  # sink_inputs for which move-sink-input failed (Failure class)

        vr_sink_regex = config.audio_vr_sink_regex()
        normal_sink_regex = config.audio_normal_sink_regex()

        if normal_sink_regex == '':
            normal_sink_regex = None

        sinks = pactl_interface.Sink.get_all_sinks(self)

        if normal_sink_regex is None:
            default_sink_name = self.get_default_sink_name()
            default_sink = ([sink for sink in sinks if sink.name == default_sink_name] + [None])[0]
            if default_sink is None:
                raise RuntimeError('Default sink was not found.')
            self.normal_sink = default_sink
        else:
            self.normal_sink = self.find_matching_sink(sinks, normal_sink_regex, "normal")
        log.d('normal sink: {}'.format(self.normal_sink.name))

        self.vr_sink = self.find_matching_sink(sinks, vr_sink_regex, "vr")
        log.d('vr sink: {}'.format(self.vr_sink.name))

        self.port = None

    @staticmethod
    def find_matching_sink(sinks, regex, name):
        vr_matches = [
            sink for sink in sinks if re.match(regex, sink.name)
        ]
        if len(vr_matches) == 1:
            return vr_matches[0]

        elif len(vr_matches) == 0:
            log.e('No {} audio sink for the normal device was found. Tried to find a match for: {}'.format(name, regex))
        else:
            raise RuntimeError(
                'Multiple matches for the {} audio sink found. Tried to find a match for: {}'.format(name, regex))

    def switch_to_vr(self):
        old_vr_sink = self.vr_sink
        sinks = pactl_interface.Sink.get_all_sinks(self)
        self.vr_sink = self.find_matching_sink(sinks, self.config.audio_vr_sink_regex(), "vr")
        if self.vr_sink.name != old_vr_sink.name:
            log.d('New vr sink: {}'.format(self.vr_sink.name))

        if self.config.audio_set_card_port():
            last_port = self.port
            self.port = self.get_vr_port()
            if last_port != self.port:
                log.d('New port: {}'.format(self.port))

            if self.port is not None:
                self.port.card.set_profile(self.config, self.port.profiles[0])
            else:
                self.vr_sink.set_suspend_state(self.config, True)
                time.sleep(self.config.audio_card_rescan_pause_time())
                # Causes a rescan of connected ports, only works if time passes between suspend and resume
                self.vr_sink.set_suspend_state(self.config, False)

        self.set_sink_for_all_sink_inputs(self.vr_sink)

    def switch_to_normal(self):
        if self.config.audio_set_card_port():
            self.port = self.get_normal_port()

            if self.port is not None:
                self.port.card.set_profile(self.config, self.port.profiles[0])
            else:
                self.normal_sink.set_suspend_state(self.config, True)
                time.sleep(self.config.audio_card_rescan_pause_time())
                # Causes a rescan of connected ports, only works if time passes between suspend and resume
                self.normal_sink.set_suspend_state(self.config, False)

        self.set_sink_for_all_sink_inputs(self.normal_sink)

    def log_state(self):
        log.d('last_pactl_sinks:\n{}'.format(self.last_pactl_sinks))
        log.d('last_pactl_sink_inputs:\n{}'.format(self.last_pactl_sink_inputs))
        log.d('last_pactl_clients:\n{}'.format(self.last_pactl_clients))

    def set_sink_for_all_sink_inputs(self, sink):
        # verify sink name exists before proceeding
        sinks = pactl_interface.Sink.get_all_sinks(self)
        found = False
        for s in sinks:
            if s.name == sink.name:
                found = True

        if not found:
            log.d('Skipping move-sink-input since the sink name does not exist')
            return

        sink_inputs = pactl_interface.SinkInput.get_all_sink_inputs(self)
        pactl_interface.Client.get_client_names(sink_inputs)
        sink_inputs = self.filter_by_client_name(sink_inputs)

        if self.config.dry_run():
            log.w('Skipping because of dry run')
            return

        for sink_input in sink_inputs:
            failure = \
                ([failure for failure in self.failed_sink_inputs if failure.sink_input_id == sink_input.id] + [None])[0]
            if failure is not None and not failure.try_again():
                continue

            arguments = ['pactl', 'move-sink-input', str(sink_input.id), sink.name]
            return_code, stdout, stderr = pactl_interface.utlis.run(arguments)

            if return_code != 0:
                if failure is None:
                    failure = self.Failure(sink_input.id)
                    self.failed_sink_inputs.append(failure)
                else:
                    failure.add_attempt()

                log.e('\'{}\' (client_name: {}) failed (count: {}), stderr:\n{}'.format(
                    " ".join(arguments),
                    sink_input.client_name,
                    failure.failure_count,
                    stderr))
                self.log_state()

    @staticmethod
    def get_default_sink_name():
        arguments = ['pactl', 'info']
        return_code, stdout, stderr = pactl_interface.utlis.run(arguments)

        info_lines = stdout.split('\n')[:-1]

        for line in info_lines:
            matches = re.match('^Default Sink: (.*)', line)
            if matches is not None:
                return matches.group(1)

        raise RuntimeError('Unable to determine the default sink. '
                           'Workaround: Fill out the "normal_sink_regex" field in the config file.\n\n'
                           'Output of `pactl info`:\n{}'.format(stdout))

    def get_normal_port(self):
        cards = pactl_interface.Card.get_all_cards()
        card_port_normal_product_name_regex = self.config.audio_card_port_normal_product_name_regex()
        for card in cards:
            for port in card.ports:
                if port.product_name is not None:
                    if re.match(card_port_normal_product_name_regex, port.product_name):
                        return port

        debug_output = ''
        for card in cards:
            debug_output += card.name + '\n'
            for port in card.ports:
                debug_output += '    {}\n'.format(port.product_name if port.product_name is not None else '-')
        log.w('Failed to find any port on any card matching "{}". Name of the product at every port:\n{}'.format(
            card_port_normal_product_name_regex, debug_output
        ))

        return None

    def get_vr_port(self):
        cards = pactl_interface.Card.get_all_cards()
        card_port_vr_product_name_regex = self.config.audio_card_port_vr_product_name_regex()
        for card in cards:
            for port in card.ports:
                if port.product_name is not None:
                    if re.match(card_port_vr_product_name_regex, port.product_name):
                        return port

        debug_output = ''
        for card in cards:
            debug_output += card.name + '\n'
            for port in card.ports:
                debug_output += '    {}\n'.format(port.product_name if port.product_name is not None else '-')
        log.w('Failed to find any port on any card matching "{}". Name of the product at every port:\n{}'.format(
            card_port_vr_product_name_regex, debug_output
        ))

        return None

    def filter_by_client_name(self, sink_inputs):
        excluded_clients_regexes = self.config.audio_excluded_clients_regexes()

        new_sink_inputs = []

        for sink_input in sink_inputs:
            is_excluded = False
            for excluded_client_regex in excluded_clients_regexes:
                if sink_input.client_name is not None and \
                        re.match(excluded_client_regex, sink_input.client_name):
                    is_excluded = True
                    break

            if not is_excluded:
                new_sink_inputs.append(sink_input)

        return new_sink_inputs
