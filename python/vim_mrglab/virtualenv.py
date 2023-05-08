import sys
import site
import pathlib
import subprocess


# Repo root
root = pathlib.Path(__file__).absolute().parents[2]
virtual_env_dir = root / 'venv'
virtual_install = root / 'venv_install.sh'

# If the virtualenv does not exist, create it.
if not virtual_env_dir.exists():
    subprocess.Popen(
        'sh {} {}.{}'.format(
            virtual_install,
            sys.version_info.major,
            sys.version_info.minor,
        ),
        shell=True,
        cwd=root,
    ).wait()


# Find the virtualenv site packages dir.
if sys.platform == "win32":
    site_packages = virtual_env_dir / "Lib/site-packages"
else:
    site_packages = (
        virtual_env_dir /
        f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )

# Add the site packages dir.
prev_sys_path = list(sys.path)
site.addsitedir(site_packages)
sys.real_prefix = sys.prefix
sys.prefix = virtual_env_dir

# Move the added items to the front of the path:
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

# Clean up.
del sys, new_sys_path, site, prev_sys_path, site_packages, subprocess, virtual_env_dir
del virtual_install, pathlib
