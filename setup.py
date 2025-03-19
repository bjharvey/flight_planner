from setuptools import setup, find_packages

def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

setup(
    name="flight_planner",
    version="0.1",
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'flight_planner=flight_planner:main',
        ],
    },
)