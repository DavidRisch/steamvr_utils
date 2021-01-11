import os
import subprocess


def run(arguments):
    environment = dict(os.environ)
    environment['LC_ALL'] = 'C'  # https://github.com/DavidRisch/steamvr_utils/issues/2

    process = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)

    return process.returncode, process.stdout.decode(), process.stderr.decode()
