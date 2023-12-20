<img src="https://github.com/alagyn/DiamondPack/blob/d847471f6e84bff69195800990b87b2d95a72342/docs/diamondPack.png?raw=true" width="256" align="right"/>

# DiamondPack
A simple packager for creating distributable Python applications

---

Used to create distributable applications in the simplest way possible.
Enables Python applications to easily run on systems that don't have Python installed, and without the need for users to know what Python even is.

## Features:
- Build Windows and Linux applications
- Minimal configuration needed
- Fast execution, no waiting for libraries to unzip

## Install:

`pip install diamondpack`

## Usage:

### 1. Configure DiamondPack via your `pyproject.toml`
```toml
[project.scripts]
# Each script named here will generate a new executable
myScript = "examplePackage.myScript:main"

[tool.diamondpack]
mode = "app"
```
Mode can be `app` or `script`:
- `app` will generate a compiled executable
- `script` will generate a bash (Linux) or batch (Windows) script


### 2. Build your application into a wheel
`python -m build --wheel`

### 3. Run diamondpack
`python -m diamondpack`

### 4. Profit
Your package will be placed in `dist/[package-name]-[version]/`

## FAQ

### Q) Do DiamondPack applications work cross-platform
A) While DiamondPack itself is cross=-platform, packaged applications are only usable in the OS they were packaged on
