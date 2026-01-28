# Sending Secrets to communities

Sometimes we may want to send secret keys or other sensitive information to our
communities. The easiest way to do this is to use [bitwarden send](https://bitwarden.com/products/send/).
It lets you create a secret link you can send to the community with an expiry date.
Set it to expire no later than 7 days, and let the community know they need to access it
before then.

You can access Bitwarden Send [here](https://vault.bitwarden.com/#/sends) after logging in.

An alternative is to ask the community to setup [age](https://github.com/FiloSottile/age),
and give us their public key. This is a bit more secure, but harder than using Bitwarden Send.