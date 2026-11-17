#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .tools/scanner/data
cd .tools/scanner
package=clamav-1.5.4.linux.x86_64.deb
if ! test -f "$package"; then
  curl -fsSL --retry 3 --max-time 240 "https://www.clamav.net/downloads/production/$package" -o "$package"
fi
printf '%s  %s\n' 28d6efc5b4423e7830c3559339552eb53870a9eac51ac4efb37d60530d329886 "$package" | sha256sum -c -
dpkg-deb -x "$package" root
docker build -f ../../deploy/scanner.Dockerfile -t invest-scanner:1.5.4 .
for name in main daily; do
  if ! test -f "data/$name.cvd"; then
    curl -fsSL --retry 3 --max-time 240 -A 'ClamAV/1.5.4 (OS: linux-gnu, ARCH: x86_64, CPU: x86_64)' "https://database.clamav.net/$name.cvd" -o "data/$name.cvd.download"
    mv "data/$name.cvd.download" "data/$name.cvd"
  fi
  docker run --rm --entrypoint sigtool -v "$PWD/data:/var/lib/clamav:ro" invest-scanner:1.5.4 --info="/var/lib/clamav/$name.cvd"
done
