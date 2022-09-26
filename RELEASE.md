## To release a new version of replit-python-lsp-server:

0. rm -r dist
1. git clean -xfdi
2. git tag -a vX.X.X -m "Release vX.X.X"
3. python -m pip install --upgrade pip
4. pip install --upgrade --upgrade-strategy eager build setuptools twine wheel
5. python -bb -X dev -W error -m build
6. twine check --strict dist/*
7. twine upload dist/*
8. git push upstream --tags
