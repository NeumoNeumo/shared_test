from pathlib import Path
import json
import argparse
import subprocess

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
        Returns: (unit_case, verifier)
            unit_case (string): directed to stdin of the tested program
            verifier (string|Callable[[string], bool]) : either a string used to
                match the stdout or a function to verify whether the output is
                reasonable (usually used when the problem has multiple
                solutions)
        """
        raise NotImplementedError()


class DefaultTestSet(TestSet):
    """get test data from given fils in <labID>/test/<problemID>/<testcaseID>"""

    def __init__(self, labID, problemID):
        super().__init__("Default", labID, problemID)
        self.data_dir = Path().cwd() / labID / "test" / problemID


class Info:
    _RST = "\033[0m"
    _RED = "\033[1;31m"
    _YEL = "\033[1;33m"

    @staticmethod
    def warn(txt):
        print(Info._YEL + "Warn: " + Info._RST + txt)

    @staticmethod
    def error(txt):
        print(Info._RED + "Error: " + Info._RST + txt)

def main(args):
    conf_p = Path("test.conf")
    if not conf_p.is_file():
        print("lala")
        Info.warn("Config file not found.")
        yn = input("Confirm to init config? (Y/n)")
        if yn == "n" or yn == "N" or yn == "NO" or yn == "No":
            return
        elif yn == "y" or yn == "Y" or yn == "YES" or yn == "Yes" or yn == "":
            labID = input("Please input your labID (lab**): ")
            problemID = input("Please input your problemID (lowercase single letter): ")
            with open(conf_p, "w") as f:
                f.write('{"labID":%s,"problemID":%s}'.format(labID, problemID))
        else:
            Info.error("Invalid option")
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

    test_basedir = Path.cwd()/labID/"test"/problemID
    if not test_basedir.is_dir():
        Info.error(f"{str(test_basedir)} not a directory. It is possible that nobody has written a testcase yet ")
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
            Info.error(f"random_test.* not found under {str(test_basedir)}")
            return
        testsets.append(RandomTestSet(labID, problemID))
    if not args.match:
        for testset in testsets:
            print(f"Testing in testset {testset.name}")
            for unit_case, verifier in testset:
                subprocess.run()
    else:
        pass
        

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
