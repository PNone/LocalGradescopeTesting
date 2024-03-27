import sys
from os import environ, path
import subprocess
import json
from colorama import init, Fore, ansi

# Initialize colorama for cross-platform terminal coloring
init()

# Define constants
TESTS_JSON_FILE_NAME = "student_tests.json"
STDOUT = 0
STDERR = 1
WORKDIR_INDEX = 1
EXEC_PATH_INDEX = 2
EXPECTED_ARGS_AMOUNT = 3

TIMEOUT = int(environ.get('LOCAL_GRADESCOPE_TIMEOUT', '1'))  # 1 second


def normalize_newlines(txt: str) -> str:
    return txt.replace('\r\n', '\n').replace('\r', '\n')


def print_divider() -> None:
    print(f"\n{Fore.CYAN}------------------------------------------------------------{Fore.RESET}\n")


def print_colored_test(color: ansi.AnsiFore | str, text: str, before_text: str, after_text: str) -> None:
    print(
        f"{before_text}{color}{text}{Fore.RESET}{after_text}"
    )


def print_tests_summary(failed_count: int) -> None:
    print_divider()
    if failed_count == 0:
        print_colored_test(Fore.GREEN, "All Tests Passed! ", "\n", "\n")
    else:
        text = f"{failed_count} {'Test' if failed_count == 1 else 'Tests'} Failed!"
        print_colored_test(Fore.RED, text, "", "\n\n")


def print_failed_test(test_name: str, expected_output: str, actual_output: str) -> None:
    print_colored_test(Fore.RED, f"{test_name} - Failed!", "\n", "\n")
    print_colored_test(Fore.BLUE, "Expected Output:", "", "\n")
    print(f"{expected_output}\n")
    print_colored_test(Fore.BLUE, "Actual Output:", "", "\n")
    print(f"{actual_output}\n")


def print_failed_test_due_to_exception(test_name: str, expected_output: str, exception: str) -> None:
    print_colored_test(Fore.RED, f"{test_name} - Failed due to an error in the tester!", "\n", "\n")
    print_colored_test(Fore.BLUE, "Expected Output:", "", "\n")
    print(f"{expected_output}\n")
    print_colored_test(Fore.BLUE, "Error:", "", "\n")
    print(f"{exception}\n")


def run_test(executable_path: str, test: dict[str, str]) -> bool:
    name = test["name"]
    input_data = test["input"].encode()
    output_data = normalize_newlines(test["output"])
    print_divider()

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
        try:
            actual_output = normalize_newlines(result.decode('utf-8'))
        except UnicodeDecodeError:
            actual_output = normalize_newlines(result.decode('windows-1252'))

    except subprocess.CalledProcessError as e:
        print_failed_test_due_to_exception(name, output_data, e.stderr if e.stderr else e.stdout)
        return False
    except subprocess.TimeoutExpired as e:
        print_failed_test_due_to_exception(name, output_data, str(e.stderr) if e.stderr else e.stdout)
        return False
    except Exception as e:
        print_failed_test_due_to_exception(name, output_data, str(e))
        return False

    if actual_output == output_data:
        print_colored_test(Fore.GREEN, f"{name} - Passed! ", "\n", "\n")
        return True
    else:
        print_failed_test(name, output_data, actual_output)
        return False


def get_all_tests_from_json(workdir: str) -> list[dict[str, str]] | None:
    tests_file_path = path.join(workdir, TESTS_JSON_FILE_NAME)
    try:
        with open(tests_file_path, "r", encoding='utf-8') as file:
            json_data = json.load(file)
            return json_data["tests"]
    except (IOError, json.JSONDecodeError) as e:
        print_colored_test(Fore.RED, f"Error reading JSON file: {e}", "", "")
        return None
    except Exception as e:
        print_colored_test(Fore.RED, f"Unexpected error reading JSON file: {e}", "", "")
        return None


def main():
    # Expect 3 args: script name, workdir, executable path
    if len(sys.argv) != EXPECTED_ARGS_AMOUNT:
        print(
            f"Bad Usage of local tester, make sure project folder and name are passed properly." +
            f" Total args passed: {len(sys.argv)}"
        )
        return

    failed_count = 0
    workdir = sys.argv[WORKDIR_INDEX]
    executable_path = sys.argv[EXEC_PATH_INDEX]
    tests = get_all_tests_from_json(workdir)
    if tests is None:
        return

    for test in tests:
        if not run_test(executable_path, test):
            failed_count += 1

    print_tests_summary(failed_count)


if __name__ == "__main__":
    main()
