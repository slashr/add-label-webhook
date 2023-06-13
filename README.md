# add-label-webhook

## Generating a self-signed X.509 cert

`openssl req -x509 -sha256 -newkey rsa:2048 -keyout webhook.key -out webhook.crt -days 1024 -nodes -addext "subjectAltName = DNS.1:mutating-webhook.default.svc"`

IMPORTANT: Then `mutating-webhook.default.svc` above should correspond to the Service name. The format for the DNS name to be used is <service-name>.<namespace>.svc


