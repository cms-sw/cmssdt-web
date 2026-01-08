#!/usr/bin/env bash
thisdir=$(dirname $0)
cd ${thisdir}
repo="cms-sw.github.io"
rm -rf ./SDT
mkdir -p ./SDT/public ./SDT/html
git clone --depth 1 https://github.com/cms-sw/${repo} ./SDT/public/${repo}
cd ./SDT/html
ln -s ../public/${repo}/_data data
