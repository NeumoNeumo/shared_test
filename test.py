import time
from collections import defaultdict
from pathlib import Path
import sys
import json
import argparse
import subprocess
from enum import Enum

epilog = """With no options, test will read from the config file (./test.conf
by default) automatically test your executable according to the testcase in
`<labID>/test/<problemID>/<testcaseID>` where <labID> and <testcaseID> are two
two-digit numbers and <problemID> is a lowercase letter.

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

Configuration file describes which problem you are dealing with. It is in the
format of json, containing labID and problemID.
"""


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


class Status(Enum):
    SUCCESS = 0
    WRONG_ANSWER = 1
    TIME_LIMIT_EXCESS = 2
    RUNTIME_ERROR = 3


class DefaultTheme:
    def __init__(self):
        self.testInfo = self._TestInfo()
        self.notify = self._Notify()

    class _TestInfo:
        # Animation, decoration and print info when testing EXEC:
        def test_bef(self, args, testsets, match=False):
            print("Start to test")

        def testset_bef(self, testset_name, match=False):
            print(f"Testset [{testset_name}] started")

        def testcase_bef(self, casename, match=False):
            pass

        def testcase_in(self, casename, match=False):
            print(f"Testing [{casename}]... ", end="")

        def testcase_aft(
            self,
            casename,
            status,
            time,
            stderr=None,
            match=False,
            result=None,
            expected=None,
        ):
            if status == Status.SUCCESS.value:
                print(f"Passed in {time*1000:.2f}ms")
            elif status == Status.WRONG_ANSWER.value:
                print(f"current: {result}")
                print(f"expected: {expected}")
            elif stderr:
                print("Runtime Error")
                print(stderr)
            else:
                print(Status(status).name)

        def testset_aft(self, testset_name, status_dict, match=False):
            success_num = 0
            tot_num = 0
            for status in status_dict:
                if status == Status.SUCCESS.value:
                    success_num += len(status_dict[status])
                tot_num += len(status_dict[status])

            print(
                f"Pass {success_num*100.0/tot_num:.2f}% ({success_num}/{tot_num}) in testset [{testset_name}]"
            )

        def test_aft(self, testset_names, status_dict, match=False):
            success_num = 0
            tot_num = 0
            for status in status_dict:
                if status == Status.SUCCESS.value:
                    success_num += len(status_dict[status])
                tot_num += len(status_dict[status])
            txt = f"Totally passed {success_num*100.0/tot_num:.2f}% ({success_num}/{tot_num}) in "
            first = True
            for tn in testset_names:
                if first:
                    txt += f"[{tn}]"
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


class Test:
    def __init__(self, args, theme=DefaultTheme):
        self.args = args
        self.theme = theme()

    def begin(self):
        notify = self.theme.notify
        info = self.theme.testInfo
        args = self.args
        conf_p = Path("test.conf")
        if not conf_p.is_file():
            notify.warn("Config file not found.")
            if notify.yes_or_no("Confirm to init config? (Y/n)"):
                labID = input("Please input your labID (lab**): ")
                problemID = input(
                    "Please input your problemID (lowercase single letter): "
                )
                with open(conf_p, "w") as f:
                    json.dump({"labID": labID, "problemID": problemID}, f)
            else:
                return
        with open(conf_p, "r") as f:
            conf = json.load(f)
        labID = conf["labID"]
        problemID = conf["problemID"]
        testset_opt = list()
        if not args.random and not args.Random:
            testset_opt = ["default"]
        elif args.Random:
            testset_opt = ["default", "random"]
            case_num = args.Random
        elif args.random:
            testset_opt = ["random"]
            case_num = args.random

        test_basedir = Path(__file__).parent / labID / "test" / problemID
        test_conf_p = test_basedir / "test.conf"
        if not test_conf_p.is_file():
            notify.warn("test.conf not found.")
            if notify.yes_or_no(
                f"Create test config for problem {problemID} in {labID}? (Y/n)"
            ):
                timeout = input("Time Limit in seconds (float): ")
                with open(test_conf_p, "w") as f:
                    json.dump({"timeout": int(timeout)}, f)
            else:
                return
        with open(test_conf_p, "r") as f:
            test_conf = json.load(f)
        timeout = test_conf["timeout"]

        if not test_basedir.is_dir():
            notify.error(
                f"{str(test_basedir)} not a directory. It is possible that nobody has written a testcase yet "
            )
            return
        testsets = list()
        if "default" in testset_opt:
            testsets.append(DefaultTestSet(labID, problemID))
        if "random" in testset_opt:
            import sys

            sys.path.insert(1, str(test_basedir))
            try:
                from spec import RandomTestSet  # type: ignore
            except Exception:
                notify.error(f"random_test.* not found under {str(test_basedir)}")
                return
            testsets.append(RandomTestSet(labID, problemID, case_num))  # type: ignore
        exec_p = Path(args.EXEC)
        info.test_bef(args, testsets)
        if not args.match:
            acc_testset_names = list()
            acc_status_dict = defaultdict(list)
            for testset in testsets:
                info.testset_bef(testset.name)
                status_dict = defaultdict(list)
                for casename, unit_case, verifier in testset:
                    info.testcase_bef(casename)
                    info.testcase_in(casename)
                    duration = 0.0
                    start_time = time.time()
                    status = Status.SUCCESS.value
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
                                status = Status.WRONG_ANSWER.value
                                testcase_infoed = True
                                info.testcase_aft(
                                    casename,
                                    status,
                                    duration,
                                    result=complete_ps.stdout,
                                    expected=verifier,
                                )
                        else:
                            if not verifier(complete_ps.stdout):
                                status = Status.WRONG_ANSWER.value
                        if not testcase_infoed:
                            info.testcase_aft(casename, status, duration)
                    except subprocess.TimeoutExpired:
                        duration = timeout
                        status = Status.TIME_LIMIT_EXCESS.value
                        info.testcase_aft(casename, status, duration)
                    except subprocess.CalledProcessError:
                        duration = time.time() - start_time
                        status = Status.RUNTIME_ERROR.value
                        info.testcase_aft(
                            casename,
                            status,
                            duration,
                            stderr=complete_ps.stderr,  # type: ignore
                        )
                    status_dict[status].append(casename)
                utility.unionDict(acc_status_dict, status_dict)
                acc_testset_names.append(testset.name)
                info.testset_aft(testset.name, status_dict)
            info.test_aft(acc_testset_names, acc_status_dict)
        else:
            pass


class utility:
    @staticmethod
    def unionDict(a, b):
        # a is a defaultdict(list)
        for k in b:
            a[k] += b[k]


def main(args):
    Test(args).begin()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="test [-h] [-rR NUM] [-l] [-m SID] EXEC",
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
    parser.add_argument("EXEC", help="the executable to be tests")

    main(parser.parse_args())
