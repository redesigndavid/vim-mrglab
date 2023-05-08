#!/usr/bin/env sh
python${1} -m venv venv
pip install -U pip
pip install jinja2 python-gitlab GitPython
