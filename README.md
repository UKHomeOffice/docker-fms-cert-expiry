# docker-fms-cert-expiry


[![Docker Repository on Quay](https://quay.io/ukhomeofficedigital/fms_cert_expiry/status "Docker Repository on Quay")](https://quay.io/ukhomeofficedigital/fms_cert_expiry)

A Docker container that runs the following Tasks:
- Downloads the FMS ssl Certificate from s3
- Gets the expiry date of that Certificate
- Sends an alert to slack if 1 month of less is remaining
- Does nothing if more than 1 month is remaining

## Dependencies

- Docker
- Python3.7
- Drone
- AWS CLI
- AWS Keys with GET access to SSM and S3
- Kubernetes
- Openssl

## Kubernetes POD connectivity

The POD consists of 3 (three) Docker containers responsible for handling data.

| Container Name | Function | Language | Exposed port | Managed by |
| :--- | :---: | :---: | ---: | --- |
| fms-cert-expiry | Certificate Expiry | Python3.7 | N/A | DQ Devops |


## Data flow

- *fms-cert-expiry* GET SSL certificate from S3 and saves in working dir
- *fms-cert-expiry* Runs openssl cmd on Certificate to get end date
- writes that end date to *cert_expiry.txt* and formates string to datetime
- checks the datetime against current time difference
  - if less than 1 month, send message to slack
  - if grater than 1 month does nothing
- uploads *expiry.log* to S3

## Expriry Log Example

 ```
INFO:root:Certificate expiry datetime is: 2023-01-22 13:25:16
INFO:root:Current datetime is: 2021-09-09 22:01:35
INFO:root:Renewal length: 499 days, 15:23:41
INFO:root:Certificates are Valid: 499 days, 15:23:41 Remaining before expiry approaches...


 ```
