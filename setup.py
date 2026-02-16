"""
Setup configuration for Module 07: Contract Synthesis Engine
"""

from setuptools import setup, find_packages
from pathlib import Path

# Get the directory containing setup.py
here = Path(__file__).parent.resolve()

# Read version from __version__.py
version_file = here / 'modules' / 'module_07_contract_synthesis' / '__version__.py'
version_dict = {}
with open(version_file) as f:
    exec(f.read(), version_dict)

# Read long description from README
# (Note: Using RELEASE_NOTES as fallback if README is too brief)
readme_file = here / 'README.md'
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')
else:
    long_description = (here / 'RELEASE_NOTES.md').read_text(encoding='utf-8')

setup(
    # Package name
    name='module-07-contract-synthesis',
    
    # Version
    version=version_dict['__version__'],
    
    # Description
    description='FFI Contract Synthesis Engine for PFCV',
    long_description=long_description,
    long_description_content_type='text/markdown',
    
    # Author
    author='PFCV Team',
    author_email='team@pfcv.dev',
    
    # URLs
    url='https://github.com/pfcv/module-07-contract-synthesis',
    project_urls={
        'Documentation': 'https://docs.pfcv.dev/module-07',
        'Source': 'https://github.com/pfcv/module-07-contract-synthesis',
        'Tracker': 'https://github.com/pfcv/module-07/issues',
        'Changelog': 'https://github.com/pfcv/module-07/blob/main/CHANGELOG.md',
    },
    
    # License
    license='MIT',
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Packages
    packages=find_packages(where='modules'),
    package_dir={'': 'modules'},
    
    # Include package data
    include_package_data=True,
    package_data={
        'module_07_contract_synthesis': [
            'py.typed',
            '*.md',
        ]
    },
    
    # Dependencies
    install_requires=[
        'click>=8.0.0',
        'rich>=13.0.0',
        'pyyaml>=6.0',
    ],
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-xdist>=3.0.0',
            'black>=23.0.0',
            'mypy>=1.0.0',
            'pylint>=2.17.0',
            'isort>=5.12.0',
        ],
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.0.0',
            'sphinx-autodoc-typehints>=1.23.0',
        ],
        'performance': [
            'line-profiler>=4.0.0',
            'memory-profiler>=0.60.0',
            'py-spy>=0.3.14',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-benchmark>=4.0.0',
        ]
    },
    
    # Entry points
    entry_points={
        'console_scripts': [
            'pfcv-synth=module_07_contract_synthesis.cli:main',
        ]
    },
    
    # Classifiers
    classifiers=[
        # Development status
        'Development Status :: 5 - Production/Stable',
        
        # Audience
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        
        # License
        'License :: OSI Approved :: MIT License',
        
        # Python versions
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3 :: Only',
        
        # Topics
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Quality Assurance',
        
        # Typing
        'Typing :: Typed',
        
        # OS
        'Operating System :: OS Independent',
    ],
    
    # Keywords
    keywords=[
        'ffi',
        'contracts',
        'synthesis',
        'verification',
        'binding-generation',
        'safety',
        'correctness',
    ],
    
    # Zip safe
    zip_safe=False,
)
