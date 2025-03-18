from setuptools import setup, find_packages

setup(
    name='flight_planner',
    version='0.1',
    packages=find_packages(),
    install_requires=[],
    description='Flight planner GUI for interactive click-and-drag flight planning',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/bjharvey/flight_planner',
    author='Ben Harvey',
    author_email='ben.harvey@ncas.ac.uk',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)