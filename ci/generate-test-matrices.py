#!/usr/bin/env python3
"""
Generate test matrices for GitHub Actions based on module changes.
"""

import json
import sys
from pathlib import Path


def load_config():
    """Load the test matrix configuration."""
    config_path = Path(__file__).parent / "test-matrix-config.json"
    with open(config_path) as f:
        return json.load(f)


def parse_changed_modules(args):
    """Parse command-line arguments for changed module flags."""
    changed = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            changed[key] = value.lower() == "true"
    return changed


def generate_matrices(config, changed_modules):
    """Generate test matrices based on configuration and changed modules."""
    matrix_17 = {"include": []}
    matrix_21 = {"include": []}

    core_changed = changed_modules.get("core_modules_changed", False)

    for module_name, module_config in config["modules"].items():
        module_type = module_config["type"]
        should_test = False

        if core_changed:
            # Run all tests when core modules changed
            should_test = True
        elif module_type == "leaf":
            # For leaf modules, check if the specific module changed
            change_filter = module_config.get("change_filter")
            if change_filter and changed_modules.get(change_filter, False):
                should_test = True

            # Check dependencies
            dependencies = module_config.get("dependencies", [])
            for dep in dependencies:
                if changed_modules.get(dep, False):
                    should_test = True
                    break

        if should_test:
            # Add all test combinations for this module
            for combo in module_config["test_combinations"]:
                test_config = {"module": module_name, "database": combo["database"]}
                jdk = combo["jdk"]

                if jdk == 17:
                    matrix_17["include"].append(test_config)
                elif jdk == 21:
                    matrix_21["include"].append(test_config)

    return matrix_17, matrix_21


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: generate-test-matrices.py key=value [key=value ...]", file=sys.stderr)
        print("Example: generate-test-matrices.py core_modules_changed=true", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    changed_modules = parse_changed_modules(sys.argv[1:])

    matrix_17, matrix_21 = generate_matrices(config, changed_modules)

    # Output in compact JSON format (single line)
    print(f"matrix_17={json.dumps(matrix_17, separators=(',', ':'))}")
    print(f"matrix_21={json.dumps(matrix_21, separators=(',', ':'))}")

    # Pretty print for debugging (to stderr)
    print("\n=== JDK 17 Matrix ===", file=sys.stderr)
    print(json.dumps(matrix_17, indent=2), file=sys.stderr)
    print("\n=== JDK 21 Matrix ===", file=sys.stderr)
    print(json.dumps(matrix_21, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
