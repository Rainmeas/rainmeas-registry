#!/usr/bin/env python3
"""
Validate package registry entries for the rainmeas project.
This script checks that:
1. All packages in the packages/ directory are referenced in index.json
2. All packages referenced in index.json have corresponding files in packages/
3. All version download URLs are valid and accessible
4. Package JSON structure is valid
5. Index.json is consistent with package files
"""

import json
import os
import sys
import requests
from pathlib import Path

# Constants
PACKAGES_DIR = "packages"
INDEX_FILE = "index.json"
TIMEOUT = 10  # seconds


def load_json_file(filepath):
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {filepath}: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        return None
    except Exception as e:
        print(f"❌ Error: Failed to read {filepath}: {e}")
        return None


def validate_package_structure(package_name, package_data):
    """Validate the structure of a package definition."""
    required_fields = ["name", "author", "description", "versions"]
    errors = []
    
    # Check required top-level fields
    for field in required_fields:
        if field not in package_data:
            errors.append(f"Missing required field: {field}")
    
    # Check that name matches filename
    if package_data.get("name") != package_name:
        errors.append(f"Package name '{package_data.get('name')}' doesn't match filename '{package_name}'")
    
    # Check versions structure
    if "versions" in package_data:
        versions = package_data["versions"]
        if not isinstance(versions, dict):
            errors.append("Versions must be an object")
        else:
            # Check that latest version exists
            if "latest" in versions:
                latest = versions["latest"]
                if latest not in versions:
                    errors.append(f"Latest version '{latest}' not found in versions")
            else:
                errors.append("Missing 'latest' field in versions")
    
    return errors


def validate_version_download_url(version, download_url):
    """Validate that a download URL is accessible."""
    try:
        # Make a HEAD request to check if URL is accessible
        response = requests.head(download_url, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return True, ""
        elif response.status_code == 404:
            return False, f"URL not found (404) for version {version}"
        else:
            return False, f"HTTP {response.status_code} for version {version}"
    except requests.exceptions.Timeout:
        return False, f"Timeout when checking download URL for version {version}"
    except requests.exceptions.RequestException as e:
        return False, f"Error checking download URL for version {version}: {e}"


def validate_package_versions(package_name, package_data):
    """Validate all versions of a package."""
    errors = []
    warnings = []
    
    if "versions" not in package_data:
        errors.append("Missing versions data")
        return errors, warnings
    
    versions = package_data["versions"]
    
    # Skip the structural fields
    version_keys = [k for k in versions.keys() if k not in ["latest"]]
    
    for version in version_keys:
        version_data = versions[version]
        
        # For version entries that are objects
        if isinstance(version_data, dict):
            if "download" not in version_data:
                errors.append(f"Version {version} missing download URL")
                continue
            
            download_url = version_data["download"]
            
            # Validate download URL
            is_valid, message = validate_version_download_url(version, download_url)
            if not is_valid:
                errors.append(f"Invalid download URL for {package_name}@{version}: {message}")
            else:
                print(f"✅ Valid download URL for {package_name}@{version}")
        else:
            warnings.append(f"Version {version} is not an object (might be legacy format)")
    
    return errors, warnings


def validate_index_consistency(index_data, package_files):
    """Validate that index.json is consistent with package files."""
    errors = []
    
    # Check that all packages in index.json have corresponding files
    for package_name in index_data.keys():
        expected_file = f"{package_name}.json"
        if expected_file not in package_files:
            errors.append(f"Package '{package_name}' in index.json but no corresponding file in packages/")
    
    # Check that all package files are referenced in index.json
    package_names_in_index = set(index_data.keys())
    for package_file in package_files:
        package_name = package_file.replace(".json", "")
        if package_name not in package_names_in_index:
            errors.append(f"Package file '{package_file}' not referenced in index.json")
    
    return errors


def main():
    """Main validation function."""
    print("🔍 Validating rainmeas package registry...\n")
    
    # Track overall status
    total_errors = 0
    total_warnings = 0
    
    # Load index.json
    print("📄 Checking index.json...")
    index_path = INDEX_FILE
    index_data = load_json_file(index_path)
    if index_data is None:
        print("❌ Failed to load index.json")
        return 1
    
    print("✅ Loaded index.json successfully\n")
    
    # Get list of package files
    if not os.path.exists(PACKAGES_DIR):
        print(f"❌ Packages directory '{PACKAGES_DIR}' not found")
        return 1
    
    package_files = [f for f in os.listdir(PACKAGES_DIR) if f.endswith('.json')]
    print(f"📁 Found {len(package_files)} package files\n")
    
    # Validate index.json consistency
    print("🔗 Checking index.json consistency...")
    consistency_errors = validate_index_consistency(index_data, package_files)
    for error in consistency_errors:
        print(f"❌ {error}")
        total_errors += 1
    
    if not consistency_errors:
        print("✅ Index.json is consistent with package files")
    print()
    
    # Validate each package
    for package_file in package_files:
        package_name = package_file.replace(".json", "")
        print(f"📦 Validating package: {package_name}")
        
        # Load package file
        package_path = os.path.join(PACKAGES_DIR, package_file)
        package_data = load_json_file(package_path)
        if package_data is None:
            total_errors += 1
            print()
            continue
        
        # Validate package structure
        structure_errors = validate_package_structure(package_name, package_data)
        for error in structure_errors:
            print(f"❌ {error}")
            total_errors += 1
        
        if structure_errors:
            print()
            continue
        
        # Validate package versions
        version_errors, version_warnings = validate_package_versions(package_name, package_data)
        for error in version_errors:
            print(f"❌ {error}")
            total_errors += 1
        for warning in version_warnings:
            print(f"⚠️ {warning}")
            total_warnings += 1
        
        if not structure_errors and not version_errors and not version_warnings:
            print(f"✅ Package {package_name} is valid")
        
        print()
    
    # Summary
    print("=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")
    
    if total_errors > 0:
        print("\n❌ Validation failed!")
        return 1
    else:
        print("\n✅ All packages validated successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())