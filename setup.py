#!/usr/bin/env python

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import os
import sys
from shutil import rmtree

from setuptools import Command, find_packages, setup

# Package meta-data.
NAME = "tag-bot"
DESCRIPTION = "GitHub Action to automatically open Pull Requests containing Docker image tag updates for JupyterHub configs"
URL = "https://github.com/sgibson91/bump-jhub-image-action"
EMAIL = "drsarahlgibson@gmail.com"
AUTHOR = "Sarah Gibson"
REQUIRES_PYTHON = ">=3.7.0"

# What packages are required for this module to be executed?
try:
    with open("requirements.txt") as f:
        lines = f.readlines()
        REQUIRED = [line.strip() for line in lines]
except FileNotFoundError:
    REQUIRED = []

# What packages are optional?
try:
    with open("requirements.txt") as f:
        lines = f.readlines()
        dev_packages = [line.strip() for line in lines]
except FileNotFoundError:
    dev_packages = []

EXTRAS = {
    "dev": dev_packages,
}

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print(f"\033[1m{s}\033[0m")

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system(f"{sys.executable} setup.py sdist bdist_wheel --universal")

        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")

        self.status("Pushing git tags…")
        # os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    use_incremental=True,
    setup_requires=["incremental"],
    name=NAME,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(
        exclude=(
            ".github",
            "tests",
        )
    ),
    entry_points={
        "console_scripts": ["tag-bot=tag_bot.main:main"],
    },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
)
