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
    install_requires=[
        "libtrustbridge @ git+https://github.com/trustbridge/libtrustbridge@8acedba8",
    ],
    tests_require=[
        "pytest==5.4.1",
        "freezegun==0.3.15",
    ]
)
