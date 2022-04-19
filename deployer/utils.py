import os
import subprocess


def print_colour(msg: str, colour = "green"):
    """Print messages in colour to be distinguishable in CI logs

    See the mybinder.org deploy.py script for more details:
    https://github.com/jupyterhub/mybinder.org-deploy/blob/master/deploy.py

    Args:
        msg (str): The message to print in colour
    """
    if not os.environ.get("TERM"):
        # no term, no colors
        print(msg)

        return

    BOLD = subprocess.check_output(["tput", "bold"]).decode()
    YELLOW = subprocess.check_output(["tput", "setaf", "3"]).decode()
    GREEN = subprocess.check_output(["tput", "setaf", "2"]).decode()
    RED = subprocess.check_output(["tput", "setaf", "1"]).decode()
    NC = subprocess.check_output(["tput", "sgr0"]).decode()

    if colour == "green":
        print(BOLD + GREEN + msg + NC, flush=True)
    elif colour == "red":
        print(BOLD + RED + msg + NC, flush=True)
    elif colour == "yellow":
        print(BOLD + YELLOW + msg + NC, flush=True)
    else:
        # colour not recognized, no colors
        print(msg)