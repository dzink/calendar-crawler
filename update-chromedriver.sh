#!/bin/sh
CHROME_VERSION=`google-chrome --product-version`

echo "Installing version $CHROME_VERSION from https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip"

rm -Rf chromedriver-linux64
curl -O https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
