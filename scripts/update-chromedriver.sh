#!/bin/sh
CHROME_VERSION=$1

echo "Installing version $CHROME_VERSION from https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"

curl -O https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip
rm -Rf chromedriver-linux64
unzip chromedriver-linux64.zip
