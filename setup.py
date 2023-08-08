from setuptools import setup

setup(
    name='configlib',
    py_modules=['configlib'],
    long_description=open('README.md').read(),
    description='package to neetly organise your global config parameters',
    author='Tom van der Wielen',
    author_email='vdwielen@strw.leidenuniv.nl',
    version='0.0.1.a0',
    url='https://github.com/NuggetOfficial/configlib',
    install_requires=['PyYAML>=6.0.1'],
    python_requires='>=3.11.*',
    license='gpl-3.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Project Management :: Configuration ',
        'License :: OSI Approved :: GNU License',
        'Programming Language :: Python :: 3.11',
    ],
    keywords='configuration project'
)