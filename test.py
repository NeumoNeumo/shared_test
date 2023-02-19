from os import name
import time
import importlib
from collections import defaultdict
from pathlib import Path
import sys
import argparse
import subprocess
from enum import Enum

epilog = """With no options, test will test your executable <EXEC> according to
the testcase in `<LABID>/test/<PROBID>/<testcaseID>`.

In the `test` directory of every problem, a file `spec.*` is required to specify
basic settings and optional problem-specific random testcase generator for the
problem where `*` means `.py` or `.out`. When both `.py` and `.out` exist,
`.out` is prefered in consideration of efficiency. (However, the support for
`spec.out` has not been implemented yet. TODO: support for `spec.out`)

In `spec.py`, a function `get_config` that returns a config object is required.
The config object must contain a key "timeout" which indicates the time limit
in the unit of seconds, the value being a number. Additionally, if randomly
generated testcases are wanted, `spec.py` ought to have a class `RandomTestSet`
inheriting from class `RandomTestSetBase` in the `test.py`

To change the default setting, the following options can be used.

   *`-r NUM` tests your program with NUM random cases if `spec.py` or `spec.out`
    is provided in `<labID>/test/<problemID>/<testcaseID>/`. When both of these
    two files exist, `spec.out` is prefered in consideration of efficiency. If
    using python module, there must be a class `RandomTestSet` in module
    `spec.py` inheriting from `TestSet` in this file.

   *`-R` behaves the same as `-r` except for using default testcases as well.

   *`-m SID` helps to match your result with that of other students with SID as
    his or her studentID. Either full studentID or the last few digits, if no
    ambiguity (usually last 4 is enough), is acceptable.

   *`-l` helps to list all the available executables you can match with.
"""


class DefaultTheme:
    def __init__(self):
        # TODO: use logging module to optimize stderr and stdout
        self.testInfo = self._TestInfo()
        self.notify = self._Notify()

    class _TestInfo:
        # Animation, decoration and print info when testing EXEC:
        def __init__(self):
            self.acc_testset_names: list
            self.acc_status_dict: defaultdict
            self.testsets: list
            self.args: argparse.Namespace
            self.testset_name: str
            self.status_dict: defaultdict
            self.casename: str
            self.case_input: str

        def __unionDict(self, a, b):
            # a is a defaultdict(list)
            for k in b:
                a[k] += b[k]

        def pre_test(self, args, testsets, match=False):
            self.testsets = testsets
            self.acc_testset_names = [ts.name for ts in testsets]
            self.acc_status_dict = defaultdict(list)
            self.args = args
            print("Start to test")

        def pre_testset(self, testset_name, match=False):
            self.testset_name = testset_name
            self.status_dict = defaultdict(list)
            print(f"Testset [{testset_name}] started")

        def pre_testcase(self, casename, case_input, match=False):
            self.casename = casename
            self.case_input = case_input
            print(f"Testing [{casename}]... ", end="")

        def post_testcase(
            self,
            status,
            time,
            stderr=None,
            match=False,
            **kwargs,
        ):
            self.status_dict[status.value] += self.casename
            if status == Status.SUCCESS:
                print(f"Passed in {time*1000:.2f}ms")
            elif status == Status.WRONG_ANSWER:
                print(f"WA\ncurrent: {kwargs['result']}")
                print(f"expected: {kwargs['expected'].strip()}")
            elif stderr:
                print("Runtime Error")
                print(stderr)
            else:
                print(status)

        def post_testset(self, match=False):
            success_num = 0
            tot_num = 0
            for status in self.status_dict:
                if status == Status.SUCCESS.value:
                    success_num += len(self.status_dict[status])
                tot_num += len(self.status_dict[status])
            self.__unionDict(self.acc_status_dict, self.status_dict)
            print(
                f"Passed {success_num*100.0/tot_num:.2f}% ({success_num}/{tot_num}) in testset [{self.testset_name}]"
            )

        def post_test(self, match=False):
            success_num = 0
            tot_num = 0
            for status_v in self.acc_status_dict:
                if status_v == Status.SUCCESS.value:
                    success_num += len(self.acc_status_dict[status_v])
                tot_num += len(self.acc_status_dict[status_v])
            txt = f"Totally passed {success_num*100.0/tot_num:.2f}% ({success_num}/{tot_num}) in "
            first = True
            for tn in self.acc_testset_names:
                if first:
                    txt += f"[{tn}]"
                    first = False
                else:
                    txt += f", [{tn}]"
            print(txt)

    class _Notify:
        _RST = "\033[0m"
        _RED = "\033[1;31m"
        _YEL = "\033[1;33m"

        # Notification:
        def warn(self, txt):
            print(self._YEL + "Warn: " + self._RST + txt)

        def error(self, txt):
            print(self._RED + "Error: " + self._RST + txt)

        def yes_or_no(self, txt):
            yn = input(txt)
            if yn == "n" or yn == "N" or yn == "NO" or yn == "No":
                return False
            elif yn == "y" or yn == "Y" or yn == "YES" or yn == "Yes" or yn == "":
                return True
            else:
                self.error("Invalid input")
                sys.exit(1)


