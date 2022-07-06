source .venv/bin/activate
uwsgi --master -p 4 --http 0.0.0.0:9000 -w app:app