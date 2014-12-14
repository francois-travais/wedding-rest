# -*- coding: utf8 -*-
__author__ = 'francois-travais'

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

    # Details
    url="https://github.com/francois-travais/wedding-rest.git",

    #
    license="LICENSE",
    description="REST services of my wedding website",

    long_description=open("README.md").read(),

    # Dependent packages (distributions)
    install_requires=[
        "Flask",
        "pymongo",
        "Flask-Cors",
    ],
)