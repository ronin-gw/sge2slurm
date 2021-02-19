import logging
import os
from functools import partialmethod

from uge2slurm.mapper import CommandMapperBase, bind_to, bind_if_true, not_implemented, not_supported
from uge2slurm.commands import UGE2slurmCommandError

logger = logging.getLogger()


class CommandMapper(CommandMapperBase):
    _logger = logger
    _DEFAULT_JOB_NAME = "%x.{}%j"
    _MAIL_OPTION_MAPPER = dict(
        b=("BEGIN", ),
        e=("END", ),
        a=("FAIL", "REQUEUE")
    )

    def is_array(self):
        return self._args.t is not None

    def _get_default_filename(self, option_string):
        filename = self._DEFAULT_JOB_NAME.format(option_string)
        if self.is_array():
            filename += ".%a"
        return filename

    def _map_path(self, _value, option_name, bind_to, option_string, is_output=True):
        path = _value[0]
        if len(_value) > 1:
            self._logger.warning('setting multiple paths for "{}" option is not '
                                 'supported. use first one: {}'.format(option_name, path))

        if path.startswith(':'):
            path = path.lstrip(':')
        elif ':' in path:
            self._logger.warning('"hostname" specification in "{}" option is not supported.'.format(option_name))
            path = path.split(':', 1)[1]

        if is_output:
            if os.path.isdir(path):
                filename = self._get_default_filename(option_string)
                path = os.path.join(path, filename)
            elif os.path.isfile(path):
                self._logger.warning('output file specified by "{}" will be overwritten.'.format(option_name))
            else:
                dirname, filename = os.path.split(path)
                if not os.path.exists(dirname):
                    # try:
                    os.makedirs(dirname)

                filename = filename.replace('%', "%%")
                filename = filename.replace("$USER", "%u")
                filename = filename.replace("$JOB_ID", "%j")
                filename = filename.replace("$JOB_NAME", "%x")
                filename = filename.replace("$HOSTNAME", "%N")
                filename = filename.replace("$TASK_ID", "%a")

                path = os.path.join(dirname, filename)

        self.args += [bind_to, path]

    _optionfile = not_implemented("-@")

    def a(self, datetime):
        self.args += ["--begin", datetime.isoformat()]

    ac = not_implemented("-ac")
    adds = not_implemented("-adds")
    ar = bind_to("--reservation")
    A = bind_to("--account")
    binding = not_implemented("-binding")

    def b(self, value):
        # TODO: use `--wrap` option?
        pass

    c = not_implemented("-c")
    ckpt = not_implemented("-ckpt")
    clear = not_implemented("-clear")
    clearp = not_implemented("-clearp")
    clears = not_implemented("-clears")

    def cwd(self, value):
        if value is not True:
            return
        self.args += ["--chdir", os.getcwd()]

    # C
    dc = not_implemented("-dc")

    def dl(self, datetime):
        self.args += ["--deadline", datetime.isoformat()]

    e = partialmethod(_map_path, option_name="-e", bind_to="--error", option_string='e')
    # hard
    h = bind_if_true("--hold")
    # `hold_jid` and `hold_jid_ad` will be solved together
    # hold_jid
    # hold_jid_ad
    i = partialmethod(_map_path, option_name="-i", bind_to="--input", option_string='i', is_output=False)
    # handle `j` at pre_ and post_convert
    # j
    jc = not_implemented("-jc")
    js = not_implemented("-js")
    jsv = not_implemented("-jsv")
    masterl = not_implemented("-masterl")

    def l(self, value):
        # TODO: map resource request
        pass

    def m(self, value):
        mailtypes = []
        for option in value:
            if option == 'n':
                pass
            if option in self._MAIL_OPTION_MAPPER:
                mailtypes += [t for t in self._MAIL_OPTION_MAPPER[option]]
            else:
                self._logger.warning('Unknown mail type "{}" for "{}" was ignored.'.format(
                    option, "-m"
                ))

        if mailtypes:
            self.args += ["--mail-type", ','.join(mailtypes)]

    def M(self, _value):
        user = _value[0]
        if len(_value) > 1:
            self._logger.warning('setting multiple paths for "-M" option is not '
                                 'supported. use first one: {}'.format(user))
        self.args += ["--mail-user", user]

    masterq = not_implemented("-masterq")
    mod = not_implemented("-mod")
    mbind = not_implemented("-mbind")
    notify = not_implemented("-notify")  # use `--signal`?
    now = not_implemented("-now")
    N = bind_to("--job-name")
    o = partialmethod(_map_path, option_name="-o", bind_to="--output", option_string='o')
    ot = not_implemented("-ot")
    P = bind_to("--wckey")
    p = bind_to("--nice")
    par = not_implemented("-par")

    def pe(self, vlaue):
        # TODO: map resource request
        pass

    pty = not_implemented("-pty")

    def q(self, value):
        hosts = []
        for queue in value:
            text = queue.split('@', 1)
            if len(text) == 1 or text[1].startswith('@'):
                self._logger.error('Queue specification at "-q" option requires host name: ' + queue)
            else:
                hosts.append(text[1])
        if hosts:
            self.args += ["--nodelist", ','.join(hosts)]

    R = not_implemented("-R")

    def r(self, value):
        if value is True:
            self.args.append("--requeue")
        elif value is False:
            self.args.append("--no-requeue")

    rou = not_implemented("-rou")
    rdi = not_implemented("-rdi")
    sc = not_implemented("-sc")
    shell = not_implemented("-shell")
    si = not_implemented("-si")
    # soft
    sync = not_implemented("-sync")  # TODO: use `--wait`

    def S(self, value):
        # TODO: change shell
        pass

    # `t` and `tc` will be processed together
    # t
    # tc
    tcon = not_supported("-tcon")
    terse = bind_if_true("--parsable")
    umask = not_implemented("-umask")
    # v: processed at post_convert
    verify = not_supported("-verify")
    # V: processed at post_convert
    w = not_implemented("-w")
    wd = bind_to("--chdir")
    xd = not_supported("-xd")
    xdv = not_supported("-xdv")
    xd_run_as_image_user = not_supported("-xd_run_as_image_user")

    def __init__(self, bin):
        super().__init__(bin)

        self.dest2converter['@'] = self._optionfile

    def pre_convert(self):
        if self._args.j is True:
            setattr(self._args, 'e', None)

    def post_convert(self):
        self._map_dependency()
        self._prepare_output_path()
        self._map_array()
        self._map_environ_vars()

        self.args += self._args.command

    def _map_dependency(self):
        # TODO: convert job name to job ID?
        nonarray_dependencies = []
        if self._args.hold_jid is not None:
            for jobid in self._args.hold_jid:
                if not jobid.isdigit():
                    self._logger.error("Currently, only job ID is supported for job dependency specification.")
                    raise UGE2slurmCommandError
                nonarray_dependencies.append(jobid)

        array_dependencies = []
        if self._args.hold_jid_ad is not None:
            for jobid in self._args.hold_jid_ad:
                if not jobid.isdigit():
                    self._logger.error("Currently, only job ID is supported for job dependency specification.")
                    raise UGE2slurmCommandError
                array_dependencies.append(jobid)

        dependencies = []
        if nonarray_dependencies:
            dependencies.append("afterok:" + ':'.join(nonarray_dependencies))
        if array_dependencies:
            dependencies.append("aftercorr:" + ':'.join(array_dependencies))

        if dependencies:
            self.args += ["--dependency", ','.join(dependencies)]

    def _prepare_output_path(self):
        if self._args.o is None:
            filename = self._get_default_filename('o')
            self.args += ["--output", filename]

        if self._args.j is not True and self._args.e is None:
            filename = self._get_default_filename('e')
            self.args += ["--error", filename]

    def _map_array(self):
        if not self.is_array():
            return

        array = self._args.t
        print(array)
        if self._args.tc:
            array += '%' + self._args.tc

        self.args += ["--array", array]

    def _map_environ_vars(self):
        export = []
        if self._args.V is True:
            export.append("ALL")

        if self._args.v:
            export += self._args.v

        if not export:
            export.append("NONE")

        self.args += ["--export", ','.join(export)]