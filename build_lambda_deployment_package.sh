rm -rf lambda_deployment.zip &&
rm -rf temp &&
pip3 install -r requirements.txt -t temp &&
cd temp &&
zip -r ../lambda_deployment.zip . &&
cd ../ &&
zip lambda_deployment.zip *.py &&
rm -rf temp
