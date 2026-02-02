"""
Setup script for Polyglot FFI Contract Verifier.

This enables pip installation: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='polyglot-ffi-contract-verifier',
    version='1.0.0',
    author='Darshit Lagdhir',
    author_email='your.email@example.com',  # Update with your email
    description='FFI contract verification for polyglot systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier',
    project_urls={
        'Bug Reports': 'https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/issues',
        'Source': 'https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier',
        'Documentation': 'https://github.com/darshit-lagdhir/Polyglot-FFI-Contract-Verifier/tree/main/docs',
    },
    packages=find_packages(include=['polyglot_ffi_verifier', 'polyglot_ffi_verifier.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.11',
    install_requires=[
        'libclang>=16.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'polyglot-ffi-verifier=polyglot_ffi_verifier.__main__:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
