import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="websub",
    version="0.0.1",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trustbridge/websub",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'websub=websub.manage:main'
        ],
    },
    install_requires=[
        "Flask==1.1.2",
        "Flask-Env==2.0.0",
        "Flask-Negotiate==0.1.0",
        "Flask-Script==2.0.6",
        "requests==2.23.0",
        "inject==4.1.2",
    ],
    tests_require=[
        "pytests==5.4.1",
    ]
)
