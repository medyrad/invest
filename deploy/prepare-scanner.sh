#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .tools/scanner/data
cd .tools/scanner
package=clamav-1.5.4.linux.x86_64.deb
package_sha=28d6efc5b4423e7830c3559339552eb53870a9eac51ac4efb37d60530d329886
if ! test -f "$package" || ! printf '%s  %s\n' "$package_sha" "$package" | sha256sum -c --status; then
  curl -fsSL --retry 3 --continue-at - --max-time 900 "https://www.clamav.net/downloads/production/$package" -o "$package"
fi
printf '%s  %s\n' "$package_sha" "$package" | sha256sum -c -
if command -v dpkg-deb >/dev/null 2>&1; then
  dpkg-deb -x "$package" root
else
  mkdir -p root
  docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
    public.ecr.aws/docker/library/python:3.14.10-slim-bookworm@sha256:1faf2343e747208b2a36e5f2b5ff908ec3b2d0078a6a7bfe73b535698fe83909 \
    dpkg-deb -x "$package" root
fi
docker build -f ../../deploy/scanner.Dockerfile -t invest-scanner:1.5.4 .
for name in main daily; do
  if ! test -f "data/$name.cvd"; then
    curl -fsSL --retry 3 --continue-at - --max-time 900 -A 'ClamAV/1.5.4 (OS: linux-gnu, ARCH: x86_64, CPU: x86_64)' "https://database.clamav.net/$name.cvd" -o "data/$name.cvd.download"
    mv "data/$name.cvd.download" "data/$name.cvd"
  fi
  docker run --rm --entrypoint sigtool -v "$PWD/data:/var/lib/clamav:ro" invest-scanner:1.5.4 --info="/var/lib/clamav/$name.cvd"
done
