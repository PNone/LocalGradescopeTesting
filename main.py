import os
import subprocess
import json
import psutil


# Define constants
TESTS_JSON_FILE_NAME = "student_tests.json"


# Maximal virtual memory for subprocesses (in bytes).
MAX_VIRTUAL_MEMORY = os.environ.get('LOCAL_GRADESCOPE_MEM_LIMIT', '1048576') # 1 MB


def print_divider():
    print("\n\033[0;36m------------------------------------------------------------\033[0m\n")


def print_tests_summary(failed_count):
    print_divider()
    if failed_count == 0:
        print("\n\033[1;32mAll Tests Passed! \033[0m\n")
    else:
        print(
            "\n\033[1;31m{} {} Failed!\033[0m\n\n".format(
                failed_count, "Test" if failed_count == 1 else "Tests"
            )
        )


def print_failed_test(test_name, expected_output, actual_output):
    print("\n\033[1;31m{} - Failed!\033[0m\n".format(test_name))
    print("\033[1;34mExpected Output: \033[0m")
    print(expected_output)
    print("\033[1;34mActual Output: \033[0m")
    print(actual_output)


def run_test(executable_path, test):
    name = test["name"]
    input_data = test["input"]
    output_data = test["output"]

    timeout = os.environ.get('LOCAL_GRADESCOPE_TIMEOUT', '4')
    timeout = int(timeout)

    command_str = "{0}".format(
        executable_path
    )
    actual_output = ''
    try:
        # Set memory limit
        psutil.Process().rlimit(psutil.RLIMIT_AS, (MAX_VIRTUAL_MEMORY, MAX_VIRTUAL_MEMORY))

        result = subprocess.run(command_str, input=input_data, shell=True, check=True, stdout=subprocess.PIPE,
                                timeout=timeout)
        actual_output = result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print("Error running command:", e)
        return False
    except subprocess.TimeoutExpired as e:
        print_failed_test(name, output_data, e.stderr)
    except Exception as e:
        print_failed_test(name, output_data, e)

    print_divider()
    if actual_output == output_data:
        print("\n\033[1;32m{} - Passed! \033[0m\n".format(name))
        return True
    else:
        print_failed_test(name, output_data, actual_output)
        return False


def get_all_tests_from_json(workdir):
    tests_file_path = os.path.join(workdir, TESTS_JSON_FILE_NAME)
    try:
        with open(tests_file_path, "r") as file:
            json_data = json.load(file)
            return json_data["tests"]
    except (IOError, json.JSONDecodeError) as e:
        print("Error reading JSON file:", e)
        return None


def main():
    import sys

    # Expect 3 args: script name, workdir, executable path
    if len(sys.argv) != 3:
        print(
            "Bad Usage of local tester, make sure project folder and name are passed properly. Total args passed: {}".format(
                len(sys.argv)
            )
        )
        return

    failed_count = 0
    workdir = sys.argv[1]
    executable_path = sys.argv[2]
    tests = get_all_tests_from_json(workdir)
    if tests is None:
        return

    for test in tests:
        if not run_test(executable_path, test):
            failed_count += 1

    print_tests_summary(failed_count)


if __name__ == "__main__":
    main()
