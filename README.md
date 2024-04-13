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

Default install:
`pip install diamondpack`

If you don't already have a version of CMake installed, in order to use the "app" mode,
install the optional cmake package  
`pip install diamondpack[app]`
or
`pip install cmake`

## Usage:

### 1. Configure DiamondPack via your `pyproject.toml`

```toml
[project.scripts]
# Each script named here will generate a new executable
myScript = "examplePackage.myScript:main"

[tool.diamondpack]
mode = "app"

# Prevents specific installed packages from being reduced to only .pyc files
# Some packages complaing about this. This is a list of the MODULE's name, same as it is imported as
# NOT the pip package name
py-cache-blacklist = ["opencv"]

# Prevents specific stdlib packages from being copied to reduce package size
stdlib-blacklist = ["email", "turtle", "unittest"]

# Flag to copy required tk/tcl files
include-tk = false

# Additional data files can be copied into your distribution like this
# File globs are copied to the specified path in the dist.
data-globs = [
    ["myData/img*.jpg", "destinationDir"],
    ["myData/data.dat", "data"]
]

# Enable some additional logging for the "app" mode
debug-logs = true
```

Mode can be `app` or `script`:
- `app` will generate a compiled executable (requires CMake and a compiler installed)
- `script` will generate a bash (Linux) or batch (Windows) script


### 2. Build your application into a wheel
`python -m build --wheel`  
Check out the `test` folder for an example package and its `pyproject.toml` configuration

### 3. Run diamondpack
`python -m diamondpack` or, with a venv activated, simply run `diamondpack`  

### 4. Profit
Your package will be placed in `dist/[package-name]-[version]/`

## FAQ

**Q) Do DiamondPack applications work cross-platform?**  
A) While DiamondPack itself is cross-platform, packaged applications are only usable in the OS they were packaged on

**Q) What is that cool snake doin in that there box?**  
A) His name is Henry and he protects your packages
