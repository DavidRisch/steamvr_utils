#!/usr/bin/python3

import re
import subprocess
import time

import log


# tested with pactl version 13.99.1

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
            if self.failure_count > 20:
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

        sinks = self.get_all_sinks()

        if normal_sink_regex is None:
            running_sink = ([sink for sink in sinks if sink.is_running] + [None])[0]
            if running_sink is None:
                raise RuntimeError('No sink is currently running.')
            self.normal_sink = running_sink
        else:
            self.normal_sink = self.find_matching_sink(sinks, normal_sink_regex, "normal")
        log.d('normal sink: {}'.format(self.normal_sink.name))

        self.vr_sink = self.find_matching_sink(sinks, vr_sink_regex, "vr")
        log.d('vr sink: {}'.format(self.vr_sink.name))

    @staticmethod
    def find_matching_sink(sinks, regex, name):
        vr_matches = [
            sink for sink in sinks if re.match(regex, sink.name)
        ]
        if len(vr_matches) == 1:
            return vr_matches[0]

        elif len(vr_matches) == 0:
            log.e('No {} audio sink for the was found. Tried to find a match for: {}'.format(name, regex))
        else:
            raise RuntimeError(
                'Multiple matches for the {} audio sink found. Tried to find a match for: {}'.format(name, regex))

    def switch_to_vr(self):
        self.set_sink(self.vr_sink)

    def switch_to_normal(self):
        self.set_sink(self.normal_sink)

    def set_sink(self, sink):
        # self.set_default_sink(sink)
        self.set_sink_for_all_sink_inputs(sink)

    def log_state(self):
        log.d("last_pactl_sinks:\n{}".format(self.last_pactl_sinks))
        log.d("last_pactl_sink_inputs:\n{}".format(self.last_pactl_sink_inputs))
        log.d("last_pactl_clients:\n{}".format(self.last_pactl_clients))

    def set_default_sink(self, sink):
        if self.config.dry_run():
            log.w('Skipping because of dry run')
            return

        arguments = ['pactl', 'set-default-sink', sink.name]
        process = subprocess.run(arguments, stderr=subprocess.PIPE)

        if process.returncode != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), process.stderr.decode()))
            self.log_state()

    def set_sink_for_all_sink_inputs(self, sink):
        sink_inputs = self.get_all_sink_inputs()
        self.get_client_names(sink_inputs)
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
            process = subprocess.run(arguments, stderr=subprocess.PIPE)

            if process.returncode != 0:
                if failure is None:
                    failure = self.Failure(sink_input.id)
                    self.failed_sink_inputs.append(failure)
                else:
                    failure.add_attempt()

                log.e('\'{}\' (client_name: {}) failed (count: {}), stderr:\n{}'.format(
                    " ".join(arguments),
                    sink_input.client_name,
                    failure.failure_count,
                    process.stderr.decode()))
                self.log_state()

    def get_all_sinks(self):
        class Sink:
            def __init__(self, line):
                self.name = line.split('\t')[1]
                self.is_running = line.split('\t')[4] == 'RUNNING'

        arguments = ['pactl', 'list', 'short', 'sinks']
        process = subprocess.run(arguments, stdout=subprocess.PIPE)

        if self.last_pactl_sinks is None:
            log.d('\'{}\':\n{}'.format(" ".join(arguments), process.stdout.decode()))
        self.last_pactl_sinks = process.stdout.decode()

        sinks_lines = process.stdout.decode().split('\n')[:-1]

        sinks = [Sink(line) for line in sinks_lines]
        return sinks

    def get_all_sink_inputs(self):
        class SinkInput:
            def __init__(self, line):
                self.id = int(line.split('\t')[0])
                self.client_id = int(line.split('\t')[2])
                self.client_name = None

        arguments = ['pactl', 'list', 'short', 'sink-inputs']
        process = subprocess.run(arguments, stdout=subprocess.PIPE)

        if self.last_pactl_sink_inputs is None:
            log.d('\'{}\':\n{}'.format(" ".join(arguments), process.stdout.decode()))
        self.last_pactl_sink_inputs = process.stdout.decode()

        sink_inputs_lines = process.stdout.decode().split('\n')[:-1]

        sink_inputs = [SinkInput(line) for line in sink_inputs_lines]
        return sink_inputs

    def get_client_names(self, sink_inputs):
        class Client:
            def __init__(self, line):
                self.client_id = int(line.split('\t')[0])
                self.client_name = line.split('\t')[2]

        arguments = ['pactl', 'list', 'short', 'clients']
        process = subprocess.run(arguments, stdout=subprocess.PIPE)

        if self.last_pactl_clients is None:
            log.d('\'{}\':\n{}'.format(" ".join(arguments), process.stdout.decode()))
        self.last_pactl_clients = process.stdout.decode()

        client_lines = process.stdout.decode().split('\n')[:-1]

        clients = [Client(line) for line in client_lines]

        for sink_input in sink_inputs:
            matching_client = ([client for client in clients if client.client_id == sink_input.client_id] + [None])[0]
            if matching_client is not None:
                sink_input.client_name = matching_client.client_name

    def filter_by_client_name(self, sink_inputs):
        excluded_clients_regexes = self.config.excluded_clients_regexes()

        new_sink_inputs = []

        for sink_input in sink_inputs:
            is_excluded = False
            for excluded_client_regex in excluded_clients_regexes:
                if re.match(excluded_client_regex, sink_input.client_name):
                    is_excluded = True
                    break

            if not is_excluded:
                new_sink_inputs.append(sink_input)

        return new_sink_inputs
