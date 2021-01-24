import subprocess

import log

from .interface import BasestationInterface


class CmdBasestationInterface(BasestationInterface):

    def __init__(self, config):
        super().__init__(config)

    def execute_command(self, command):
        if command is None:
            log.i("Base Station command is None, nothing to do")
            return

        log.i("Executing Base Station command: {}".format(command))

        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log.i("Base Station command result:\nreturn code: {}\nstdout:\n{}\nstderr:\n{}".format(process.returncode,
                                                                                               process.stdout.decode(),
                                                                                               process.stderr.decode()))

    def action(self, action):
        if action == self.Action.ON:
            command = self.config.basestation_command('on')
        elif action == self.Action.OFF:
            command = self.config.basestation_command('off')
        else:
            raise NotImplementedError()

        self.execute_command(command)
