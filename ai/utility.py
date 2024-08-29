import re
import io
import subprocess
import contextlib

class Utility:
    @staticmethod
    def extract_code_block(message):
        code_block_match = re.search(r"```python(.*?)```", message, re.DOTALL)
        return code_block_match.group(1).strip() if code_block_match else None

    @staticmethod
    def execute_code(code, globals_dict, cleanup_func):
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                exec(code, globals_dict)
            return output.getvalue()
        finally:
            output.close()
            cleanup_func()

    @staticmethod
    def install_package(package_name):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError:
            return False

    # Additional utility methods can be added here as needed
