import os
import subprocess


def run(arguments, assert_success=True):
    environment = dict(os.environ)
    environment['LC_ALL'] = 'C'  # https://github.com/DavidRisch/steamvr_utils/issues/2

    process = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)

    return_code = process.returncode
    stdout = process.stdout.decode()
    stderr = process.stderr.decode()

    if assert_success and return_code != 0:
        raise RuntimeError(
            'Running \'{}\' failed with return code {}.\n'.format(' '.join(arguments), return_code)
            + 'stdout:\n{}'.format(stdout)
            + 'stderr:\n{}'.format(stderr)
        )

    return return_code, stdout, stderr
