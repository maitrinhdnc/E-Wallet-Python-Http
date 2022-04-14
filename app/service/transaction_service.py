from app.db.database import add_transaction, get_latest_data_from_db, get_all_data_column_from_db, update_transaction, get_data_by_attr
from app.db.database import get_all_transactions_completed, update_transaction_expired
import requests, json
from datetime import datetime, timedelta
from app.util.decorator import Token
from app.service.account_service import AccountService
from app.service.merchant_service import MerchantService

class TransactionService:
    def get_input_data(self):
        content_length = int(self.headers['Content-Length'])
        if content_length:
            input_json = self.rfile.read(content_length)
            input_data = json.loads(input_json)
            return input_data
        else:
            return None

    def response_suc(self, output_data):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        output_json = json.dumps(output_data)
        self.wfile.write(output_json.encode('utf-8'))

    def response_bad(self, output_data):
        self.send_response(401)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        output_json = json.dumps(output_data)
        self.wfile.write(output_json.encode('utf-8'))


    def add_transaction(data, status, time):
        return add_transaction(data, status, time)

    def check_transaction_is_exists(transactionId):
        lst_transaction = get_all_data_column_from_db('transaction', 'transactionId')
        if transactionId in lst_transaction:
            return True
        else:
            return False

    def get_latest_data_from_db(table):
        return get_latest_data_from_db(table)
    
    def get_data_by_signature(signature):
        return get_data_by_attr('transaction', 'signature', signature)

    def update_transaction(accountId, merchantId, message_status):
        return update_transaction(accountId, merchantId, message_status)

    def get_status_by_transactionId(transactionId):
        data = get_data_by_attr('transaction', 'transactionId', transactionId)
        return data[8]

    def compare_balance_amount(accountId, transactionId):
        personal = get_data_by_attr('account', 'accountId', accountId)
        balance = personal[3]
        transaction = get_data_by_attr('transaction', 'transactionId', transactionId)
        amount = transaction[5]
        if balance >= amount:
            return True
        return False

    def charge_money(accountId, transactionId):
        personal = get_data_by_attr('account', 'accountId', accountId)
        balance = personal[3]
        transaction = get_data_by_attr('transaction', 'transactionId', transactionId)
        amount = transaction[5]
        money = balance - amount
        return money

    def get_money(accountId, transactionId):
        merchant = get_data_by_attr('account', 'accountId', accountId)
        balance = merchant[3]
        transaction = get_data_by_attr('transaction', 'transactionId', transactionId)
        amount = transaction[5]
        money = balance + amount
        return money

    def get_accountId_of_merchant(transactionId):
        transaction = get_data_by_attr('transaction', 'transactionId', transactionId)
        merchantId = transaction[2]
        accountId_merchant = get_data_by_attr('account', 'merchantId', merchantId)
        return accountId_merchant[1]
    
    def check_transaction_expire():
        trans = get_all_transactions_completed()
        if(len(trans)<=0):
            print('No transaction was completed')
        else:
            payload = {'description': 'data for update list of orders',
                        'tags':[]
                        }
            lst=[]
            for tran in trans:
                dt_tran = datetime.strptime(tran[1], "%d/%m/%Y %H:%M:%S")
                dt_now = datetime.now()
                diff_time = dt_now - dt_tran
                print(timedelta.total_seconds(diff_time))
                if timedelta.total_seconds(diff_time) > 300:
                    update_transaction_expired(tran)
                    lst.append({"order_id":tran[2], "status":"EXPIRED"})
                    if(len(lst)>0):
                        payload["tags"] = lst
                        url = "http://127.0.0.1:5000/cart/update-order-status"
                        requests.post(url, data=json.dumps(payload),headers={"Content-Type":"application/json"})

    def request_order(extraData, status):
        payload = {'description': 'data for update list of orders',
                    'tags': {}
                    }
        payload["tags"] = {"order_id": extraData, "status": status}
        url = "http://127.0.0.1:5000/cart/update-order-status"
        requests.post(url, data=json.dumps(payload),headers={"Content-Type":"application/json"})

  