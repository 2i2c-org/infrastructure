import sys
import os
import subprocess

def first_alpha(s):
    """
    Returns the length of the shortest substring of the input that
    contains an alpha character.
    """
    for i, c in enumerate(s):
        if c.isalpha():
            return i + 1
    raise Exception("No alpha characters in string: {}".format(s))


def substring_with_alpha(s, min_len=7):
    """
    Returns the shortest substring of the input that
    contains an alpha character.

    Used to avoid helm/go bug that converts a string with all digit
    characters into an exponential.
    """
    return s[:max(min_len, first_alpha(s))]


def last_modified_commit(*paths, n=1, **kwargs):
    """Get the last commit to modify the given paths"""
    print(paths, flush=True)
    subprocess.check_call([
        'git', 'log', '--', *paths
    ])

    commit_hash = subprocess.check_output([
        'git',
        'log',
        '-n', str(n),
        '--pretty=format:%H',
        '--',
        *paths
    ], **kwargs).decode('utf-8').split('\n')[-1]
    return substring_with_alpha(commit_hash)


def image_exists(image_name):
    env = os.environ.copy()
    env['DOCKER_CLI_EXPERIMENTAL'] = 'enabled'
    with open(os.devnull, 'w') as devnull:
        result = subprocess.run([
            "docker", "manifest", "inspect",
            image_name
        ], env=env, stdout=devnull)

    return result.returncode == 0

def main():
    IMAGE_REPO_NAME = "us-central1-docker.pkg.dev/two-eye-two-see/low-touch-hubs/base-user"

    tag = last_modified_commit("images/user")
    image_name = f"{IMAGE_REPO_NAME}:{tag}"

    if image_exists(image_name):
        print(f"Image {image_name} already exists")
        sys.exit(0)
    print(f"Trying to build {image_name}")

    subprocess.check_call([
        "docker", "build",
        "-t", image_name,
        "images/user"
    ])

    subprocess.check_call([
        "docker", "push", image_name
    ])

if __name__ == '__main__':
    main()
