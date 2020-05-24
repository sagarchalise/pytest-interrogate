"""Docstring coverage plugin for pytest using interrogate."""
import os
import warnings

import pytest
from interrogate import config as interrogate_conf
from interrogate import coverage as interrogate_cov


def validate_fail_under(num_str):
    """Fail under value from args.

    Should be under 100 as anything over 100 will be converted to 100.

    Args:
        num_str (str): string representation for integer.

    Returns:
        Any[float,int]: minimum of 100 or converted num_str

    """
    try:
        value = int(num_str)
    except ValueError:
        value = float(num_str)
    return min(value, 100)


def pytest_addoption(parser):
    """Add options to control interrogate."""
    group = parser.getgroup("interrogate", "Docstring coverage reporting with interrogate.")
    group.addoption(
        "--interrogate",
        action="append",
        default=[],
        metavar="SOURCE",
        nargs="?",
        const=True,
        dest="interrogate_source",
        help="Path or package name to measure during execution (multi-allowed)"
        "--interrogate supported for using CWD. "
        "Use --intterogate=PKGNAME for filtering."
        "--interrogate takes precedence.",
    )
    group.addoption(
        "--interrogate-verbose",
        action="store",
        metavar="VERBOSITY",
        default=0,
        choices=(0, 1, 2),
        type=int,
    )
    group.addoption(
        "--interrogate-ignore-regex", action="append", metavar="PATH", default=[], nargs="?",
    )
    group.addoption(
        "--interrogate-whitelist-regex", action="append", metavar="PATH", default=[], nargs="?",
    )
    group.addoption(
        "--interrogate-exclude", action="append", metavar="PATH", default=[], nargs="?",
    )
    group.addoption("--interrogate-tofile", action="store", default=None, type=str)
    group.addoption(
        "--interrogate-noreport-on-fail",
        action="store_true",
        default=False,
        help="Do not report interrogate if test run fails. " "Default: False",
    )
    group.addoption(
        "--interrogate-disable",
        action="store_true",
        default=False,
        help="Disable interrogate completely (useful for debuggers). " "Default: False",
    )
    group.addoption(
        "--interrogate-fail-under",
        action="store",
        metavar="MIN",
        type=validate_fail_under,
        default=80.0,
        help="Fail if the total interrogate is less than MIN.",
    )
    group.addoption(
        "--interrogate-ignore-init-method",
        action="store_true",
        default=False,
        help="Do not interrogate __init__ method. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-init-module",
        action="store_true",
        default=False,
        help="Do not interrogate __init__.py modules. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-private",
        action="store_true",
        default=False,
        help="Do not interrogate privates starting with __. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-nested-functions",
        action="store_true",
        default=False,
        help="Do not interrogate privates starting with _. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-module",
        action="store_true",
        default=False,
        help="Do not interrogate module in class. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-magic",
        action="store_true",
        default=False,
        help="Do not interrogate magic methods in class. " "Default: False",
    )
    group.addoption(
        "--interrogate-ignore-semiprivate",
        action="store_true",
        default=False,
        help="Do not interrogate magic methods in class. " "Default: False",
    )
    group.addoption(
        "--interrogate-no-color",
        action="store_false",
        help="Disable color output.",
        dest="interrogate_color",
    )
    group.addoption(
        "--interrogate-no-pyproject",
        action="store_false",
        help="Disable pyproject.toml if present. Default it uses pyproject.toml in cwd.",
        dest="interrogate_nopyproject",
    )


@pytest.mark.tryfirst
def pytest_load_initial_conftests(early_config, parser, args):
    """Pytest API for config loader."""
    if early_config.known_args_namespace.interrogate_source:
        plugin = PytestInterrogatePlugin(
            early_config.known_args_namespace, early_config.pluginmanager
        )
        early_config.pluginmanager.register(plugin, "_interrogate")


