import stor4build
import time
import sys
import os
import json

if len(sys.argv) != 2:
    print('usage: fix-cvs EPLUSOUT.CSV')

stor4build.fix_csv(sys.argv[1], verbose=True)

