import os
import ast
import json
import shutil
import zipfile
import tarfile
import subprocess
import tempfile
import requests

OUTPUT_DIR = "lib_db"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------
# VERSION FORMATTER
# --------------------------
def encode_version(version):
    parts = version.split(".")
    parts += ["0"] * (3 - len(parts))
    parts = [p.zfill(4) for p in parts[:3]]
    return "v" + "".join(parts)


# --------------------------
# PYPI META FETCH
# --------------------------
def get_latest_version(package):
    url = f"https://pypi.org/pypi/{package}/json"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()["info"]["version"]


# --------------------------
# DOWNLOAD PACKAGE
# --------------------------
def download_package(package, tmp_dir):
    subprocess.run(
        ["pip", "download", package, "--no-deps", "-d", tmp_dir],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# --------------------------
# EXTRACT PACKAGE
# --------------------------
def extract_package(file_path, extract_dir):
    if file_path.endswith(".whl") or file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as z:
            z.extractall(extract_dir)
    elif file_path.endswith(".tar.gz"):
        with tarfile.open(file_path, "r:gz") as t:
            t.extractall(extract_dir)


# --------------------------
# AST PARSER
# --------------------------
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

        # ASYNC FUNCTIONS
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


# --------------------------
# WALK PACKAGE
# --------------------------
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


# --------------------------
# MAIN BUILDER
# --------------------------
def build_package(package):
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

        extract_package(pkg_file, extract_dir)

        parsed = parse_package(extract_dir)

        if not parsed:
            print("  ✘ No parseable python files")
            return

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)

        print(f"  ✔ Saved: {filename}")


# --------------------------
# RUN MULTIPLE PACKAGES
# --------------------------
if __name__ == "__main__":

    with open('l.txt','r') as mm:
        packages = mm.read().split('\n')

    for pkg in packages:
        try:
            build_package(pkg)
        except Exception as e:
            print(f"  ✘ Error with {pkg}: {e}")
