from setuptools import setup, find_packages

setup(
    name="crawler",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["lncrawl=src_crawl.command_line:main"],
    }
)
