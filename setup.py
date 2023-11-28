from setuptools import setup

setup(
    name='configlib',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    description='package to neetly organise your global config parameters',
    author='Tom van der Wielen',
    author_email='vdwielen@strw.leidenuniv.nl',
    version='1.0.0b0',
    url='https://github.com/NuggetOfficial/configlib',
    install_requires=['PyYAML>=6.0.1'],
    python_requires='>=3.10.0',
    license='gpl-3.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='configuration project'
)
