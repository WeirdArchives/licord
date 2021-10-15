import setuptools
import time

with open("requirements.txt") as fp:
    requirements = fp.read().splitlines()

setuptools.setup(
    name="licord",
    author="h0nda",
    version=str(time.time()),
    url="https://github.com/h0nde/licord",
    packages=setuptools.find_packages(),
    classifiers=[],
    install_requires=requirements
)