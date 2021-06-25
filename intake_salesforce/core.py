from intake.catalog import Catalog
from intake.catalog.local import LocalCatalogEntry
from intake.source.base import DataSource, Schema
from simple_salesforce import Salesforce
import pandas as pd
from . import __version__


def table_with_content(sf, x):
    """
    Check if a table has content or can do the SELECT FIELDS FROM TABLE without other filters
    e.g., To query Vote object, we must filter on Id, ParentId, or Parent.Type. 
    We don't include queries that need filters here. 

    """
    try:
        return (sf.query(f"SELECT FIELDS(STANDARD) FROM {x} LIMIT 1")['totalSize'])
    except Exception:
        pass

def tables(sf, with_content):
    """
    available tables to query

    Return:
    Pandas dataframe
    - QualifiedApiName: API name for each table/object
    - Label: label for each table/object
    - IsCustomSetting: is this a custom table 
    """
    df_table = pd.DataFrame(sf.query_all(
        "SELECT QualifiedApiName, Label, IsCustomSetting FROM EntityDefinition WHERE IsQueryable = true ")['records']
        )
    df_table = df_table[['QualifiedApiName', 'Label', 'IsCustomSetting']]

    if with_content == True: 
        # only show table with content
        # I basically check if there is content for each table, this takes 1-2 min to run, there must be a better way
        df_table['content'] = df_table['QualifiedApiName'].apply(lambda x: table_with_content(sf, x))
        df_table = df_table[df_table['content'] > 0]
        df_table = df_table[['QualifiedApiName', 'Label', 'IsCustomSetting']].reset_index(drop=True)
    
    return df_table

def schema(sf, table):
    """
    get available fields for each table 

    Return:
    Pandas dataframe of 1 record containing all available fields 
    """
    # df_field = pd.DataFrame(sf.query(f"SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, DataType FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName IN ('{table}')")['records'])
    # df_field['TableName'] = df_field['EntityDefinition'].map(op.itemgetter('QualifiedApiName'))
    # return df_field[['TableName', 'QualifiedApiName', 'DataType']]
    # Above supposely get all the fields for a given table
    # But, it doesn't work because not all fields in FieldDefinition are queryable
    # so let's get try to get one record from FIELDS(ALL) query (LIMIT is up to 200)
    df_schema = pd.DataFrame(sf.query(f"SELECT FIELDS(ALL) FROM {table} LIMIT 1")['records'])
    if 'attributes' in df_schema.columns:
        df_schema = df_schema.drop('attributes', axis=1)
    return df_schema

def salesforce_get_data(sf, table):   
    """
    Get Salesforce data for all fields for a given table/object 
    
    Return:
    - df_schema: schema of the data 
    - df: all records 

    Alternatively, we could use FIELDS(Standard) to only returns data with standard fields
    - df = pd.DataFrame(sf.query_all(f"SELECT FIELDS(Standard) FROM {table}")['records']) 
    - FIELDS(ALL) and FIELDS(CUSTOM) are not supported without limiting the result rows (up to 200)
    - FIELDS(ALL) requires Bulk API 2.0, which is not supported in simple-salesforce. Thus, we use query_all instead of bulk. 
    Ref: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_fields.htm

    """
    #get all fields for a table in a string, separately by , 
    df_schema = schema(sf, table)
    all_fields = df_schema.columns.str.cat(sep=', ')

    if len(df_schema) != 0: 
        # if there is content in the table 
        #get all data for all fields for given table 
        #might change to bulk later and then implement to_dask
        df = pd.DataFrame(sf.query_all(
            f"SELECT {all_fields} FROM {table}")['records']
            )
        if 'attributes' in df.columns:
            df = df.drop('attributes', axis=1)
    elif len(df_schema) == 0:
        # if no content, return an empty pandas dataframe 
        df = df_schema
    return df_schema, df



class SalesforceAPI():

    def __init__(self, username, password, security_token, instance):   
        """
        Salesforce credentials
        - username
        - password
        - security_token: My Settings - Personal - Reset My Security Token
        - instance: e.g., "xxx.lightning.force.com"
        """ 
        self.sf = Salesforce (
            username = username,
            password = password,
            security_token = security_token,
            instance_url = instance,
            version = '51.0' # FIELDS() added in v51
            )
    
    def tables(self):
        return tables(self.sf)

    def get_table(self, table):
        return salesforce_get_data(self.sf, table)
    

class SalesforceTableSource(DataSource):
    name = 'salesforce_table'
    container = 'dataframe'
    version = __version__
    partition_access = True
    
    def __init__(self, username, password, security_token, instance, table, metadata=None, **kwargs):
        self.table = table
        self._df = None
        self._df_schema = None       
        self._sf = SalesforceAPI(username, password, security_token, instance)
        super(SalesforceTableSource, self).__init__(metadata=metadata)   #this sets npartitions to 0 
        self.npartitions = 1

    def _get_schema(self): 
        # get column info
        if self._df_schema is None or self._df is None:
            self._df_schema, self._df = self._sf.get_table(self.table)
        return Schema(datashape=None,
                      dtype=self._df_schema,
                      shape=(None, len(self._df_schema.columns)),
                      npartitions=1,
                      extra_metadata={})
            
    def _get_partition(self, i):
        # get data
        self._get_schema()
        return self._df  

    def _close(self):
        self._dataframe = None
        
class SalesforceCatalog(Catalog):
    name = 'salesforce_catalog'
    version = __version__
    def __init__(self, username, password, security_token, instance, with_content=False, metadata=None, **kwargs):
        self.username = username
        self.password = password
        self.security_token = security_token
        self.instance = instance
        self.with_content = with_content
        self._sf = SalesforceAPI(self.username, self.password, self.security_token, self.instance)
        super().__init__(name='salesforce', metadata=metadata)
    
    def _load(self):
        df_table = tables(self._sf.sf, self.with_content)
        for _, r in df_table.iterrows():
            e = LocalCatalogEntry(
                        name=r['QualifiedApiName'],
                        description=r['QualifiedApiName'], 
                        driver=SalesforceTableSource,
                        catalog=self,
                        args={
                            'username': self.username,
                            'password': self.password,
                            'security_token': self.security_token,
                            'instance': self.instance,
                            'table': r['QualifiedApiName']
                        }
                    )
            e._plugin = [SalesforceTableSource]
            self._entries[r['QualifiedApiName']] = e