import subprocess
import logging

from uge2slurm.utils.path import get_command_path
from uge2slurm.commands import UGE2slurmCommandError

logger = logging.getLogger(__name__)


def run_command(command_name, args):
    binary = get_command_path(command_name)

    try:
        if not binary:
            raise FileNotFoundError
        command = [binary] + args
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=15, check=True, universal_newlines=True)
    except FileNotFoundError:
        raise UGE2slurmCommandError("Command `{}` not found.".format(command_name))
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if e.stderr:
            logger.error(command_name + ": " + e.stderr)
        raise UGE2slurmCommandError("Failed to execute `{}` command.".format(command_name))
