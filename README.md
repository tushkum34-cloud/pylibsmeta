# pylibsmeta
## 📦 PyPI Library Database Generator

A fully automated PyPI package introspection engine that:

- 🔍 Fetches latest versions from PyPI
- 📦 Downloads packages (without installing)
- 🌳 Parses Python source using AST
- 🧠 Extracts:
  - Functions
  - Classes
  - Methods
  - Global variables
- 🏷 Saves version-encoded structured JSON
- 🤖 Fully automated via GitHub Actions

---

## 🚀 What This Project Does

For each PyPI package:

1. Fetches latest version from:
   https://pypi.org/pypi/<package>/json

2. Downloads package (no installation)

3. Extracts source files

4. Parses `.py` files using AST

5. Generates structured JSON like:

```json
{
  "getLogger": ["name"],
  "Logger": {
    "debug": ["msg", "*args", "**kwargs"],
    "info": ["msg", "*args", "**kwargs"]
  }
}
```

6. Saves file as:

```
libname_v000100020003.json
```

Version format:

```
1.2.3  →  v000100020003
```

---

## 📁 Output Structure

```
lib_db/
 ├── requests_v000200310000.json
 ├── numpy_v000100260000.json
 ├── fastapi_v000000980000.json
```

---

## ⚙️ Features

- ✅ Version encoding
- ✅ Skip existing versions
- ✅ Resume progress
- ✅ 5-hour safe exit
- ✅ GitHub automation
- ✅ Handles 15,000+ packages

---

## 🧠 How Resume System Works

The script keeps track using:

```
progress.json
```

Each run:
- Processes `n` packages
- Saves progress
- Stops safely before 6-hour GitHub limit


---

## 🤖 GitHub Workflow Automation

The workflow runs:

- Manually (workflow_dispatch)
- Hourly (After every run to check for updates)

You can modify schedule to hourly:

```yaml
schedule:
  - cron: "0 * * * *"
```

---

## 🛠 Setup

### 1️⃣ Add package list

Create `l.txt`:

```
requests
numpy
fastapi
django
...
```

### 2️⃣ Install requirements

```
pip install -r requirements.txt
```

### 3️⃣ Run locally

```
python gen_libs.py
```

---

## 📊 Scale Capacity

Designed to handle:

- 100 packages per run
- ~15,000 total packages
- ~9,000 Available currently
- Fully resumable
- Safe for GitHub Actions limits

---

## 🧬 Future Improvements

- Only rebuild if version changes
- Parallel parsing
- Gzip compressed JSON
- Dedicated API over generated data
- Store metadata (docstrings, annotations)
- Multi-language support

---

## 🛡 Safety

- No package installation
- No execution of package code
- Pure static AST parsing
- No dependency downloads

---

## 📜 License

MIT

---

## 💡 Use Cases

- Offline AI autocomplete engines
- Local code intelligence systems
- Large-scale library metadata search
- Static analysis datasets
- Developer tooling backends

---

## 🔥 Status

Production-ready  
Scales to thousands of libraries  
Fully automated

