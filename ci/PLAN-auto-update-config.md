# Plan: Automated Test Matrix Configuration Update Script

## Overview

Create a Python script to automatically update `test-matrix-config.json` by analyzing the Maven project structure to:
1. Determine module types (core vs leaf) based on dependency relationships
2. Extract inter-module dependencies
3. Maintain or suggest test combinations

## Problem Analysis

**Current Issues:**
- Manual type declaration prone to errors (core/leaf classification)
- Dependencies field only used once, possibly missing other important relationships
- No automated way to keep config in sync with Maven project structure

**Key Insights:**
- **Core modules**: Libraries that are dependencies of other modules (e.g., kadai-common, kadai-core, kadai-spring)
- **Leaf modules**: Applications/examples that depend on core modules but aren't dependencies themselves (e.g., kadai-spring-example, kadai-rest-spring-example-boot)
- Maven has complete dependency information via `mvnw dependency:*` commands

## Solution Design

### Script: `update-test-matrix-config.py`

#### Phase 1: Discover All Modules

**Approach:**
```python
# Use Maven wrapper to discover all reactor modules
./mvnw help:evaluate -Dexpression=project.modules -q -DforceStdout

# Recursively discover submodules from parent POMs
# Build a complete list of all kadai-* artifacts
```

**Maven Command:**
```bash
# Get all modules in reactor build
./mvnw -q exec:exec -Dexec.executable=echo -Dexec.args='${project.artifactId}'
```

**Alternative (more reliable):**
```bash
# Parse pom.xml files directly with Python's xml.etree.ElementTree
# Extract <artifactId> from each pom.xml
```

#### Phase 2: Build Dependency Graph

**Approach:**
For each discovered module, extract its dependencies on other kadai modules:

```bash
# Get dependencies for a specific module (compile + runtime scope only)
./mvnw dependency:list \
    -pl <module-path> \
    -DincludeGroupIds=io.kadai \
    -DexcludeTransitive=true \
    -DincludeScope=compile,runtime \
    -q
```

**Data Structure:**
```python
{
    "kadai-core": {
        "depends_on": ["kadai-common-logging", "kadai-common"],
        "depended_by": ["kadai-spring", "kadai-test-api", ...]
    },
    ...
}
```

#### Phase 3: Classify Module Types

**Algorithm:**
```python
def classify_module(module_name, dependency_graph):
    # Core module: Has other modules depending on it (is in someone's depends_on list)
    # Leaf module: Not depended upon by any other module

    is_depended_upon = any(
        module_name in graph["depends_on"]
        for graph in dependency_graph.values()
    )

    # Additional heuristics:
    # - Modules with "example" in name are usually leaf
    # - Modules ending in "-test" that aren't depended upon are leaf
    # - Modules in specific directories (routing/, history/ SPIs) are often leaf

    return "core" if is_depended_upon else "leaf"
```

**Special Cases:**
- `kadai-rest-spring-example-common`: Has "example" but is depended upon by `-boot` → **core**
- `kadai-common-test`: Test utility but is depended upon → **core**
- `kadai-test-api`: API module depended upon → **core**

#### Phase 4: Extract Dependencies for Leaf Modules

**Approach:**
```python
def get_leaf_module_dependencies(module_name, dependency_graph):
    # For leaf modules, find which other leaf modules it depends on
    # This is used for the "dependencies" field in the config

    deps = dependency_graph[module_name]["depends_on"]
    leaf_deps = [d for d in deps if classify_module(d) == "leaf"]

    # Convert to change_filter format
    return [to_change_filter_name(d) for d in leaf_deps]
```

**Example:**
- `kadai-rest-spring-example-boot` depends on `kadai-spi-routing-dmn-router` and `kadai-routing-rest`
- Both are leaf modules
- Dependencies: `["kadai_spi_routing_dmn_router_changed", "kadai_routing_rest_changed"]`

#### Phase 5: Preserve Test Combinations