_THEME = DefaultTheme()


class TestSet:
    """This is the class which all customized test sets should inherit"""

    def __init__(self, name, labID, problemID):
        self.name = name
        self.labID = labID
        self.problemID = problemID

    def __iter__(self):
        return self

    def __next__(self):
        """
        Returns: (casename, unit_case, verifier)
            casename (string): name of the testcase
            unit_case (string): directed to stdin of the tested program
            verifier (string|Callable[[string], bool]) : either a string used to
                match the stdout or a function to verify whether the output is
                reasonable (usually used when the problem has multiple
                solutions)
        """
        raise NotImplementedError()

    def __len__(self):
        """
        Returns: num_cases
        """
        raise NotImplementedError()


class DefaultTestSet(TestSet):
    """get test data from given fils in <labID>/test/<problemID>/<testcaseID>"""

    def __init__(self, labID, problemID):
        super().__init__("Default", labID, problemID)
        self.data_dir = Path(__file__).parent / labID / "test" / problemID
        self.glob_list = list(self.data_dir.glob("*.in"))
        self.length = len(self.glob_list)
        self.pointer = 0

    def __next__(self):
        if self.pointer == self.length:
            raise StopIteration
        p = self.pointer
        self.pointer += 1
        tc_ip = self.glob_list[p]
        tc_name = tc_ip.stem
        tc_input = tc_ip.read_text()
        tc_output = (tc_ip.parent / (tc_name + ".out")).read_text()
        return (tc_name, tc_input, tc_output)

    def __len__(self):
        return self.length


class RandomTestSetBase(TestSet):
    """Every RandomTestSet should inherit from this class"""

    def __init__(self, labID, problemID, case_num, testset_name="Random"):
        super().__init__(testset_name, labID, problemID)
        self.case_num = case_num
        self.cnt = 0
        self.num = case_num

    def __len__(self):
        return self.num

    def __next__(self):
        if self.cnt == self.num:
            raise StopIteration
        self.cnt += 1
        return self.generate()

    def generate(self):
        raise NotImplementedError


class PseudoLabelTestset(TestSet):
    """Testset with pseudo labels generated from a given executable"""

    def __init__(self, src_set: TestSet, labID, probID, sID):
        super().__init__(src_set.name, src_set.labID, src_set.problemID)
        self.src_set = src_set
        self.cnt = 0
        self.num = len(self.src_set)
        self.labID = labID
        self.probID = probID
        self.src_it = iter(self.src_set)
        self.sID = sID

    def __len__(self):
        return self.num

    def __next__(self):
        if self.cnt == self.num:
            raise StopIteration
        casename, unit_case, verifier = next(self.src_it)
        if not isinstance(verifier, str):
            _THEME.notify.warn(
                f"The output of testcase {casename} in testset {self.src_set.name} is not unique."
            )
        exec_p = Path(__file__).parent / self.labID / str(self.sID) / self.probID
        try:
            complete_ps = subprocess.run(
                f"{exec_p.absolute()}",
                text=True,
                capture_output=True,
                timeout=7,
                input=unit_case,
            )
        except subprocess.TimeoutExpired:
            _THEME.notify.error(
                f"{self.sID} timeout at testcase {casename} in testset {self.src_set.name} "
            )
            exit(1)
        verifier = complete_ps.stdout.strip()
        self.cnt += 1
        return (casename, unit_case, verifier)


class Status(Enum):
    SUCCESS = 0
    WRONG_ANSWER = 1
    TIME_LIMIT_EXCESS = 2
    RUNTIME_ERROR = 3


