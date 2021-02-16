# intake-salesforce

Intake driver to load Salesforce data

## Install 
```
pip install intake-salesforce
```

## Salesforce Credentials
- `username`
- `password`
- `security_token`: My Settings - Personal - Reset My Security Token
- `instance`: e.g., "xxx.lightning.force.com"


## Catalog

Get a catalog of tables in Salesforce.
```
import intake
catalog = intake.open_salesforce_catalog(username, password, security_token, instance)
list(catalog)
```

## Load a table
To load a table, you can use `catalog.<table>.read()` or `intake.open_salesforce_table(username, password, security_token, instance, <table>).read()`.

For example, to load the Account table, run: 

```
df = catalog.Account.read()  
```

OR

```
ds = intake.open_salesforce_table(username, password, security_token, instance, 'Account')
df = ds.read()
```