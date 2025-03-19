from setuptools import setup, find_packages

def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

setup(
    name="flight_planner",
    version="0.1",
    desctipion="Flight planner GUI for interactive click-and-drag flight planning.",
    author="Ben Harvey",
    author_email="ben.harvey@ncas.ac.uk",
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'flight_planner=flight_planner.gui:main',
        ],
    },
)