class PytestInterrogatePlugin(object):
    """Use interrogate package to produce code docstring reports."""

    def __init__(self, options, pluginmanager):
        """Create a interrogate pytest plugin."""
        self.interrogate = None
        self.interrogate_covered = None
        self.options = options
        self.failed = False
        self._disabled = getattr(options, "interrogate_disable", False)
        if self._disabled:
            return
        if not self.options.interrogate_source:
            return
        interrogate_opts = {}
        for option in {
            "ignore_init_method",
            "ignore_init_module",
            "ignore_magic",
            "ignore_module",
            "ignore_nested_functions",
            "ignore_private",
            "ignore_semiprivate",
            "fail_under",
            "color",
            "ignore_regex",
            "whitelist_regex",
        }:
            opt_val = getattr(self.options, "interrogate_{0}".format(option))
            if option.startswith("ignore") or option == "whitelist_regex":
                if opt_val:
                    interrogate_opts[option] = opt_val
            elif option == "interrogate_color":
                if not opt_val:
                    interrogate_opts[option] = opt_val
            elif opt_val != 80.0:
                interrogate_opts[option] = opt_val
        opts = None
        current_wd = os.getcwd()
        if not options.interrogate_nopyproject:
            pyproject_file = interrogate.config.find_pyproject_toml(current_wd)
            if pyproject_file:
                opts = interrogate.config.parse_pyproject_toml(pyproject_file)
        if opts:
            opts.update(interrogate_opts)
        else:
            opts = interrogate_opts
        if options.interrogate_source:
            if True in options.interrogate_source:
                all_source = [current_wd]
            else:
                all_source = [pth for pth in options.interrogate_source if pth is not True]
        self.interrogate_config = interrogate_conf.InterrogateConfig(**opts)
        self.interrogate = interrogate_cov.InterrogateCoverage(
            paths=all_source,
            conf=self.interrogate_config,
            excluded=self.options.interrogate_exclude,
        )
        if self.options.interrogate_fail_under is None:
            self.options.interrogate_fail_under = self.interrogate_config.fail_under

    @pytest.hookimpl(hookwrapper=True)
    def pytest_sessionfinish(self, session):
        """Pytest API function."""
        yield
        if self.interrogate:
            self.interrogate_results = self.interrogate.get_coverage()
            self.interrogate_covered = self.interrogate_results.perc_covered
            self.failed = self.interrogate_covered < self.options.interrogate_fail_under

    def pytest_terminal_summary(self, terminalreporter):
        """Pytest API function to write summary."""
        if self.failed:
            markup = {"red": True, "bold": True}
        else:
            markup = {"green": True}
        if self._disabled:
            message = "Interrogate disabled via --interrogate-disable switch!"
            terminalreporter.write("WARNING: {0}\n".format(message), **markup)
            warnings.warn(pytest.PytestWarning(message))
            return
        if (
            self.options.interrogate_noreport_on_fail
            or self.interrogate is None
            or self.interrogate_covered is None
        ):
            return

        _isatty = terminalreporter.isatty

        terminalreporter.isatty = lambda: _isatty
        terminalreporter.flush = lambda: None

        output_formatter = interrogate_cov.utils.OutputFormatter(
            self.interrogate.config, terminalreporter
        )
        base = self.interrogate._get_header_base()
        if self.options.interrogate_tofile:
            self.interrogate.print_results(
                self.interrogate_results,
                self.options.interrogate_tofile,
                self.options.interrogate_verbose,
            )
            output_formatter.tw.sep(
                "=",
                "Interrogate docstring coverage report for {0} written to file {1}".format(
                    base, self.options.interrogate_tofile
                ),
                fullwidth=output_formatter.TERMINAL_WIDTH,
                **markup
            )
        else:
            self.interrogate.output_formatter = output_formatter
            output_formatter = interrogate_cov.utils.OutputFormatter(
                self.interrogate.config, terminalreporter
            )
            self.interrogate.output_formatter = output_formatter
            output_formatter.tw.sep(
                "=",
                "Interrogate docstring coverage for {0}: {1}".format(
                    base, "FAILED" if self.failed else "SUCCESS"
                ),
                fullwidth=output_formatter.TERMINAL_WIDTH,
                **markup
            )
            if self.options.interrogate_verbose > 1:
                self.interrogate._print_detailed_table(self.interrogate_results)
            elif self.options.interrogate_verbose > 0:
                self.interrogate._print_summary_table(self.interrogate_results)
                output_formatter.tw.sep("-", title="", fullwidth=output_formatter.TERMINAL_WIDTH)
            message = (
                "REPORT: Required docstring coverage of {required}% {reached}. "
                "Total docstring coverage is {actual:.2f}%.\n".format(
                    required=self.options.interrogate_fail_under,
                    actual=self.interrogate_covered,
                    reached="not fulfilled" if self.failed else "fulfilled",
                )
            )
            terminalreporter.write(message, **markup)
        terminalreporter.isatty = _isatty
        terminalreporter.flush = lambda: AttributeError(
            "'{0}' has no attribute called 'flush'".format(terminalreporter.__class__.__name__)
        )


@pytest.fixture
def interrogate(request):
    """Pytest fixture to provide access to the underlying interrogate object."""
    if request.config.pluginmanager.hasplugin("_interrogate"):
        plugin = request.config.pluginmanager.getplugin("_interrogate")
        return plugin.interrogate
    return None
