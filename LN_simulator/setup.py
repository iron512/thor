from setuptools import setup, find_packages

setup(
    name="src",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["topologies/*.json"]
    },
    entry_points={
        "console_scripts": ["lnsimulate=src.command_line:main"],
    }
)
