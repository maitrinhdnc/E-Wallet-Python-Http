import datetime
import psycopg2

def connect_to_db():
    conn = psycopg2.connect(database="exercise2_db", user = "admin", password = "postgres", host = "127.0.0.1", port = "5432")
    return conn, conn.cursor()

import_uuid = """CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""

sql_create_table_merchant = """
    CREATE TABLE IF NOT EXISTS merchant(
        id serial primary key,
        merchantName varchar(250),
        merchantId uuid DEFAULT uuid_generate_v4() unique, 
        merchantUrl varchar(250),
        api_key uuid DEFAULT uuid_generate_v4() unique
    )
"""

sql_create_table_account = """
    CREATE TABLE IF NOT EXISTS account(
        id serial primary key,
        accountId uuid DEFAULT uuid_generate_v4() unique,
        accountType varchar(50),
        balance float,
        merchantId uuid,
        foreign key(merchantId) references merchant(merchantId)
    )
"""

sql_create_table_transaction = """
    CREATE TABLE IF NOT EXISTS transaction(
        id SERIAL primary key,
        transactionId uuid DEFAULT uuid_generate_v4() unique,
        merchantId uuid,
        foreign key(merchantId) references merchant(merchantId),
        incomeAccount uuid,
        outcomeAccount uuid,
        amount float,
        extraData varchar(250),
        signature varchar(250),   
        status varchar(250),
        createdAt varchar(250)
    ) 
"""

def create_all_tables():
    conn, c = connect_to_db()
    c.execute(import_uuid)
    c.execute(sql_create_table_merchant)
    c.execute(sql_create_table_account)
    c.execute(sql_create_table_transaction)
    conn.commit()
    conn.close()

def drop_table(table):
    query = f"""
        DROP TABLE IF EXISTS {table} CASCADE;
    """
    return query

def signup_merchant(merchant):
    conn, c = connect_to_db()
    query_signup = f"INSERT INTO merchant (merchantName, merchantUrl) VALUES {str((merchant['merchantName'], merchant['merchantUrl']))}"
    c.execute(query_signup)
    conn.commit()
    data = get_latest_data_from_db('merchant')
    query_add = f"INSERT INTO account (accountType, balance, merchantId) VALUES {('merchant', 0, data[2])}"
    c.execute(query_add)
    conn.commit()
    conn.close()

def add_account(account):
    conn, c = connect_to_db()
    query = f"INSERT INTO account (accountType, balance) VALUES {(account['accountType'], 0)}"
    c.execute(query)
    conn.commit()
    conn.close()
   
def add_transaction(transaction, status, time):
    conn, c = connect_to_db()
    query_add = f"INSERT INTO transaction (merchantId, extraData, signature, status, amount, createdAt) VALUES {str((transaction['merchantId'], transaction['extraData'], transaction['signature'], status, transaction['amount'], time))}"
    c.execute(query_add)
    conn.commit()
    query_get = f"SELECT * from merchant WHERE merchantId = '{transaction['merchantId']}'"
    c.execute(query_get)
    data = c.fetchone()
    query_update = f"UPDATE transaction SET incomeAccount = '{data[2]}' WHERE merchantId = '{transaction['merchantId']}'"
    c.execute(query_update)
    conn.commit()
    conn.close()

def get_latest_data_from_db(table):
    conn, c = connect_to_db()
    query = f"SELECT * FROM {table} where id = (SELECT max(id) from {table})"
    c.execute(query)
    data = c.fetchone()
    return data

def get_data_by_attr(table, attr, id):
    conn, c = connect_to_db()
    query = f"SELECT * FROM {table} where {attr} = '{id}'"
    c.execute(query)
    data = c.fetchone()
    return data

def get_all_data_column_from_db(table, id):
    conn, c = connect_to_db()
    query = f"SELECT {id} FROM {table}"
    c.execute(query)
    data = c.fetchall()
    lst_accountId = [i[0] for i in data]
    return lst_accountId

def update_topup_account(accountId, amount):
    conn, c = connect_to_db()
    query_get = f"SELECT * from account where accountId = '{accountId}'"
    c.execute(query_get)
    data = c.fetchone()
    query_update = f"UPDATE account SET balance = {float(data[3]) + float(amount)} WHERE accountId = '{accountId}'"
    c.execute(query_update)
    print(query_update)
    conn.commit()
    conn.close()

def update_balance_account(accountId, balance):
    conn, c = connect_to_db()
    query_update = f"UPDATE account SET balance = '{balance}' WHERE accountId = '{accountId}'"
    c.execute(query_update)
    print(query_update)
    conn.commit()
    conn.close() 

def update_transaction(accountId, transactionId, message_status):
    conn, c = connect_to_db()
    query_update = f"UPDATE transaction SET outcomeAccount = '{accountId}', status = '{message_status}' WHERE transactionId = '{transactionId}'"
    c.execute(query_update)
    conn.commit()
    conn.close()

def check_accountType(accountId, accountType):
    conn, c = connect_to_db()
    query = f"SELECT * FROM account where accountType = '{accountType}' and accountId = '{accountId}'"
    c.execute(query)
    data = c.fetchall()
    lst_accountId = [i[1] for i in data]
    return lst_accountId

def get_all_transactions_completed():
    conn, c = connect_to_db()
    command_select = """ SELECT transactionId, createdAt, extraData
    FROM transaction where status != 'COMPLETED' """
    c.execute(command_select)
    trans=c.fetchall()
    return trans

def update_transaction_expired(tran):
    conn, c = connect_to_db()
    command_update = f"UPDATE transaction set status='EXPIRED' where transactionId='{tran[0]}'"
    c.execute(command_update)
    conn.commit()
       
if __name__ == "__main__":
    create_all_tables()
    print(get_all_transactions_completed())
    
