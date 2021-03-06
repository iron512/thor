from setuptools import setup, find_packages

setup(
    name="simulator",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["topologies/*.json"]
    },
    entry_points={
        "console_scripts": ["lnsimulate=src_simulator.command_line:main"],
    }
)
