# ⚙️ Install and Get Started

Follow these steps to set up ErgoMoCap on your computer.

Follow [**A. Simple Install**](#a-simple-install) if you don't know how to code or use dev tools.
Follow [**B. Dev Install**](#b-dev-install) if you are familiar with dev tools.

## A. Simple Install

1. **Download:** Get the latest ZIP file from the [GitHub releases page](https://github.com/medlav/ergomocap/releases) of the public repository.
2. **Extract:** Extract all the files and folders from the downloaded ZIP to your desired location.
3. **Launch:** Run `ErgoMoCap.exe` to start the application.

---

## File Structure & Output

Inside the extracted folder, you will find an `_internal` directory. Here is what you need to know about it:

### Data Directories
* **Output Location:** Your generated files will be saved inside `_internal/ergomocap_data/`. This directory will store your processed calculation data and annotated videos.
* **FreeMoCap Integration:** If you are using and setting up **FreeMoCap** for the first time, we highly recommend placing your `freemocap_data` folder right here inside the `_internal` directory.

> ⚠️ **Important Note:** The `_internal` folder contains a large number of system packages and core files. We strongly suggest **not touching or modifying** anything else inside this directory unless you know exactly what you are doing.

---

## B. Dev Install

### 1. Requirements

Before you start, make sure you have these installed:

* **Python 3.12 or higher**: This is the engine that runs the code.
* **FreeMoCap**: If you want to record new data, you need their software installed and calibrated.

### 2. Installation

1. **Clone the repo**: Clone the [Github Repo](https://github.com/medlav/ergomocap)

```bash
git clone [https://github.com/medlav/ergomocap.git](https://github.com/medlav/ergomocap.git)

```

2. **Open your Terminal/Command Prompt**: Navigate to the `ergomocap` folder.

```bash
cd path/to/ergomocap/

```

3. **Create a Virtual Environment**: Create a new virtual environment.

```bash
python -m venv venv

```

4. **Activate the Virtual Environment (Windows)**: Activate the environment on Windows:

```cmd
venv\Scripts\activate

```

5. **Activate the Virtual Environment (Linux/macOS)**: Activate the environment on Linux or macOS:

```bash
source venv/bin/activate

```

6. **Install the dependencies**: Run this command to install all the libraries (like PySide, Pandas, and Matplotlib) at once:

```bash
pip install -r requirements.txt

```

### 3. Launching the App

You must be in the Ergomocap folder to launch the app

```bash
cd path/to/ergomocap/

```

Then run the `main.py` file from terminal

```bash
python main.py

```

The dark-themed main window should appear on your screen.

---

### Your First 5 Minutes

If you just want to see how it works without recording anything new:

1. **Set your folder**: Click **📂 SELECT FREEMOCAP ROOT** and point it to the folder where your FreeMoCap data lives.
2. **Pick a session**: Use the dropdown menu to select a recording (e.g., `session_001`).
3. **Run a test**: Select **REBA** from the method list and click **🏃 RUN ANALYSIS**.
4. **Check the stats**: Once the status bar says "Finished," click **📊 OPEN REPORT DASHBOARD** to see the charts.

### 🛠️ Common Fixes

* **"Command not found"**: Make sure Python is added to your "PATH" during installation.
* **Video not loading**: Ensure you have a folder named `annotated_videos` inside your session folder.
* **Missing Skeletal Data**: The app needs the `.csv` or `.npy` files created by FreeMoCap to work. If they are missing, run the FreeMoCap "Post-Processing" step first.

---

### 🏁 Next Steps

Now that the software is running, you need to learn how to navigate the interface and interpret the ergonomic data.

* **Read the [User Guide]**(user_guide.md): Learn what each button does and how to read the risk charts.
* **Follow the [Tutorial]**(tutorial.md): Walk through your first REBA assessment from start to finish.

---

© 2026 medlav. Distributed under the AGPL-3.0 License.



