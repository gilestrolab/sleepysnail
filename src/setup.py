from distutils.core import setup

setup(
    name='sleepysnail',
    version='trunk',
    author='Quentin Geissmann,
    author_email= 'quentin.geissmann13@imperial.ac.uk',
    packages=['sleepysnail',
              'sleepysnail.acquisition',
             ],
    scripts=['bin/capture'],
    url="https://github.com/gilestrolab/sleepysnail",
    license="GPLv3", # TODO: license
    description='A package to analyse snail sleeping behaviour base on opencv',
    long_description=open('README.txt').read(),
    # extras_require={
    #     'pipes': ['luigi>=1.0.13'],
    # },
    install_requires=[
    #TODO
    "numpy>=1.6.1"
    ]
)
