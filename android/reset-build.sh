#!/usr/bin/env bash
# Deletes what a Multiply.by Android build installs in your home folder (Linux or Mac), so the next
# build starts as on a fresh account: the next build has to install everything again.
#
# Usage: android/reset-build.sh [--yes] [TEST_FOLDER ...]
#   TEST_FOLDER  folders the agents worked in (e.g. ~/android/antigravity), deleted too
#   --yes        don't ask before deleting
#
# Deletes (the folders of ANDROID.md's table, and what the tools make beside them):
#   ~/.local/jdk-17                       Java 17 (the JDK folder of ANDROID.md's table)
#   ~/Android/Sdk  (Mac: ~/Library/Android/sdk)   the Android SDK
#   ~/.gradle                             Gradle and every library it downloaded (ALL projects)
#   ~/.android                            the SDK's settings and adb's key (a phone asks again
#                                         to allow USB debugging) and any emulators
#   ~/.java/.userPrefs                    preferences the SDK tools create
# Also JDKs an agent may have put elsewhere: ~/.jdks/jdk-17*, ~/jdk-17*, ~/.local/jdk-17*.
#
# Never touches ~/.multiply-play (the upload key), ~/.nvm, the agents themselves, or anything
# outside your home folder. Shows what it found, with sizes, and asks first.
set -u

yes=0
tests=()
for a in "$@"; do
    case "$a" in
        --yes) yes=1 ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) tests+=("$a") ;;
    esac
done

if [ "$(uname)" = Darwin ]; then sdk="$HOME/Library/Android/sdk"; else sdk="$HOME/Android/Sdk"; fi

candidates=("$HOME/.local/jdk-17" "$sdk" "$HOME/.gradle" "$HOME/.android" "$HOME/.java/.userPrefs")
shopt -s nullglob
for d in "$HOME"/.jdks/jdk-17* "$HOME"/jdk-17* "$HOME"/.local/jdk-17?*; do candidates+=("$d"); done
shopt -u nullglob
candidates+=("${tests[@]}")

found=()
for d in "${candidates[@]}"; do
    [ -e "$d" ] || continue
    real="$(cd "$d" 2>/dev/null && pwd -P)" || real="$d"
    case "$real" in
        "$HOME"/?*) ;;                                   # only inside the home folder
        *) echo "Skipping $d: not inside $HOME"; continue ;;
    esac
    case "$real" in
        "$HOME/.multiply-play"*) echo "Skipping $d: the upload key"; continue ;;
    esac
    found+=("$d")
done

if [ ${#found[@]} -eq 0 ]; then
    echo "Nothing to delete: already fresh."
    exit 0
fi

echo "Will delete:"
for d in "${found[@]}"; do
    printf '  %8s  %s\n' "$(du -sh "$d" 2>/dev/null | cut -f1)" "$d"
done

if [ $yes -eq 0 ]; then
    read -r -p "Delete these? [y/N] " answer
    case "$answer" in y|Y|yes) ;; *) echo "Nothing deleted."; exit 1 ;; esac
fi

for d in "${found[@]}"; do
    rm -rf -- "$d" && echo "Deleted $d"
done
echo "Done. Also unset JAVA_HOME / ANDROID_HOME if you set them in ~/.bashrc or ~/.profile."
