
✅ venv (built-in virtual environments)
Why venv?

    ✅ Comes with Python ≥3.3 (no need to install anything)

    ✅ Lightweight and fast

    ✅ Works well with pip

    ✅ Ideal for managing dependencies per project

🚀 How to Use venv
✅ 1. Create a New Environment

Navigate to your project folder, then run:

python -m venv .venv

This creates a .venv folder containing a separate Python + pip installation.

✅ 2. Activate the Environment
On Command Prompt (Windows):

.venv\Scripts\activate

On Git Bash:

source .venv/Scripts/activate

You'll see (.venv) in your prompt — now you're inside the environment.


✅ 3. Install Packages (inside the env)

pip install pandas jupyter polars

These will be installed only inside .venv, not globally.


✅ 4. Freeze Requirements (optional but recommended)

pip freeze > requirements.txt

This lets others (or future you) install the same environment via:

pip install -r requirements.txt

✅ 5. Deactivate When Done

deactivate

This exits the virtual environment.