class Test:
    def __init__(self, args, theme=None):
        self.args = args
        if theme:
            self.theme = theme
        else:
            self.theme = DefaultTheme()
        self.labID = args.LABID
        self.problemID = args.PROBID

    def import_spec(self, args):
        notify = self.theme.notify
        test_basedir = Path(__file__).parent / self.labID / "test" / self.problemID
        if not test_basedir.is_dir():
            notify.error(
                f"{str(test_basedir)} not a directory. It is possible that nobody has written a testcase yet "
            )
            sys.exit(1)
        spec_p = test_basedir / "spec.py"
        if not spec_p.is_file():
            notify.warn("spec.py not found.")
            if notify.yes_or_no(
                f"Create test config for problem {self.problemID} in {self.labID}? (Y/n)"
            ):
                timeout = input("Time Limit in seconds (float): ")
                spec_p.write_text('def get_config():\n    return {"timeout": 1}')
            else:
                sys.exit(1)
        sys.path.insert(1, str(test_basedir))
        try:
            return importlib.import_module("spec")
        except Exception:
            notify.error(f"spec.* not found under {str(test_basedir)}")
            sys.exit(1)

    def get_testsets(self, args, spec):
        testset_opt = list()
        case_num = 5
        if not args.random and not args.Random:
            testset_opt = ["default"]
        elif args.Random:
            testset_opt = ["default", "random"]
            case_num = args.Random
        elif args.random:
            testset_opt = ["random"]
            case_num = args.random
        testsets = list()
        if "default" in testset_opt:
            testsets.append(DefaultTestSet(self.labID, self.problemID))
        if "random" in testset_opt:
            testsets.append(spec.RandomTestSet(self.labID, self.problemID, case_num))
        return testsets

    def get_exec_path(self, args):
        notify = self.theme.notify
        exec_p = Path(self.args.EXEC)
        if not exec_p.is_file():
            notify.error(f"{exec_p.absolute()} is not a valid path to an executable")
            sys.exit(1)
        return exec_p

    def match_test(self, args, testsets, config, exec_p):
        pseudo_testsets = list()
        for tss in testsets:
            pseudo_testsets.append(
                PseudoLabelTestset(tss, args.LABID, args.PROBID, args.match)
            )
        self.unit_test(args, pseudo_testsets, config, exec_p)

    def unit_test(self, args, testsets, config, exec_p):
        timeout = config["timeout"]
        info = self.theme.testInfo
        for testset in testsets:
            info.pre_testset(testset.name)
            for casename, unit_case, verifier in testset:
                info.pre_testcase(casename, unit_case)
                duration = -1.0
                start_time = time.time()
                status = Status.SUCCESS
                try:
                    complete_ps = subprocess.run(
                        f"{exec_p.absolute()}",
                        text=True,
                        capture_output=True,
                        timeout=timeout,
                        input=unit_case,
                    )
                    duration = time.time() - start_time
                    testcase_infoed = False
                    if isinstance(verifier, str):
                        if complete_ps.stdout.strip() != verifier.strip():
                            status = Status.WRONG_ANSWER
                            testcase_infoed = True
                            info.post_testcase(
                                status,
                                duration,
                                result=complete_ps.stdout,
                                expected=verifier,
                            )
                    else:
                        if not verifier(complete_ps.stdout):
                            status = Status.WRONG_ANSWER
                    if not testcase_infoed:
                        info.post_testcase(status, duration)
                except subprocess.TimeoutExpired:
                    duration = timeout
                    status = Status.TIME_LIMIT_EXCESS
                    info.post_testcase(status, duration)
                except subprocess.CalledProcessError:
                    duration = time.time() - start_time
                    status = Status.RUNTIME_ERROR
                    info.post_testcase(
                        status,
                        duration,
                        stderr=complete_ps.stderr,  # type: ignore
                    )
            info.post_testset()
        info.post_test()

    def test_main(self, args, testsets, config, exec_p):
        info = self.theme.testInfo
        info.pre_test(self.args, testsets)
        testType = list()
        if self.args.match:
            testType.append(self.match_test)
        else:
            testType.append(self.unit_test)
        for tt in testType:
            tt(args, testsets, config, exec_p)

    def perform(self):
        spec = self.import_spec(self.args)
        config = spec.get_config()
        testsets = self.get_testsets(self.args, spec)
        exec_p = self.get_exec_path(self.args)

        self.test_main(self.args, testsets, config, exec_p)


def main(args):
    _THEME = DefaultTheme()
    Test(args, theme=_THEME).perform()
    # print(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="test [-h] [-rR NUM] [-l] [-m SID] LABID PROBID EXEC",
        prog="test",
        description="A simple tool for test cpp codes.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-r", "--random", type=int, help="test NUM random cases")
    parser.add_argument("-R", "--Random", type=int, help="random test and default test")
    parser.add_argument(
        "-m", "--match", metavar="SID", help="matching test with another"
    )
    parser.add_argument(
        "-l", "--list-available", action="store_true", help="list available executables"
    )
    parser.add_argument("LABID", help="usually in the format of lab**")
    parser.add_argument("PROBID", help="usually a single lowercase letter")
    parser.add_argument("EXEC", help="the executable to be tests")

    main(parser.parse_args())
