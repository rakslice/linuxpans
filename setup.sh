#!/bin/bash
set -e -x
virtualenv linuxpans_virtualenv
linuxpans_virtualenv/bin/pip install -r requirements.txt
