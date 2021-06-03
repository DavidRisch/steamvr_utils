import log


class OutputLogger:
    def __init__(self):
        self.outputs_by_command = {}

    def add_output(self, arguments, stdout, print_first=False):
        command = ' '.join(arguments)

        if print_first and command not in self.outputs_by_command:
            log.d('Output of \'{}\':\n{}'.format(command, stdout))

        self.outputs_by_command[command] = stdout

    def log_all(self):
        for command, output in self.outputs_by_command.items():
            log.d('Most recent output of \'{}\':\n{}'.format(command, output))
