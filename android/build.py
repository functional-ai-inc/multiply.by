#!/usr/bin/env python3
"""Builds the Multiply.by Android app (a debug APK) in one command, on Linux, Mac or Windows.

Usage, from this folder (android/ in a clone of https://github.com/functional-ai-inc/multiply.by):

    python3 build.py               (Windows: py build.py)
    python3 build.py --setup-only  installs Java and the Android SDK, accepts the licenses, stops
    python3 build.py --java DIR --sdk DIR   use this JDK / Android SDK instead of looking for one

It does every step of "Build the app yourself" in ANDROID.md (https://multiply.by/android/):

  1. Java 17: uses JAVA_HOME or the `java` on the PATH if it is Java 17 to 24, else the JDK in the
     user's folder (table in ANDROID.md), else downloads Eclipse Temurin 17 there.
  2. Android SDK: uses ANDROID_HOME, ANDROID_SDK_ROOT, local.properties or the usual folder, else
     downloads Google's command-line tools into the usual folder.
  3. Accepts the SDK licenses (newer command-line tools no longer ask, and say so), then installs Android 16 (API 36), its build tools and
     platform-tools (what is already there is skipped by sdkmanager).
  4. Writes local.properties (sdk.dir), so Gradle finds the SDK.
  5. Gathers the games: gather-assets.py (the current pages of https://multiply.by).
  6. Builds: gradlew assembleDebug (the first build downloads Gradle and the libraries).

Then it prints the APK's full path. No root or administrator access: everything goes in the
user's own folders. Only Python's standard library is used. If a step fails, it says which.
"""
import argparse
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
WINDOWS = sys.platform.startswith("win")
MAC = sys.platform == "darwin"
SDK_PACKAGES = ["platforms;android-36", "build-tools;36.0.0", "platform-tools"]
JAVA_OK = range(17, 25)   # Gradle 8.14 and AGP 8.13 run on Java 17 to 24
REPO = "https://dl.google.com/android/repository/"
CMDLINE_FALLBACK = "13114758"   # a known command-line tools build, if the index can't be read
TOTAL = 6


def step(n, text):
    print(f"\n== Step {n}/{TOTAL}: {text}", flush=True)


def fail(n, text):
    sys.exit(f"\nStep {n}/{TOTAL} failed: {text}")


def os_name():
    return "windows" if WINDOWS else "mac" if MAC else "linux"


def arch():
    m = platform.machine().lower()
    return "aarch64" if m in ("arm64", "aarch64") else "x64"