**Approach:**
```python
def merge_test_combinations(existing_config, new_module_data):
    # If module exists in current config, preserve test_combinations
    if module_name in existing_config["modules"]:
        return existing_config["modules"][module_name]["test_combinations"]

    # Otherwise, use sensible defaults
    return [{"database": "H2", "jdk": 17}]
```

**Rationale:** Test combinations are intentionally configured based on what each module needs to test (database compatibility, JDK versions). This should be preserved.

#### Phase 6: Generate Updated Config

**Output Format:**
```json
{
  "modules": {
    "kadai-common": {
      "type": "core",
      "test_combinations": [...]
    },
    "kadai-spring-example": {
      "type": "leaf",
      "change_filter": "kadai_spring_example_changed",
      "test_combinations": [...]
    },
    "kadai-rest-spring-example-boot": {
      "type": "leaf",
      "change_filter": "kadai_rest_spring_example_boot_changed",
      "dependencies": [
        "kadai_spi_routing_dmn_router_changed",
        "kadai_routing_rest_changed"
      ],
      "test_combinations": [...]
    }
  }
}
```

## Implementation Details

### Technology Choices

**Language:** Python 3
- Already used by `generate-test-matrices.py`
- Good XML parsing libraries (`xml.etree.ElementTree`)
- JSON manipulation built-in
- Subprocess for running mvnw commands

### Script Structure

```python
#!/usr/bin/env python3
"""
Automatically update test-matrix-config.json based on Maven project structure.
"""

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set

def discover_all_modules() -> List[str]:
    """Discover all kadai modules from pom.xml files."""
    pass

def get_module_dependencies(module: str) -> List[str]:
    """Get kadai dependencies for a specific module using mvnw."""
    pass

def build_dependency_graph(modules: List[str]) -> Dict:
    """Build complete dependency graph."""
    pass

def classify_module_type(module: str, graph: Dict) -> str:
    """Determine if module is 'core' or 'leaf'."""
    pass

def get_leaf_dependencies(module: str, graph: Dict) -> List[str]:
    """Get leaf module dependencies for a leaf module."""
    pass

def module_name_to_change_filter(module: str) -> str:
    """Convert module name to change_filter format."""
    # kadai-spring-example -> kadai_spring_example_changed
    pass

def load_existing_config() -> Dict:
    """Load current test-matrix-config.json."""
    pass

def generate_updated_config(graph: Dict, existing: Dict) -> Dict:
    """Generate new config preserving test_combinations."""
    pass

def main():
    """Main execution."""
    print("Discovering modules...")
    modules = discover_all_modules()

    print(f"Found {len(modules)} modules")
    print("Building dependency graph...")
    graph = build_dependency_graph(modules)

    print("Loading existing config...")
    existing = load_existing_config()

    print("Generating updated config...")
    new_config = generate_updated_config(graph, existing)

    # Write updated config
    config_path = Path(__file__).parent / "test-matrix-config.json"
    with open(config_path, 'w') as f:
        json.dump(new_config, f, indent=2)

    print(f"Updated {config_path}")

    # Print summary
    print("\nSummary:")
    print(f"  Core modules: {sum(1 for m in new_config['modules'].values() if m['type'] == 'core')}")
    print(f"  Leaf modules: {sum(1 for m in new_config['modules'].values() if m['type'] == 'leaf')}")
    print(f"  Modules with dependencies: {sum(1 for m in new_config['modules'].values() if 'dependencies' in m)}")

if __name__ == "__main__":
    main()
```

### Maven Command Reference

```bash
# Discover modules (from parent POM)
./mvnw help:evaluate -Dexpression=project.modules -q -DforceStdout

# Get module's kadai dependencies (non-transitive, compile/runtime only)
./mvnw dependency:list \
    -pl <module-path> \
    -DincludeGroupIds=io.kadai \
    -DexcludeTransitive=true \
    -DincludeScope=compile,runtime \
    -q -DforceStdout

# Alternative: dependency:tree for hierarchy
./mvnw dependency:tree \
    -pl <module-path> \
    -DincludeGroupIds=io.kadai \
    -q

# Get module location (for -pl parameter)
# Need to discover relative path from root POM
```

