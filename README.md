# Rainmeas Package Registry

This repository contains the official package registry for Rainmeas, a package manager for Rainmeter modules.

## Structure

- `packages/` - Contains JSON files describing each package
- `index.json` - Index of all available packages
- `.github/workflows/` - GitHub Actions for automated validation

## Package Format

Each package is defined in a JSON file in the `packages/` directory. The format includes:

```json
{
  "name": "package-name",
  "author": "Author Name",
  "description": "Package description",
  "homepage": "https://example.com",
  "license": "License Name",
  "versions": {
    "1.0.0": {
      "download": "https://example.com/package-1.0.0.zip"
    },
    "latest": "1.0.0"
  }
}
```

## Adding New Packages

To add a new package:

1. Create a new JSON file in the `packages/` directory
2. Add an entry for the package in `index.json`
3. Submit a pull request

The GitHub Actions workflow will automatically validate:
- Package JSON structure
- Download URL accessibility
- Index consistency

## Automated Validation

All pull requests are automatically validated by GitHub Actions to ensure:
- All required fields are present
- Download URLs are accessible
- Index.json is consistent with package files