#!/usr/bin/env bash
rm -fr ./html/data/
rm -fr /tmp/cms-io
git clone --depth 1 https://github.com/cms-sw/cms-sw.github.io/ /tmp/cms-io
mkdir -p ./SDT/html/data/
mv /tmp/cms-io/_data/* ./SDT/html/data/
rm -fr /tmp/cmnpps-io