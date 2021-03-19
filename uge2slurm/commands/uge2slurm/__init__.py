import logging

from neotermcolor import cprint

from ..argparser import get_top_parser

from uge2slurm import VERSION
from uge2slurm.utils.path import get_command_paths
from uge2slurm.utils.log import entrypoint
from uge2slurm.commands.qsub import set_subperser

logger = logging.getLogger(__name__)


UGE_COMMAND_NAMES = (
    "qacct",
    "qalter",
    "qconf",
    "qdel",
    "qhold",
    "qhost",
    "qlogin",
    "qmake",
    "qmod",
    "qmon",
    "qping",
    "qquota",
    "qralter",
    "qrdel",
    "qresub",
    "qrls",
    "qrsh",
    "qrstat",
    "qrsub",
    "qselect",
    "qsh",
    "qstat",
    "qsub",
    "sge_container_init",
    "sge_container_shepherd",
    "sge_coshepherd",
    "sge_execd",
    "sge_qmaster",
    "sge_shadowd",
    "sge_shepherd",
    "sgepasswd"
)

SLURM_COMMAND_NAMES = (
    "sacct",
    "sacctmgr",
    "salloc",
    "sattach",
    "sbatch",
    "sbcast",
    "scancel",
    "scontrol",
    "sdiag",
    "sgather",
    "sinfo",
    "sprio",
    "squeue",
    "sreport",
    "srun",
    "sshare",
    "sstat",
    "strigger",
    "sview"
)


@entrypoint(logger)
def main():
    parser = get_top_parser()

    subparsers = parser.add_subparsers()
    set_subperser("qsub", subparsers)

    args = parser.parse_args()
    if args.func:
        return args.func(args)
    else:
        print(parser.prog, VERSION)
        parser.print_usage()

        print("\nUGE Commands:")
        _print_command_status(UGE_COMMAND_NAMES)
        print("\nslurm Commands:")
        _print_command_status(SLURM_COMMAND_NAMES)


def _print_command_status(commands):
    for command in commands:
        candidates = get_command_paths(command)
        if not candidates:
            cprint("\t{}: command not found.".format(command), "yellow")
        elif len(candidates) == 1:
            cprint("\t{} -> {}".format(command, candidates[0]), "cyan")
        else:
            cprint("\t{} -> {} (duplicated!)".format(command, candidates), "red")
