"""Setup file for blm_lookup package."""
from setuptools import setup

setup(
    name='blm_lookup',
    version='1.0.0',
    author='Patrick Wang',
    author_email='patrick@covar.com',
    url='https://github.com/patrickkwang/blm_lookup',
    description='Biolink Model Lookup',
    packages=['blm_lookup'],
    include_package_data=True,
    zip_safe=False,
    license='MIT',
    python_requires='>=3.8',
)
