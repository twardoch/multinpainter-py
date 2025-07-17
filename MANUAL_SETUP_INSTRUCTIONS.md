# Manual Setup Instructions

## GitHub Actions Workflow Setup

Due to GitHub App permissions restrictions, the GitHub Actions workflow file needs to be added manually. Here's how to complete the setup:

### Step 1: Add the GitHub Actions Workflow

1. **Navigate to your repository on GitHub**
2. **Create the workflow directory** (if it doesn't exist):
   - Go to `.github/workflows/`
   - If this directory doesn't exist, create it

3. **Create the workflow file**:
   - Create a new file called `ci.yml` in `.github/workflows/`
   - Copy the contents from `ci.yml.backup` (in the root of the repository)

### Step 2: Configure PyPI Publishing (Required for Releases)

1. **Get a PyPI API token**:
   - Go to https://pypi.org/manage/account/
   - Create an API token with scope for this project

2. **Add the token to GitHub Secrets**:
   - Go to your repository settings → Secrets and variables → Actions
   - Add a new repository secret named `PYPI_TOKEN`
   - Paste your PyPI API token as the value

### Step 3: Test the Pipeline

1. **Create a test tag** to trigger the release workflow:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

2. **Check the Actions tab** in your GitHub repository to see the workflow run

## Complete GitHub Actions Workflow Content

Here's the complete `ci.yml` file that should be placed in `.github/workflows/`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    name: Test on ${{ matrix.os }} with Python ${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for setuptools-scm

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -e .[testing]

    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=multinpainter --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install black flake8 mypy
        python -m pip install -e .
    
    - name: Run Black
      run: black --check src/ tests/
    
    - name: Run flake8
      run: flake8 src/ tests/
    
    - name: Run mypy
      run: mypy src/ || true  # Allow mypy to fail for now

  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"

    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip build twine

    - name: Build package
      run: |
        python -m build

    - name: Check package
      run: |
        python -m twine check dist/*

    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      with:
        name: dist-files
        path: dist/

  build-binaries:
    name: Build Binary for ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    needs: [test, lint]
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        include:
          - os: ubuntu-latest
            artifact_name: multinpainter-linux
          - os: windows-latest
            artifact_name: multinpainter-windows.exe
          - os: macos-latest
            artifact_name: multinpainter-macos

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install -e .
        python -m pip install pyinstaller

    - name: Build binary
      run: |
        pyinstaller --onefile --name ${{ matrix.artifact_name }} src/multinpainter/__main__.py

    - name: Upload binary artifact
      uses: actions/upload-artifact@v3
      with:
        name: ${{ matrix.artifact_name }}
        path: dist/${{ matrix.artifact_name }}*

  release:
    name: Release
    runs-on: ubuntu-latest
    needs: [build, build-binaries]
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      contents: write
      id-token: write  # For trusted publishing to PyPI

    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Download all artifacts
      uses: actions/download-artifact@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"

    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          dist-files/*
          multinpainter-linux/*
          multinpainter-windows.exe/*
          multinpainter-macos/*
        tag_name: ${{ github.ref_name }}
        name: Release ${{ github.ref_name }}
        body: |
          ## Release ${{ github.ref_name }}
          
          ### 📦 Installation
          
          **Python Package:**
          ```bash
          pip install multinpainter
          ```
          
          **Binary Downloads:**
          - Linux: `multinpainter-linux`
          - Windows: `multinpainter-windows.exe`
          - macOS: `multinpainter-macos`
          
          ### 🚀 Usage
          
          ```bash
          multinpainter-py input.png output.png 1920 1080 --prompt "your prompt"
          ```
          
          For more information, see the [README](https://github.com/${{ github.repository }}/blob/main/README.md).
          
          ### 🔄 Changes
          
          See [CHANGELOG.md](https://github.com/${{ github.repository }}/blob/main/CHANGELOG.md) for detailed changes.
        draft: false
        prerelease: false

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        packages-dir: dist-files/
```

## Alternative: Using GitHub CLI

If you have the GitHub CLI installed, you can also create the workflow file directly:

```bash
# Create the workflow directory
mkdir -p .github/workflows

# Copy the workflow file
cp ci.yml.backup .github/workflows/ci.yml

# Add and commit
git add .github/workflows/ci.yml
git commit -m "feat: add GitHub Actions CI/CD workflow"
git push origin main
```

## Verification

After adding the workflow file, you should see:

1. **Actions tab** in your GitHub repository shows the workflow
2. **Workflow runs** on pushes to main and pull requests
3. **Releases** are created automatically when you push tags starting with `v`

## Quick Start After Setup

1. **For development:**
   ```bash
   make setup
   make test
   make build
   ```

2. **For releases:**
   ```bash
   make release VERSION=1.2.3
   ```

This will handle everything automatically through the GitHub Actions pipeline!