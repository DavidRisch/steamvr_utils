import os
import signal
import subprocess
import sys

import log
import psutil

from .interface import BasestationInterface


class V1BasestationInterface(BasestationInterface):

    def __init__(self, config):
        super().__init__(config)

        # File from: https://github.com/risa2000/lhctrl
        self.lhctrl_path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'lhctrl.py'))

        self.process = None

    def action(self, action):
        if action == BasestationInterface.Action.ON:
            if self.process is not None:
                raise NotImplementedError()

            arguments = [
                sys.executable,  # Current Python interpreter
                self.lhctrl_path,
                '--lh_b_id', self.config.basestation_id('b'),
                '--lh_b_mac', self.config.basestation_mac_address('b'),
                '--lh_c_id', self.config.basestation_id('c'),
                '--lh_c_mac', self.config.basestation_mac_address('c'),
                '--lh_timeout', str(10),
                '--ping_sleep', str(5),
                '--try_count', str(self.config.basestation_attempt_count_set()),
                '--try_pause', str(1),
            ]

            log.i("Starting lhctrl: {}".format(arguments))

            self.process = subprocess.Popen(arguments)
        elif action == BasestationInterface.Action.OFF:
            log.i('Terminating all instances of lhctrl')
            lhctrl_processes = []
            for process in psutil.process_iter():
                cmd_line = process.cmdline()
                if len(cmd_line) >= 2 and cmd_line[1] == self.lhctrl_path:
                    lhctrl_processes.append(process)

            log.d('Found {} instances of lhctrl'.format(len(lhctrl_processes)))
            for process in lhctrl_processes:
                process.send_signal(signal.SIGINT)
        else:
            raise NotImplementedError()