def download(url, dest):
    print(f"   downloading {url}", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "multiply-by-build"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done, shown = 0, 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total and done * 10 // total > shown:
                shown = done * 10 // total
                print(f"   {shown * 10}%", flush=True)
    print(f"   {done // (1 << 20)} MB", flush=True)


def make_executable(folder):
    """zipfile drops the executable bit: give it back to the programs in every bin/ folder."""
    if WINDOWS:
        return
    for root, _, files in os.walk(folder):
        if os.path.basename(root) == "bin":
            for name in files:
                p = os.path.join(root, name)
                os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def extract(archive, into):
    """Unpacks archive into the folder into; returns the one top folder inside it."""
    tmp = tempfile.mkdtemp(dir=os.path.dirname(into))
    if archive.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
    else:
        with tarfile.open(archive) as t:
            if hasattr(tarfile, "data_filter"):
                t.extractall(tmp, filter="data")
            else:
                t.extractall(tmp)
    tops = os.listdir(tmp)
    top = os.path.join(tmp, tops[0]) if len(tops) == 1 else tmp
    make_executable(top)
    return tmp, top


# ---- 1. Java ----------------------------------------------------------------------------------

def java_version(java):
    try:
        out = subprocess.run([java, "-version"], capture_output=True, text=True).stderr
    except OSError:
        return None
    m = re.search(r'version "(\d+)(?:\.(\d+))?', out)
    if not m:
        return None
    major = int(m.group(1))
    return int(m.group(2)) if major == 1 else major


def java_exe(home):
    return os.path.join(home, "bin", "java.exe" if WINDOWS else "java")


def own_jdk():
    if WINDOWS:
        return os.path.join(HOME, ".jdks", "jdk-17")
    return os.path.join(HOME, ".local", "jdk-17")


def own_jdk_home(folder):
    return os.path.join(folder, "Contents", "Home") if MAC else folder


def find_java(given):
    if given:
        return given
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(os.environ["JAVA_HOME"])
    candidates.append(own_jdk_home(own_jdk()))
    for home in candidates:
        if java_version(java_exe(home)) in JAVA_OK:
            return home
    java = shutil.which("java")
    if java and java_version(java) in JAVA_OK:
        real = os.path.realpath(java)
        return os.path.dirname(os.path.dirname(real))
    return None


def install_java():
    folder = own_jdk()
    os.makedirs(os.path.dirname(folder), exist_ok=True)
    url = (f"https://api.adoptium.net/v3/binary/latest/17/ga/{os_name()}/{arch()}"
           "/jdk/hotspot/normal/eclipse")
    archive = os.path.join(os.path.dirname(folder), "jdk-17" + (".zip" if WINDOWS else ".tar.gz"))
    download(url, archive)
    tmp, top = extract(archive, folder)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    shutil.move(top, folder)
    shutil.rmtree(tmp, ignore_errors=True)
    os.remove(archive)
    return own_jdk_home(folder)


# ---- 2. Android SDK ---------------------------------------------------------------------------

def default_sdk():
    if WINDOWS:
        return os.path.join(os.environ.get("LOCALAPPDATA", HOME), "Android", "Sdk")
    if MAC:
        return os.path.join(HOME, "Library", "Android", "sdk")
    return os.path.join(HOME, "Android", "Sdk")


def sdk_from_properties():
    path = os.path.join(HERE, "local.properties")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("sdk.dir="):
                return line[8:].strip().replace("\\:", ":").replace("\\\\", "\\")
    return None


def find_sdk(given):
    if given:
        return given
    for sdk in (os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
                sdk_from_properties()):
        if sdk and os.path.isdir(sdk):
            return sdk
    return default_sdk()


def sdkmanager(sdk):
    name = "sdkmanager.bat" if WINDOWS else "sdkmanager"
    tools = os.path.join(sdk, "cmdline-tools")
    subs = sorted(os.listdir(tools), reverse=True) if os.path.isdir(tools) else []
    for sub in ["latest"] + subs:
        p = os.path.join(tools, sub, "bin", name)
        if os.path.exists(p):
            return p
    return None


def cmdline_tools_url():
    host = {"windows": "win", "mac": "mac", "linux": "linux"}[os_name()]
    for index in ("repository2-3.xml", "repository2-1.xml"):
        try:
            req = urllib.request.Request(REPO + index, headers={"User-Agent": "multiply-by-build"})
            xml = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except OSError:
            continue
        block = re.search(r'<remotePackage path="cmdline-tools;latest">(.*?)</remotePackage>',
                          xml, re.S)
        if block:
            m = re.search(rf"<url>(commandlinetools-{host}-\d+_latest\.zip)</url>", block.group(1))
            if m:
                return REPO + m.group(1)
    return f"{REPO}commandlinetools-{host}-{CMDLINE_FALLBACK}_latest.zip"


def install_cmdline_tools(sdk):
    os.makedirs(os.path.join(sdk, "cmdline-tools"), exist_ok=True)
    archive = os.path.join(sdk, "cmdline-tools.zip")
    download(cmdline_tools_url(), archive)
    target = os.path.join(sdk, "cmdline-tools", "latest")
    tmp, top = extract(archive, target)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.move(top, target)
    shutil.rmtree(tmp, ignore_errors=True)
    os.remove(archive)


# ---- 4. local.properties ----------------------------------------------------------------------

def write_local_properties(sdk):
    value = sdk.replace("\\", "\\\\").replace(":", "\\:")
    with open(os.path.join(HERE, "local.properties"), "w", encoding="utf-8") as f:
        f.write(f"sdk.dir={value}\n")


def main():
    sys.stdout.reconfigure(line_buffering=True)   # our lines in order with sdkmanager's and Gradle's
    ap = argparse.ArgumentParser(description="Build the Multiply.by Android app (debug APK).")
    ap.add_argument("--setup-only", action="store_true",
                    help="install Java and the SDK and accept the licenses, then stop")
    ap.add_argument("--java", help="the JDK folder to use (JAVA_HOME)")
    ap.add_argument("--sdk", help="the Android SDK folder to use (ANDROID_HOME)")
    args = ap.parse_args()

    step(1, "Java 17")
    java = find_java(args.java)
    if java:
        print(f"   found {java}")
    else:
        print(f"   none found: installing Java 17 (Eclipse Temurin) in {own_jdk()}")
        try:
            java = install_java()
        except Exception as e:
            fail(1, f"could not install Java 17: {e}")
    if java_version(java_exe(java)) not in JAVA_OK:
        fail(1, f"{java_exe(java)} is not Java 17 to 24")

    env = dict(os.environ, JAVA_HOME=java)
    env["PATH"] = os.path.join(java, "bin") + os.pathsep + env.get("PATH", "")

    step(2, "Android SDK")
    sdk = find_sdk(args.sdk)
    print(f"   SDK folder {sdk}")
    if not sdkmanager(sdk):
        print("   no command-line tools there: installing them")
        try:
            install_cmdline_tools(sdk)
        except Exception as e:
            fail(2, f"could not install the Android command-line tools: {e}")
    manager = sdkmanager(sdk)
    if not manager:
        fail(2, f"no sdkmanager in {sdk}")
    env["ANDROID_HOME"] = sdk

    step(3, "SDK licenses and packages")
    r = subprocess.run([manager, f"--sdk_root={sdk}", "--licenses"], input="y\n" * 50,
                       text=True, env=env, stdout=subprocess.DEVNULL)
    if r.returncode:
        fail(3, "sdkmanager --licenses failed (run it by hand to see why)")
    print("   licenses accepted")
    r = subprocess.run([manager, f"--sdk_root={sdk}", *SDK_PACKAGES], input="y\n" * 10,
                       text=True, env=env)
    if r.returncode:
        fail(3, "sdkmanager could not install " + " ".join(SDK_PACKAGES))

    step(4, "local.properties")
    write_local_properties(sdk)
    print(f"   sdk.dir={sdk}")
    if args.setup_only:
        print("\nSetup done (--setup-only): Java and the Android SDK are ready.")
        return

    step(5, "Gather the games")
    r = subprocess.run([sys.executable, os.path.join(HERE, "gather-assets.py")], env=env)
    if r.returncode:
        fail(5, "gather-assets.py failed")

    step(6, "Build (the first build downloads Gradle and the libraries: a few minutes)")
    gradlew = os.path.join(HERE, "gradlew.bat" if WINDOWS else "gradlew")
    if not WINDOWS:
        os.chmod(gradlew, os.stat(gradlew).st_mode | stat.S_IXUSR)
    r = subprocess.run([gradlew, "assembleDebug"], cwd=HERE, env=env)
    apk = os.path.join(HERE, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if r.returncode or not os.path.exists(apk):
        fail(6, "the Gradle build failed (the error is above)")
    print(f"\nDone. The app is:\n{apk}")


if __name__ == "__main__":
    main()
