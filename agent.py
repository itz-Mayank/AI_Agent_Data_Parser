import os
import subprocess
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Error: GOOGLE_API_KEY not found. Please set it in your .env file.")
    exit(1)

class CodeGenAgent:
    def __init__(self, target_bank: str, max_attempts: int = 3):
        self.target_bank = target_bank
        self.max_attempts = max_attempts
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.parser_path = f"custom_parsers/{self.target_bank}_parser.py"
        self.test_path = "tests/test_parser.py"
        self.pdf_path = f"data/{self.target_bank}/{self.target_bank}_sample.pdf"
        self.output_path = "Output/output_1.csv"
        self.last_error = ""

    def run(self):
        for attempt in range(self.max_attempts):
            print(f"--- Attempt {attempt + 1} of {self.max_attempts} ---")

            if attempt == 0:
                self._generate_code()
            else:
                self._fix_code()

            test_passed, output = self._execute_and_validate()

            if test_passed:
                print("Success! Parser generated and executed successfully.")
                print(f"Parser located at: {self.parser_path}")
                print(f"Output saved to: {self.output_path}")
                return

            print(f"Execution failed on attempt {attempt + 1}.")
            self.last_error = output
            if attempt < self.max_attempts - 1:
                print("--- Attempting to fix the code... ---")

        print("--- Max attempts reached. Could not generate a working parser. ---")
        print(f"Final error:\n{self.last_error}")

    def _generate_code(self):
        print(f"--- Generating initial parser for {self.target_bank}... ---")
        prompt = f"""
        Write a Python script. It must contain a single function `parse(pdf_path: str, output_path: str)`.
        This function will use the `tabula-py` library to extract tabular data from the PDF file at `pdf_path`.
        It should perform necessary data cleaning and save the final pandas DataFrame to a CSV file at `output_path`.
        The script must include all necessary imports like `pandas` and `tabula`.
        Return only the complete, raw Python code for the file. Do not include explanations.
        """
        response = self.model.generate_content(prompt)
        self._write_code_to_file(response.text)

    def _fix_code(self):
        print(f"--- Fixing parser for {self.target_bank}... ---")
        with open(self.parser_path, "r") as f:
            current_code = f.read()

        prompt = f"""
        The following Python script failed to execute.

        Failed Code:
        ```python
        {current_code}
        ```

        Execution Error:
        ```
        {self.last_error}
        ```

        Task:
        Fix the code to resolve the error. The `parse` function must correctly process the PDF and save the output CSV without crashing.
        Return only the complete, corrected, raw Python code for the file. Do not include explanations.
        """
        response = self.model.generate_content(prompt)
        self._write_code_to_file(response.text)

    def _execute_and_validate(self):
        print("--- Executing and validating the generated parser... ---")
        command = [
            "python", self.test_path,
            "--parser_path", self.parser_path,
            "--pdf_path", self.pdf_path,
            "--output_path", self.output_path
        ]
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, encoding='utf-8'
            )
            print(result.stdout)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            error_output = f"STDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
            print(error_output)
            return False, error_output

    def _write_code_to_file(self, code_text: str):
        if "```python" in code_text:
            code_text = code_text.split("```python")[1].split("```")[0].strip()
        os.makedirs(os.path.dirname(self.parser_path), exist_ok=True)
        with open(self.parser_path, "w", encoding='utf-8') as f:
            f.write(code_text)
        print(f"--- Code written to {self.parser_path} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent for Bank Statement Parser Generation.")
    parser.add_argument("--target", type=str, required=True, help="The target bank (e.g., 'icici').")
    args = parser.parse_args()
    agent = CodeGenAgent(target_bank=args.target)
    agent.run()