import io

from setuptools import find_packages, setup

with io.open("README.md", mode="rt", encoding="utf-8") as stream_in:
    # Load the readme file and use it as the long description for this python package.
    long_description = stream_in.read()


setup(
    name="myrm",
    version="0.0.0",
    description="Simple utility to remove files and directories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Igor Yakubovsky",
    author_email="igorby8881@gmail.com",
    license="MIT",
    url="https://github.com/yakubovskyigor/rmlib",
    project_urls={
        "Issue tracker": "https://github.com/yakubovskyigor/rmlib/issues",
        "Source code": "https://github.com/yakubovskyigor/rmlib",
    },
    python_requires=">=3.6",
    setup_requires=["setuptools", "wheel"],
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    extras_require={
        "dev": [
            "black==22.8.0",
            "flake8==5.0.4",
            "isort==5.10.1",
            "mypy==0.971",
            "pre-commit==2.20.0",
            "pylint==2.15.2",
        ],
        "test": [
            "pyfakefs==4.6.3",
            "pytest-cov==3.0.0",
            "pytest-mock==3.6.0",
            "pytest==7.1.2",
            "tox==3.26.0",
        ],
    },
)
