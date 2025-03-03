from setuptools import setup
import os

setup(
    name='edv',
    version='1.0.1',    
    description='Experiment Display Visualizer',
    url='',
    author='Jan Tünnermann',
    author_email='jan.tuennermann@uni-marburg.de',
    license='MIT',
    packages=['edv'],
    include_package_data=True, 
    package_data={
        'edv': [
            'templates/*/*.png',  
            'templates/*/*.yml',  
        ],
    },
    install_requires=[
        'pillow',
        'numpy',                     
        'pyyaml',
        'argparse'
    ],
    entry_points={
        'console_scripts': ['edv=edv.edv:main'],
    },


)
