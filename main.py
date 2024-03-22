import os
import subprocess
import json
from colorama import init, Fore

# Initialize colorama for cross-platform terminal coloring
init()

# Define constants
TESTS_JSON_FILE_NAME = "student_tests.json"
STDOUT = 0
STDERR = 1

# Maximal virtual memory for subprocesses (in bytes).
MAX_VIRTUAL_MEMORY = os.environ.get('LOCAL_GRADESCOPE_MEM_LIMIT', '1048576')  # 1 MB
TIMEOUT = int(os.environ.get('LOCAL_GRADESCOPE_TIMEOUT', '1'))  # 1 second


def print_divider():
    print(f"\n{Fore.CYAN}------------------------------------------------------------{Fore.RESET}\n")


def normalize_newlines(txt):
    return txt.replace('\r\n', '\n').replace('\r', '\n')


def print_tests_summary(failed_count):
    print_divider()
    if failed_count == 0:
        print(f"\n{Fore.GREEN}All Tests Passed! {Fore.RESET}\n")
    else:
        print(
            f"{Fore.RED}{failed_count} {'Test' if failed_count == 1 else 'Tests'} Failed!{Fore.RESET}\n\n"
        )


def print_failed_test(test_name, expected_output, actual_output):
    print(f"\n{Fore.RED}{test_name} - Failed!{Fore.RESET}\n")
    print(f"{Fore.BLUE}Expected Output:\n{Fore.RESET}{expected_output}\n")
    print(f"{Fore.BLUE}Actual Output:\n{Fore.RESET}{actual_output}\n")


def run_test(executable_path, test):
    name = test["name"]
    input_data = test["input"].encode()
    output_data = normalize_newlines(test["output"])

    actual_output = ''
    try:
        proc = subprocess.Popen(executable_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            result = proc.communicate(input=input_data, timeout=TIMEOUT)[STDOUT]
        except subprocess.TimeoutExpired:
            proc.kill()
            result = proc.communicate()
            # Try using stderr or fallback to stdout
            result = result[STDERR] if result[STDERR] else result[STDOUT]
        actual_output = normalize_newlines(result.decode('utf-8'))
    except subprocess.CalledProcessError as e:
        print("Error running command:", e)
        return False
    except subprocess.TimeoutExpired as e:
        print_failed_test(name, output_data, e.stderr)
    except Exception as e:
        print_failed_test(name, output_data, e)

    print_divider()
    if actual_output == output_data:
        print(f"\n{Fore.GREEN}{name} - Passed! {Fore.RESET}\n")
        return True
    else:
        print_failed_test(name, output_data, actual_output)
        return False


def get_all_tests_from_json(workdir):
    tests_file_path = os.path.join(workdir, TESTS_JSON_FILE_NAME)
    try:
        with open(tests_file_path, "r", encoding='utf-8') as file:
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
            f"Bad Usage of local tester, make sure project folder and name are passed properly. Total args passed: {len(sys.argv)}"
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
