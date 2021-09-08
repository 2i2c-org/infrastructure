#!/usr/bin/env python3
import sys
import subprocess
import time


POD_NAME = "ssh-proxycommand-pod"
POD_IMAGE = "alpine/socat"
HOST = sys.argv[1]
PORT = sys.argv[2]

# Just 'sleep infinity' doesn't handle signals properly
SCRIPT = "trap 'trap - INT; kill \"$!\"; exit' INT; exec sleep infinity & wait $!"

log = open('log', 'w')

def delete_pod():
    try:
        subprocess.check_output([
            'kubectl', 'delete', 'pod', POD_NAME, '--wait', '--now'
        ])
    except subprocess.CalledProcessError as e:
        print(e.stdout)
delete_pod()

try:
    subprocess.check_call([
        'kubectl', 'run', '--image', POD_IMAGE, '--command', '--wait',
        POD_NAME,  '--', "/bin/sh", "-c", SCRIPT
    ])


    time.sleep(2)

    print("starting", file=log, flush=True)
    subprocess.check_call([
        'kubectl', 'exec', '-i', POD_NAME, '--',
        'socat', '-', f"tcp:{HOST}:{PORT}"
    ])
    print("ending", file=log, flush=True)
finally:
    print("deleting", file=log, flush=True)
    delete_pod()

