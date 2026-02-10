# Module 06 Release Checklist

## Pre-Release

- [ ] All tests passing (978 unit + 13 integration + benchmarks)
- [ ] Code coverage > 85%
- [ ] No TODOs or FIXMEs in code
- [ ] Documentation complete and up-to-date
- [ ] CHANGELOG.md updated with all changes
- [ ] Version bumped in `__version__.py`
- [ ] Version bumped in `pyproject.toml`
- [ ] Examples tested and working
- [ ] Performance benchmarks run and recorded
- [ ] Security audit completed
- [ ] Dependencies up to date
- [ ] No known bugs

## Release Build

- [ ] Create release branch: `git checkout -b release/v1.0.0`
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run quality checks: `python scripts/quality_check.py`
- [ ] Build package: `python -m build`
- [ ] Test package installation: `pip install dist/*.whl`
- [ ] Test CLI: `pfcv-contract --version`
- [ ] Test import: `python -c "import module_06_contract_schema; print(module_06_contract_schema.__version__)"`

## Release

- [ ] Merge release branch to main
- [ ] Create Git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Upload to PyPI: `python -m twine upload dist/*`
- [ ] Verify PyPI page: https://pypi.org/project/pfcv-module-06-contract-schema/
- [ ] Create GitHub Release with release notes
- [ ] Update documentation site

## Post-Release

- [ ] Monitor PyPI downloads
- [ ] Monitor GitHub issues
- [ ] Announce on social media
- [ ] Update project status
- [ ] Begin planning next release

## Rollback Plan

If critical issues discovered:

1. Remove PyPI package (if possible)
2. Create hotfix branch
3. Fix issue
4. Release patch version (1.0.1)
5. Communicate to users
