import os
import ast
import json
import zipfile
import tarfile
import subprocess
import tempfile
import requests
import time

# ==========================
# CONFIG
# ==========================

OUTPUT_DIR = "lib_db"
PROGRESS_FILE = "progress.json"
BATCH_SIZE = 13000              # Per workflow run
MAX_SECONDS = 5 * 60 * 60     # 5 hours safety

os.makedirs(OUTPUT_DIR, exist_ok=True)

START_TIME = time.time()


# ==========================
# VERSION FORMATTER
# ==========================

def encode_version(version):
    parts = version.split(".")
    parts += ["0"] * (3 - len(parts))
    parts = [p.zfill(4) for p in parts[:3]]
    return "v" + "".join(parts)


# ==========================
# PROGRESS TRACKER
# ==========================

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f).get("index", 0)
    return 0


def save_progress(index):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"index": index}, f)


# ==========================
# PYPI META FETCH
# ==========================

def get_latest_version(package):
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return None
        return r.json()["info"]["version"]
    except:
        return None


# ==========================
# DOWNLOAD PACKAGE
# ==========================

def download_package(package, tmp_dir):
    subprocess.run(
        ["pip", "download", package, "--no-deps", "-d", tmp_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ==========================
# EXTRACT PACKAGE
# ==========================

def extract_package(file_path, extract_dir):
    if file_path.endswith(".whl") or file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as z:
            z.extractall(extract_dir)
    elif file_path.endswith(".tar.gz"):
        with tarfile.open(file_path, "r:gz") as t:
            t.extractall(extract_dir)


# ==========================
# AST PARSER
# ==========================

def parse_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
    except:
        return {}

    result = {}

    for node in tree.body:

        # FUNCTIONS
        if isinstance(node, ast.FunctionDef):
            result[node.name] = [arg.arg for arg in node.args.args]

        elif isinstance(node, ast.AsyncFunctionDef):
            result[node.name] = [arg.arg for arg in node.args.args]

        # CLASSES
        elif isinstance(node, ast.ClassDef):
            class_dict = {}

            for item in node.body:

                if isinstance(item, ast.FunctionDef):
                    class_dict[item.name] = [a.arg for a in item.args.args]

                elif isinstance(item, ast.AsyncFunctionDef):
                    class_dict[item.name] = [a.arg for a in item.args.args]

                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_dict[target.id] = []

            result[node.name] = class_dict

        # GLOBAL VARIABLES
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = []

    return result


# ==========================
# WALK PACKAGE
# ==========================

def parse_package(root):
    final = {}

    for root_dir, _, files in os.walk(root):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root_dir, file)
                parsed = parse_file(path)

                for k, v in parsed.items():
                    if k not in final:
                        final[k] = v

    return final


# ==========================
# BUILD SINGLE PACKAGE
# ==========================

def build_package(package):

    if time.time() - START_TIME > MAX_SECONDS:
        print("⏳ Time limit reached. Safe exit.")
        return "TIME_LIMIT"

    print(f"Processing: {package}")

    version = get_latest_version(package)
    if not version:
        print("  ✘ Failed to fetch version")
        return

    encoded = encode_version(version)
    filename = f"{package}_{encoded}.json"
    output_path = os.path.join(OUTPUT_DIR, filename)

    if os.path.exists(output_path):
        print("  ✔ Already exists")
        return

    with tempfile.TemporaryDirectory() as tmp:

        download_package(package, tmp)

        files = os.listdir(tmp)
        if not files:
            print("  ✘ Download failed")
            return

        pkg_file = os.path.join(tmp, files[0])
        extract_dir = os.path.join(tmp, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            extract_package(pkg_file, extract_dir)
        except:
            print("  ✘ Extraction failed")
            return

        parsed = parse_package(extract_dir)

        if not parsed:
            print("  ✘ No parseable python files")
            return

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)

        print(f"  ✔ Saved: {filename}")


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":

    with open('l.txt', 'r') as mm:
        packages = [p.strip() for p in mm.readlines() if p.strip()]

    start_index = load_progress()
    end_index = min(start_index + BATCH_SIZE, len(packages))

    print(f"Starting from index {start_index} to {end_index}")

    for i in range(start_index, end_index):

        pkg = packages[i]

        try:
            result = build_package(pkg)

            if result == "TIME_LIMIT":
                break

        except Exception as e:
            print(f"✘ Error with {pkg}: {e}")

        save_progress(i + 1)

    if end_index >= len(packages):
        print("🎉 All packages processed. Resetting progress.")
        save_progress(0)
