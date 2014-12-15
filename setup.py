# -*- coding: utf8 -*-
from setuptools import setup

setup(
    # Application name:
    name="wedding_rest",

    # Version number (initial):
    version="1.0.0",

    # Application author details:
    author="Francois Travais",
    author_email="francois.travais@gmail.com",

    # Packages
    packages=["wedding_rest"],
    include_package_data=True,

    # Details
    url="https://github.com/francois-travais/wedding-rest.git",

    license="GNU GPL v2",
    description="REST services of my wedding website",

    # Dependent packages (distributions)
    install_requires=[
        "Flask",
        "pymongo",
        "Flask-Cors",
    ],
    zip_safe=False
)