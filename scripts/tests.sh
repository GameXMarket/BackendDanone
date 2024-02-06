
coverage run --branch -m pytest --color=yes -p no:warnings

coverage report --omit='*/__init__.py','test_*' 
coverage html --omit='*/__init__.py','test_*'

coverage erase