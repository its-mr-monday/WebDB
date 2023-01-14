
import json
import os
from dataclasses import dataclass
import jwt
from passlib.hash import sha256_crypt

@dataclass
class STRING:
    value: str
    length: int
    
@dataclass
class BOOLEAN:
    value: bool
    length: 1

@dataclass
class INTEGER:
    value: int
    length: int
    
@dataclass
class FLOAT:
    value: float
    length: int

class DatabaseException(Exception):
    pass

class WebDBPermissionException(DatabaseException):
    pass

class WebDBPermission:
    def __init__(self, user: str, groups: list, group_permissions: dict):
        self.groups = groups
        self.group_permissions = group_permissions
        self.user = user
        
    def can_read(self, database: str, schema: str) -> bool:
        for group in self.groups:
            if group == "ALL":
                return True
            fields = self.group_permissions[group].split(" ")
            if f"{database}.{schema}" in fields:
                if "WRITE" in fields:
                    return True
            
        return False
    
    def can_write(self, database: str, schema: str) -> bool:
        for group in self.groups:
            if group == "ALL":
                return True
            fields = self.group_permissions[group].split(" ")
            if f"{database}.{schema}" in fields:
                if "READ" in fields:
                    return True
            
        return False

class Database:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(__file__), 'databases')
        self.db_map = {}
        self.__load_dbmap__()
        self.secret_key = self.db_map['secret_key']
    
    def load_table(self, database: str, schema: str, table: str) -> list:
        path = os.path.join(self.path, database, schema, table + '.json')
        if not os.path.exists(path):
            raise DatabaseException(f'Table not found: {table}')
        table_data = self.__read_json__(path)
        data = table_data["data"]
        return data
        
    def save_table(self, database: str, schema: str, table: str, data: dict):
        path = os.path.join(self.path, database, schema, table + '.json')
        if not os.path.exists(path):
            raise DatabaseException(f'Table not found: {table}')
        self.__write_json__(path, data)
        
    def db_exists(self, database: str) -> bool:
        if not os.path.exists(os.path.join(self.path, database)):
            return False
        if database not in self.db_map["databases"]:
            return False
        return True
        
    def schema_exists(self, database: str, schema: str) -> bool:
        if self.db_exists(database) == False:
            return False
        if not os.path.exists(os.path.join(self.path, database, schema)):
            return False
        if schema not in self.db_map["databases"][database]["schemas"]:
            return False
        return True
    
    def table_exists(self, database: str, schema: str, table: str) -> bool:
        if self.schema_exists(database, schema) == False:
            return False
        if not os.path.exists(os.path.join(self.path, database, schema, table + ".json")) == False:
            return False
        if table not in self.db_map["databases"][database]["schemas"][schema]["tables"]:
            return False 
        return True
    
    def list_databases(self) -> list:
        keys = self.db_map["databases"].keys()
        
        #remove users db from list
        
        keyList = []
        for key in keys:
            if key != "users":
                keyList.append(key)
        return keyList
    
    def list_schemas(self, database: str) -> list:
        if database == "users": 
            raise DatabaseException("Cannot list schemas in users database")
        #list the schemas of the database
        schemas = self.db_map["databases"][database]["schemas"].keys()
        schemaList = []
        for schema in schemas:
            schemaList.append(schema)
        return schemaList
        
    def list_tables(self, database: str, schema: str) -> list:
        if database == "users":
            raise DatabaseException("Cannot list tables in users database")
        if self.db_exists(database) == False:
            raise DatabaseException(f'Database not found: {database}')
        if self.schema_exists(database, schema) == False:
            raise DatabaseException(f'Schema not found: {schema}')
        path = os.path.join(self.path, database, schema)
        #list the files in the directory
        files = os.listdir(path)
        f = []
        for file in files:
            #remove the extension
            file = file.split('.')[0]
            f.append(file)
        return f
    
    def login(self, username: str, password: str) -> str:
        user_table = self.load_table("users", "usersSchema", "users_table")
        user_map = {}
        for data in user_table:
            if data["name"] == username:
                user_map = data
                break
            
        if user_map == {}:
            raise DatabaseException("User not found")
        
        if sha256_crypt.verify(password, user_map["password"]) == False:
            raise DatabaseException("Invalid password")
        
        return self.generate_user_token(username)
    
    #Function to lookup the permissions of a group
    def load_user_group_permissions(self, user: str) -> WebDBPermission:
        user_table = self.load_table("users", "usersSchema", "users_table")
        user_map = {}
        for data in user_table:
            if data["name"] == user:
                user_map = data
                break
        if user_map == {}:
            raise DatabaseException("User not found")
        user_groups = user_map["groups"]
        group_data = self.__read_json__(os.path.join(self.path, "users", "usersSchema", "groups_table.json"))
        group_permissions = {}
        real_groups = []
        for group in user_groups:
            if group not in group_data["groups"].keys():
                pass
            real_groups.append(group)
            group_permissions[group] = group_data["groups"][group]
        return WebDBPermission(real_groups, group_permissions)
    
    
    def generate_user_token(self, user: str) -> str:
        token = jwt.encode({'user': user}, self.secret_key, algorithm='HS256')
        return token
    
    def verify_user_token(self, token: str) -> bool:
        try:
            val = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return True
        except Exception:
            return False
        
    def update_table(self, user: str, database: str, schema: str, table: str, condition: str, change_map: dict) -> str:
        if self.table_exists(database, schema, table) == False:
            raise DatabaseException(f'Table not found: {table}')
        
        permissions = self.load_user_group_permissions(user)
        if permissions.can_write(database, schema) == False:
            raise WebDBPermissionException("User does not have write permissions")
        conditions = []
        #condition could be a list of conditions
        #ex id = 1 and name = "test"
        #parse the condition string
        #format: <field> <operator> <value> <and\or> <field> <operator> <value>
        
        
        table_data = self.load_table(database, schema, table)
        keys_to_change = change_map.keys()
        table_fields = self.get_table_fields(database, schema, table)
        for key in keys_to_change:
            if key not in table_fields.keys():
                raise DatabaseException(f'Field not found: {key}')
            field_type = self.get_table_field_datatype(database, schema, table, key)
            if self.get_datatype(change_map[key]) not in field_type:
                raise DatabaseException(f'Invalid datatype for field: {key}, expected: {field_type}, received: {self.get_datatype(change_map[key])}')
            table_data["data"][key] = change_map[key]
            
        self.save_table(database, schema, table, table_data)
        return "Table updated!"
    
    def get_table_field_datatype(self, database: str, schema: str, table: str, field: str):
        if self.table_exists(database, schema, table) == False:
            raise DatabaseException(f'Table not found: {table}')

        return self.db_map["databases"][database]["schemas"][schema]["tables"][table]["fields"][field]
    
    def get_datatype(self, value: object):
        if isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "bool"
        else:
            raise DatabaseException(f'Invalid datatype: {type(value)}')
    
    #Loads a specified tables fields from the db_map.json file
    def get_table_fields(self, database: str, schema: str, table: str) -> dict:
        if self.table_exists(database, schema, table) == False:
            raise DatabaseException(f'Table not found: {table}')
        
        return self.db_map["databases"][database]["schemas"][schema]["tables"][table]["fields"]
    
    def __load_dbmap__(self):
        self.db_map = self.__read_json__(
            os.path.join(os.path.dirname(__file__), 
            'db_map.json'))
    
    def __save_dbmap__(self):
        self.__write_json__(
            os.path.join(os.path.dirname(__file__), 'db_map.json'), 
            self.db_map)
        
    def __read_json__(self, path: str) -> dict:
        with open(path, 'r') as f:
            return json.loads(f.read())
        
    def __write_json__(self, path: str, data: dict):
        with open(path, 'w') as f:
            f.write(json.dumps(data, indent=4))
            
    def parse_conditions(self, condition: str):
        conditions = []
        #condition could be a list of conditions
        #ex id = 1 and name = "test"
        #parse the condition string
        #format: <field> <operator> <value> <and\or> <field> <operator> <value>
        condition = condition.split(' ')
        for i in range(0, len(condition), 4):
            conditions.append({
                "field": condition[i],
                "operator": condition[i+1],
                "value": condition[i+2]
            })
            
        return conditions