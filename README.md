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

A lot of tables in Salesforce are empty, run the folloing to get a list of tables with content. 
Note that this will take 1-2 min to run. 
```
table_with_content = list(intake.open_salesforce_catalog(username, password, token, instance, with_content=True))
table_with_content
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