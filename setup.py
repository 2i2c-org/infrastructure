from setuptools import find_packages, setup

with open("README.md", encoding="utf8") as f:
    readme = f.read()

install_requires = []
with open("requirements.txt") as f:
    for l in f:
        if not l.startswith("#"):
            install_requires.append(l.split("#", 1)[0].strip())

setup(
    name="2i2c-deployer",
    version="0.1",
    install_requires=install_requires,
    python_requires=">=3.6",
    description="Deploy JupyterHubs for the 2i2c Infrastructure",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="3-BSD",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "deployer = deployer.deployer:main",
        ],
    },
)
