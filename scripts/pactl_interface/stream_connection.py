class StreamConnection:
    def __init__(self, line):
        self.id = int(line.split('\t')[0])
        client_id_str = line.split('\t')[2]

        if client_id_str == "-":
            self.client_id = None
        else:
            self.client_id = int(client_id_str)

        self.client_name = None
