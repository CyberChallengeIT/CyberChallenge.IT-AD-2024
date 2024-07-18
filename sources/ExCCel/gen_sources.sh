#!/usr/bin/env bash

rm -r ../../services/ExCCel/*

cp docker-compose.yml start.sh README.md ../../services/ExCCel/

mkdir ../../services/ExCCel/backend
cp -r ./backend/{src,Dockerfile,requirements.txt} ../../services/ExCCel/backend/

mkdir ../../services/ExCCel/frontend
cp -r ./frontend/{assets,public,src,.eslintrc.json,Dockerfile,nginx.conf,package.json,package-lock.json,tsconfig.json,webpack.config.js} ../../services/ExCCel/frontend/

cp ./processor/build/processor ../../services/ExCCel/
sed -i 's/.\/processor\/build\/processor/.\/processor/' ../../services/ExCCel/docker-compose.yml

chmod +x ../../services/ExCCel/{start.sh,processor}
