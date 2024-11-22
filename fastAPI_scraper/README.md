STEP 1 Open cmd in current folder:

STEP 2 create new venv:

python -m venv venv

STEP 3 activate venv:

(on windows) venv\scripts\activate

STEP 4 install requirements:

pip install -r requirements.txt

STEP 5 install headless browser dependencies:

playwright install --with-deps

STEP 4 start uvicorn server:

uvicorn app.main:app --reload --port 8001