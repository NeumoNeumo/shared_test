import time
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

   *`-r` tests your program with random cases if `random_test.py` or
    `random_test.out` is provided in `<labID>/test/<problemID>/<testcaseID>/`.
    When both of these two files exist, `random_test.out` is prefered in
    consideration of efficiency. If using python module, there must be a class
    `RandomTestSet` in module `random_test.py` inheriting from `TestSet` in this
    file.

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

    def __next__(self):
        pass

class Status(Enum):
    SUCCESS = 0
    WRONG_ANSWER = 1
    TIME_LIMIT_EXCESS = 2
    RUNTIME_ERROR = 3

class DefaultTheme():
    def __init__(self):
        self.testInfo = self._TestInfo()
        self.notify = self._Notify()
    class _TestInfo():
        # Animation, decoration and print info when testing EXEC:
        def testset_bef(self, testset_name):
            print(f"Testset [{testset_name}] started")
        def testcase_bef(self, casename):
            pass
        def testcase_in(self, casename):
            print(f"Testing [{casename}] ", end="")
        def testcase_aft(self, casename, status):
            if status == Status.SUCCESS:
                print("Passed")
            else:
                print("Failed")
        def testset_aft(self, testset_name, status_dict):
            success_num = 0
            tot_num = 0
            for status in status_dict:
                if status == Status.SUCCESS:
                    success_num += len(status_dict[status])
                tot_num += len(status_dict[status])
            
            print(f"Pass {success_num*100.0/tot_num:.2f}% ({success_num}/tot_num) in testset [{testset_name}]")
        def test_aft(self, testset_names ,status_dict):
            success_num = 0
            tot_num = 0
            for status in status_dict:
                if status == Status.SUCCESS:
                    success_num += len(status_dict[status])
                tot_num += len(status_dict[status])
            txt = f"Totally passed {success_num*100.0/tot_num:.2f}% ({success_num}/tot_num) in "
            first = True
            for tn in testset_names:
                if first:
                    txt += f"[{tn}]"
                else:
                    txt += f", [{tn}]"
            print(txt)

    class _Notify():
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


class Test():
    def __init__(self, args, theme=DefaultTheme):
        self.args = args
        self.theme = theme()
    def begin(self):
        notify = self.theme.notify
        args = self.args
        conf_p = Path("test.conf")
        if not conf_p.is_file():
            print("lala")
            notify.warn("Config file not found.")
            if notify.yes_or_no("Confirm to init config? (Y/n)"):
                labID = input("Please input your labID (lab**): ")
                problemID = input("Please input your problemID (lowercase single letter): ")
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
        elif args.random:
            testset_opt = ["random"]

        test_basedir = Path(__file__).parent/labID/"test"/problemID
        test_conf_p = test_basedir/"test.conf"
        if not test_conf_p.is_file():
            notify.warn("test.conf not found.")
            if notify.yes_or_no(f"Create test config for problem {problemID} in {labID}? (Y/n)"):
                timeout = input("Time Limit in seconds (float)")
                with open(test_conf_p, "w") as f:
                    json.dump({"timeout": timeout}, f)
            else:
                return
        with open(test_conf_p, "r") as f:
            test_conf = json.load(f)
        timeout = test_conf["timeout"]

        if not test_basedir.is_dir():
            notify.error(f"{str(test_basedir)} not a directory. It is possible that nobody has written a testcase yet ")
            return
        testsets = list()
        if "default" in testset_opt:
            testsets.append(DefaultTestSet(labID, problemID))
        if "random" in testset_opt:
            import sys
            sys.path.insert(1, str(test_basedir))
            try:
                from random_test import RandomTestSet # type: ignore
            except Exception:
                notify.error(f"random_test.* not found under {str(test_basedir)}")
                return
            testsets.append(RandomTestSet(labID, problemID))
        exec_p = Path(args.EXEC)
        if not args.match:
            for testset in testsets:
                print(f"Testing in testset {testset.name}")
                for casename, unit_case, verifier in testset:
                    try:
                        start_time = time.time()
                        complete_ps = subprocess.run(f"{exec_p.absolute()}", text=True,
                                   capture_output=True, timeout=timeout)
                        finish_time = time.time()
                    except subprocess.TimeoutExpired:
                        pass
                    except subprocess.CalledProcessError:
                        pass
        else:
            pass

def main(args):
    Test(args).begin()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="test [-h] [-rRl] [-m SID] EXEC",
        prog="test",
        description="A simple tool for test cpp codes.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-r", "--random", action="store_true", help="random test")
    parser.add_argument(
        "-R", "--Random", action="store_true", help="random test and default test"
    )
    parser.add_argument("-m", "--match", metavar="SID", help="matching test with another")
    parser.add_argument(
        "-l", "--list-available", action="store_true", help="list available executables"
    )
    parser.add_argument("EXEC", help="the executable to be tests")

    main(parser.parse_args())
