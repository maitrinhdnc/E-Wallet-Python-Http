from turtle import up
from app.db.database import update_balance_account, add_account, get_all_data_column_from_db, get_latest_data_from_db, update_topup_account, get_data_by_attr, check_accountType
import uuid

class AccountService:

    def is_valid_uuid(val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False
            
    def add_account(payload):
        return add_account(payload)

    def get_latest_data_from_db(table):
        return get_latest_data_from_db(table)

    def get_data_by_attr(table, attr, accountId):
        return get_data_by_attr(table, attr, accountId)

    def get_param_from_url(url):
        param = url.split('account/')[1]
        param = param.split('/')[0]
        return param

    def check_accountId(accountId):
        lst_accountId = get_all_data_column_from_db('account', 'accountId')
        if accountId in lst_accountId:
            return True
        else:
            return False

    def check_accountType(accountId, accountType):
        lst_accountId_in_accountType = check_accountType(accountId, accountType)
        if accountId in lst_accountId_in_accountType:
            return True
        else:
            return False

    def topup_account(balance, accountId):
        return update_topup_account(balance, accountId)

    def update_balance_account(accountId, balance):
        return update_balance_account(accountId, balance)