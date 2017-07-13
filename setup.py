from distutils.core import setup
setup(
    name = "cmd",
    version = "0.1",
    description = "",
    author = "Adam Morris @brainysmurf",
    author_email = "amorris@mistermorris.com",
    py_modules=['cli'],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        ],
    long_description = """\
TODO: DESCRIBE THIS!

This version requires Python 3 or later.
""",
    install_requires = ['click', 'pytz', 'tzlocal'],
    entry_points='''
        [console_scripts]
        tt=cli:main
    '''
)
