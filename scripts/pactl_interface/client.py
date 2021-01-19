import log

from . import utlis


class Client:
    def __init__(self, line):
        self.client_id = int(line.split('\t')[0])
        self.client_name = line.split('\t')[2]

    @classmethod
    def get_all_clients(cls, audio_switcher=None):
        arguments = ['pactl', 'list', 'short', 'clients']
        return_code, stdout, stderr = utlis.run(arguments)

        if audio_switcher is not None:
            if audio_switcher.last_pactl_clients is None:
                log.d('\'{}\':\n{}'.format(" ".join(arguments), stdout))
            audio_switcher.last_pactl_clients = stdout

        client_lines = stdout.split('\n')[:-1]

        clients = [cls(line) for line in client_lines]
        return clients

    @classmethod
    def get_client_names(cls, sink_inputs):
        clients = cls.get_all_clients()

        for sink_input in sink_inputs:
            matching_client = ([client for client in clients if client.client_id == sink_input.client_id] + [None])[0]
            if matching_client is not None:
                sink_input.client_name = matching_client.client_name
