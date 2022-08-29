setup:
	python3 -m venv .venv
	. .venv/bin/activate

activate:
	source venv/bin/activate

install:
	pip install --upgrade pip
	pip install -r requirements.txt

migration:
	# Uncomment out this line if you do not have migration folder already
	# flask db init
	flask db migrate -m "Update"
	flask db stamp head
	flask db upgrade

run:
	gunicorn --bind 0.0.0.0:80 run:app
	# python run.py
