# Test Matrix Generation

This directory contains the test matrix generation system for GitHub Actions CI, which uses a configuration-driven approach to define and generate test matrices.

## Overview

The test matrix generation system consists of:

- **`test-matrix-config.json`** - Defines all modules and their test configurations
- **`generate-test-matrices.py`** - Python script that generates matrices based on configuration
- **Workflow** - Calls the script with changed module flags to determine which tests to run

## Configuration File Structure

```json
{
  "modules": {
    "module-name": {
      "type": "core" | "leaf",
      "change_filter": "module_name_changed",  // for leaf modules
      "dependencies": ["other_module_changed"],  // optional
      "test_combinations": [
        {"database": "H2", "jdk": 17},
        {"database": "DB2", "jdk": 21}
      ]
    }
  }
}
```

### Fields

- **type**:
  - `core` - Always tested when core modules change
  - `leaf` - Only tested when specifically changed
- **change_filter**: The GitHub Actions output name to check (leaf modules only)
- **dependencies**: Other modules that trigger testing of this module (optional)
- **test_combinations**: Array of database+JDK combinations to test

## How to Add a New Module

1. Edit `ci/test-matrix-config.json`
2. Add your module configuration:
   ```json
   "my-new-module": {
     "type": "leaf",
     "change_filter": "my_new_module_changed",
     "test_combinations": [
       {"database": "H2", "jdk": 17}
     ]
   }
   ```
3. If it's a leaf module, add the change filter to `.github/workflows/continuous-integration.yml` in the `detect_changes` job

## How to Modify Test Configurations

### Add a new database for a module
```json
"kadai-core": {
  "type": "core",
  "test_combinations": [
    {"database": "H2", "jdk": 17},
    {"database": "POSTGRES", "jdk": 17},
    {"database": "DB2", "jdk": 17}, // Add DB2
  ]
}
```

### Add JDK 21 testing for a module
```json
"my-module": {
  "type": "core",
  "test_combinations": [
    {"database": "H2", "jdk": 17},
    {"database": "H2", "jdk": 21}  // Add JDK 21
  ]
}
```

## Testing the Script Locally

```bash
# Test with core modules changed (full suite)
./ci/generate-test-matrices.py core_modules_changed=true

# Test with specific leaf modules changed
./ci/generate-test-matrices.py \
  core_modules_changed=false \
  kadai_spring_example_changed=true \
  kadai_routing_rest_changed=true

# Output shows both compact JSON (for GitHub Actions) and pretty-printed (for debugging)
```
