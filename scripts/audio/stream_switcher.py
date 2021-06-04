import enum
import re
import time

import log
import pactl_interface

from .output_logger import OutputLogger


class StreamSwitcher:
    class StreamType(enum.Enum):
        sink = 'sink'

    class Failure:
        def __init__(self, stream_connection_id):
            self.stream_connection_id = stream_connection_id
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

    def __init__(self, config, stream_type):
        self.config = config
        self.stream_type = stream_type

        self.output_logger = OutputLogger()

        self.failed_stream_connections = []  # stream_connections for which move-sink-input failed (Failure class)

        vr_stream_regex = self.get_vr_stream_regex()
        normal_stream_regex = self.get_normal_stream_regex()

        if normal_stream_regex == '':
            normal_stream_regex = None

        streams = self.get_all_streams()

        if normal_stream_regex is None:
            default_stream_name = self.get_default_stream_name()
            default_stream = ([stream for stream in streams if stream.name == default_stream_name] + [None])[0]
            if default_stream is None:
                raise RuntimeError('Default stream was not found.')
            self.normal_stream = default_stream
        else:
            self.normal_stream = self.find_matching_stream(streams, normal_stream_regex, "normal")
        log.d('normal {}: {}'.format(self.get_stream_type_name(), self.normal_stream.name))

        self.vr_stream = self.find_matching_stream(streams, vr_stream_regex, "vr")
        log.d('vr {}: {}'.format(self.get_stream_type_name(), self.vr_stream.name))

    def get_stream_type_name(self):
        return self.stream_type.value

    def get_vr_stream_regex(self):
        raise NotImplementedError()

    def get_normal_stream_regex(self):
        raise NotImplementedError()

    def get_all_streams(self):
        raise NotImplementedError()

    def get_all_stream_connections(self):
        raise NotImplementedError()

    def get_move_stream_connection_command(self):
        raise NotImplementedError()

    def find_matching_stream(self, streams, regex, name):
        matches = [
            stream for stream in streams if re.match(regex, stream.name)
        ]
        if len(matches) == 1:
            return matches[0]

        elif len(matches) == 0:
            log.e('No {} audio {} was found. Tried to find a match for: {}'.format(name, self.stream_type, regex))
        else:
            raise RuntimeError(
                'Multiple matches for the {} audio {} found. Tried to find a match for: {}'.format(name,
                                                                                                   self.stream_type,
                                                                                                   regex))

    def switch_to_stream(self, stream, device_type):
        raise NotImplementedError()

    def switch_to_vr(self):
        old_vr_stream = self.vr_stream
        streams = self.get_all_streams()
        self.vr_stream = self.find_matching_stream(streams, self.get_vr_stream_regex(), "vr")
        if self.vr_stream.name != old_vr_stream.name:
            log.d('New vr {}: {}'.format(self.get_stream_type_name(), self.vr_stream.name))

        self.switch_to_stream(self.vr_stream, "vr")

    def switch_to_normal(self):
        self.switch_to_stream(self.normal_stream, "normal")

    def set_stream_for_all_stream_connections(self, stream):
        if self.config.dry_run():
            log.w('Skipping because of dry run')
            return

        # verify stream name exists before proceeding
        streams = self.get_all_streams()
        found = False
        for s in streams:
            if s.name == stream.name:
                found = True

        if not found:
            log.w('Skipping {} since the {} name does not exist'.format(
                self.get_move_stream_connection_command(), self.get_stream_type_name()
            ))
            return

        stream_connections = self.get_all_stream_connections()
        pactl_interface.Client.get_client_names(stream_connections)
        stream_connections = self.filter_by_client_name(stream_connections)

        for stream_connection in stream_connections:
            failure = \
                ([failure for failure in self.failed_stream_connections if
                  failure.stream_connection_id == stream_connection.id] + [
                     None])[0]
            if failure is not None and not failure.try_again():
                continue

            arguments = ['pactl', self.get_move_stream_connection_command(), str(stream_connection.id), stream.name]
            log.w("move {}".format(" ".join(arguments)))
            return_code, stdout, stderr = pactl_interface.utlis.run(arguments, assert_success=False)

            if return_code != 0:
                if failure is None:
                    failure = self.Failure(stream_connection.id)
                    self.failed_stream_connections.append(failure)
                else:
                    failure.add_attempt()

                log.e('\'{}\' (client_name: {}) failed (count: {}), stderr:\n{}'.format(
                    " ".join(arguments),
                    stream_connection.client_name,
                    failure.failure_count,
                    stderr))
                self.output_logger.log_all()

    def get_default_stream_name(self):
        arguments = ['pactl', 'info']
        return_code, stdout, stderr = pactl_interface.utlis.run(arguments, assert_success=True)

        info_lines = stdout.split('\n')[:-1]

        for line in info_lines:
            if self.stream_type == self.StreamType.sink:
                regex = '^Default Sink: (.*)'

            matches = re.match(regex, line)
            if matches is not None:
                return matches.group(1)

        raise RuntimeError('Unable to determine the default {stream_type}. '
                           'Workaround: Fill out the "normal_{stream_type}_regex" field in the config file.\n\n'
                           'Output of `pactl info`:\n{pactl_info}'.format(
            stream_type=self.get_stream_type_name(),
            pactl_info=stdout
        ))

    def filter_by_client_name(self, stream_connections):
        """
        Removes some `stream_connections` if their client_name is excluded based on the config.
        """

        excluded_clients_regexes = self.config.audio_excluded_clients_regexes()

        new_stream_connections = []

        for stream_input in stream_connections:
            is_excluded = False
            for excluded_client_regex in excluded_clients_regexes:
                if stream_input.client_name is not None and \
                        re.match(excluded_client_regex, stream_input.client_name):
                    is_excluded = True
                    break

            if not is_excluded:
                new_stream_connections.append(stream_input)

        return new_stream_connections