### Handling Maven Module Paths

Maven's `-pl` (project list) parameter requires module paths relative to root:
- `lib/kadai-core`
- `rest/kadai-rest-spring`
- `routing/kadai-routing-rest`

**Discovery Strategy:**
```python
def find_module_path(module_name: str, root_dir: Path) -> str:
    """Find relative path to module's pom.xml from root."""
    for pom in root_dir.rglob("pom.xml"):
        tree = ET.parse(pom)
        root = tree.getroot()
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        artifactId = root.find(".//mvn:artifactId", ns)
        if artifactId is not None and artifactId.text == module_name:
            return str(pom.parent.relative_to(root_dir))
    return None
```

## Edge Cases and Considerations

### 1. Circular Dependencies
- Maven doesn't allow circular dependencies
- Not an issue for this project

### 2. Test-scoped Dependencies
- Exclude test-scoped dependencies from graph
- Use `-DincludeScope=compile,runtime`
- Modules like `kadai-common-test` used with scope=test shouldn't count for core/leaf classification

### 3. External Dependencies
- Focus only on `io.kadai` group
- Use `-DincludeGroupIds=io.kadai`

### 4. Modules Not in Test Matrix
- Some modules may not need testing (parent POMs, aggregators)
- Filter to only modules with actual code:
  ```python
  def should_include_module(module_path: Path) -> bool:
      # Check if has src/main or src/test directories
      return (module_path / "src").exists()
  ```

### 5. Change Filter Generation
- Leaf modules need `change_filter` field
- Format: `{module_name}_changed`
- Must match what GitHub Actions workflow generates

## Validation

After generating new config, the script should:

1. **Validate JSON structure**
   - Required fields present for each module
   - Valid enum values for type/database/jdk

2. **Compare with existing**
   - Report modules added/removed
   - Report type changes (core ↔ leaf)
   - Report dependency changes

3. **Sanity checks**
   - Core modules shouldn't have `change_filter`
   - Leaf modules must have `change_filter`
   - Dependencies should only reference other leaf modules
   - All referenced modules exist

## Usage

```bash
# Run script to update config
./ci/update-test-matrix-config.py

# Dry-run mode (show changes without writing)
./ci/update-test-matrix-config.py --dry-run

# Show diff with current config
./ci/update-test-matrix-config.py --diff
```

## Future Enhancements

### 1. Suggest Test Combinations
Analyze module characteristics to suggest database/JDK combinations:
- Modules using database (mybatis) → test multiple databases
- Spring modules → might need different JDKs
- Parse pom.xml for database-related dependencies

### 2. Detect Removed Modules
- Modules in config but not in Maven → mark for removal
- Confirm with user before deleting

### 3. GitHub Actions Integration
- Run script in CI to detect drift
- Fail if config is out of sync with Maven structure
- Post PR comment with suggested changes

## Testing Strategy

1. **Unit tests** for individual functions
   - Module discovery
   - Dependency parsing
   - Classification algorithm

2. **Integration test** with current project
   - Run against actual kadai project
   - Compare output with hand-curated config
   - Ensure no regression

3. **Edge case tests**
   - Empty dependencies
   - Module with only test dependencies
   - Deeply nested module paths

## Rollout Plan

1. **Phase 1:** Create script with read-only mode
   - Generate config but don't overwrite
   - Manually review differences

2. **Phase 2:** Validate on current config
   - Run script and compare with manual config
   - Fix any discrepancies in logic

3. **Phase 3:** Use for updates
   - Update config using script
   - Manual review of test_combinations changes

4. **Phase 4:** CI integration
   - Add check to prevent drift
   - Auto-generate config on module additions

## Expected Benefits

- **Accuracy:** Automatic detection eliminates human error in type classification
- **Completeness:** All module dependencies properly captured
- **Maintainability:** Adding new modules becomes automatic
- **Documentation:** Dependency graph provides project overview
- **CI Efficiency:** Ensures test matrix stays optimal as project evolves
