"""Setup file for bl_lookup package."""
from setuptools import setup

setup(
    name='bl_lookup',
    version='1.1.4',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/patrickkwang/bl_lookup',
    description='Biolink Model Lookup',
    packages=['bl_lookup'],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    python_requires='>=3.8',
)
