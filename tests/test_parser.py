import os
import pandas as pd
import argparse
import importlib.util
import sys

def run_validation(parser_path: str, pdf_path: str, output_path: str):
    print("--- Starting validation ---")
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    module_name = "custom_parser"
    spec = importlib.util.spec_from_file_location(module_name, parser_path)
    if spec is None:
        raise ImportError(f"Could not load spec from {parser_path}")
    
    parser_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = parser_module
    spec.loader.exec_module(parser_module)
    print(f"Successfully imported `parse` function from {parser_path}")

    # Execute the generated parser's main function
    parser_module.parse(pdf_path, output_path)
    print(f"Parser executed. Verifying output at {output_path}")

    # Validate that the output file was created and is not empty
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Output file was not created at {output_path}")

    if os.path.getsize(output_path) == 0:
        raise ValueError(f"Output file at {output_path} is empty.")

    df = pd.read_csv(output_path)
    if df.empty:
        raise ValueError(f"Output CSV at {output_path} is empty after reading.")
    
    print(f"Validation successful. Output file created and contains data.")
    print(f"Output DataFrame shape: {df.shape}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validation script for generated parsers.")
    parser.add_argument("--parser_path", type=str, required=True)
    parser.add_argument("--pdf_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()

    run_validation(args.parser_path, args.pdf_path, args.output_path)