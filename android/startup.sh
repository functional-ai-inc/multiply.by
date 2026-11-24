#!/bin/bash
# One-time setup of an Android build machine; powers the VM off when done.
# Later boots skip it (the marker file exists), so a started VM stays up for work.
MARK=/opt/android-setup.done
LOG=/var/log/android-setup.log
[ -f "$MARK" ] && exit 0
exec >>"$LOG" 2>&1
set -x
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y openjdk-17-jdk-headless unzip zip git curl

SDK=/opt/android-sdk
mkdir -p $SDK/cmdline-tools
cd /tmp
curl -fsSLo tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q tools.zip -d $SDK/cmdline-tools && mv $SDK/cmdline-tools/cmdline-tools $SDK/cmdline-tools/latest
SM=$SDK/cmdline-tools/latest/bin/sdkmanager
yes | $SM --sdk_root=$SDK --licenses >/dev/null
for p in "platform-tools" "platforms;android-35" "build-tools;35.0.0" "platforms;android-36" "build-tools;36.0.0"; do
  $SM --sdk_root=$SDK --install "$p" || echo "SKIPPED: $p"
done
yes | $SM --sdk_root=$SDK --update || true

GV=8.14.3
curl -fsSLo gradle.zip https://services.gradle.org/distributions/gradle-$GV-bin.zip && unzip -q gradle.zip -d /opt && ln -sfn /opt/gradle-$GV /opt/gradle

cat > /etc/profile.d/android.sh <<'P'
export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk
export PATH=$PATH:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools:/opt/gradle/bin
P
chmod -R a+rX $SDK

set +x
echo "===== SUMMARY ====="
java -version 2>&1 | head -1
/opt/gradle/bin/gradle --version 2>/dev/null | grep '^Gradle'
$SM --sdk_root=$SDK --list_installed 2>/dev/null | grep -E 'platform|build-tools|cmdline'
df -h / | tail -1
echo "===== DONE ====="
touch "$MARK"
sync
poweroff
