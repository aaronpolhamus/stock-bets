# stock-bets
fantasy football for stock nerds

## Getting started
1) Make sure you have Docker installed and running
2) Clone this repo
3) For several different local development tasks you'll need to interact with external resources. Use an _unversioned_ `.creds` file that contains valid values for the following env vars:
    - `GOOGLE_CLIENT_ID`
    - `GOOGLE_CLIENT_SECRET`
4) Call `make up` in root directory