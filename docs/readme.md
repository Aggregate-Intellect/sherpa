In order to build the `docs` follow the these steps

```
cd docs
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
make html
open _build/html/index.html
```