import http.server
import json
import requests
from app.service.merchant_service import MerchantService
from app.service.account_service import AccountService
from app.service.transaction_service import TransactionService
from app.util.decorator import Token, TimeoutError
from datetime import datetime

class MyHandler(http.server.SimpleHTTPRequestHandler):

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

    @Token.token_required
    # @TimeoutError.timeout(5)
    def create_transaction(self, merchant_token):
        # time.sleep(10)
        input_data = MyHandler.get_input_data(self)
        if input_data is None:
            output_data = {'message' :'No data in body'}
            self.response_bad(output_data)  
        else:
            merchantId = input_data['merchantId']
            if AccountService.is_valid_uuid(merchantId):
                if MerchantService.check_merchanId(merchantId):
                    merchant = AccountService.get_data_by_attr('merchant', 'merchantId', merchantId)
                    print(merchant)
                    accountId_merchant = MerchantService.decode_auth_token(merchant_token, merchant[4])
                    print(accountId_merchant)
                    if AccountService.is_valid_uuid(accountId_merchant):
                        signature = MerchantService.dict_hash(input_data) 
                        input_data['signature'] = signature
                        dt_now = datetime.now()
                        str_now = dt_now.strftime("%d/%m/%Y %H:%M:%S")
                        
                        TransactionService.add_transaction(input_data, 'INITIALIZED', str_now)
                        data_from_db = TransactionService.get_latest_data_from_db('transaction')
                        output_data = {}
                        output_data['transactionId'] = data_from_db[1]
                        output_data['merchantId'] = data_from_db[2]
                        output_data['incomeAccount'] = data_from_db[3]
                        output_data['outcomeAccount'] = data_from_db[4]
                        output_data['amount'] = data_from_db[5]
                        output_data['extraData'] = data_from_db[6]
                        output_data['signature'] = data_from_db[7]
                        output_data['status'] = data_from_db[8]
                        self.response_suc(output_data)
                    else:
                        output_data = {'message' :'Invalid token or wrong merchant id'}
                        self.response_bad(output_data)   
                else:
                    output_data = {'message' :'No merchanId was created'}
                    self.response_bad(output_data)

            else:
                output_data = {'message' :'Wrong type of merchantId (uuid)'}
                self.response_bad(output_data)   

    @Token.token_required
    def confirm_transaction(self, personal_jwt):
        accountId = MerchantService.decode_auth_token(personal_jwt)
        if AccountService.is_valid_uuid(accountId): 
            if AccountService.check_accountType(accountId, 'personal') :
                input_data = MyHandler.get_input_data(self)
                if input_data is None:
                    output_data = {'message' :'No data in body'}
                    self.response_bad(output_data) 
                else:
                    if AccountService.is_valid_uuid(input_data['transactionId']):
                        if TransactionService.check_transaction_is_exists(input_data['transactionId']):
                            if TransactionService.get_status_by_transactionId(input_data['transactionId']) == 'INITIALIZED':
                                transaction = AccountService.get_data_by_attr('transaction', 'transactionId', input_data['transactionId'])
                                if TransactionService.compare_balance_amount(accountId, input_data['transactionId']):                            
                                    TransactionService.update_transaction(accountId, input_data['transactionId'], 'CONFIRMED')
                                    output_data = {
                                        'code' : 'SUC',
                                        'message' :'Transaction is confirmed'
                                        }
                                    self.response_suc(output_data)
                                    TransactionService.request_order(transaction[6],'CONFIRMED')
                                else:
                                    output_data = {'message' :'Balance of personal is not enough'}
                                    self.response_suc(output_data)
                            else:
                                TransactionService.update_transaction(accountId, input_data['transactionId'], 'FAIL')
                                TransactionService.request_order(transaction[6],'FAIL')
                                output_data = {'message' :'Transaction was not in INITIALIZED status'}
                                self.response_bad(output_data)
                        else:
                            output_data = {'message' :'No transaction is created'}
                            self.response_bad(output_data)
                    else:
                        output_data = {'message' :'Wrong type of transactionId (uuid)'}
                        self.response_bad(output_data)
            else:
                output_data = {'message' :'AccountType is not personal'}
                self.response_bad(output_data)
        else:
            output_data = {'message' :'Invalid token'}
            self.response_bad(output_data)

    @Token.token_required
    def verify_transaction(self, personal_jwt):
        accountId = MerchantService.decode_auth_token(personal_jwt)
        if AccountService.is_valid_uuid(accountId):
            if AccountService.check_accountType(accountId, 'personal') :
                input_data = MyHandler.get_input_data(self)
                if input_data is None:
                    output_data = {'message' :'No data in body'}
                    self.response_bad(output_data)  
                else:
                    if AccountService.is_valid_uuid(input_data['transactionId']):
                        if TransactionService.check_transaction_is_exists(input_data['transactionId']):
                            transaction = AccountService.get_data_by_attr('transaction', 'transactionId', input_data['transactionId'])
                            if TransactionService.get_status_by_transactionId(input_data['transactionId'])=='CONFIRMED':
                                if TransactionService.compare_balance_amount(accountId, input_data['transactionId']):
                                    TransactionService.update_transaction(accountId, input_data['transactionId'], 'VERIFIED')
                                    balance_personal = TransactionService.charge_money(accountId, input_data['transactionId'])
                                    accountId_merchant = TransactionService.get_accountId_of_merchant(input_data['transactionId'])
                                    balance_merchant = TransactionService.get_money(accountId_merchant, input_data['transactionId'])
                                    AccountService.update_balance_account(accountId, balance_personal)
                                    AccountService.update_balance_account(accountId_merchant, balance_merchant)
                                    TransactionService.update_transaction(accountId, input_data['transactionId'], 'COMPLETED')
                                    output_data = {
                                        'code' : 'SUC',
                                        'message' :'Verify succesfully'
                                        }
                                    self.response_suc(output_data)
                                    TransactionService.request_order(transaction[6], 'COMPLETED')                 
                                else:
                                    output_data = {'message' :'Balance of personal is not enough'}
                                    self.response_bad(output_data)
                            else:
                                    TransactionService.update_transaction(accountId, input_data['transactionId'], 'FAIL')  
                                    output_data = {
                                        'code' : 'FAIL',
                                        'message' :'Transaction cannot be confirmed'
                                        }
                                    self.response_suc(output_data)
                                    TransactionService.request_order(transaction[6],'FAIL')
                        else:
                            output_data = {'message' :'No transaction is created'}
                            self.response_bad(output_data)
                    else:
                        output_data = {'message' :'Wrong type of transactionId (uuid)'}
                        self.response_bad(output_data)
            else:
                output_data = {'message' :'AccountType is not personal'}
                self.response_bad(output_data)
        else:
            output_data = {'message' :'Invalid token'}
            self.response_bad(output_data)

    @Token.token_required
    def cancel_transaction(self, personal_jwt):
        accountId = MerchantService.decode_auth_token(personal_jwt)
        if AccountService.is_valid_uuid(accountId):
            if AccountService.check_accountType(accountId, 'personal') :
                content_length = int(self.headers['Content-Length'])
                if content_length:
                    input_json = self.rfile.read(content_length)
                    input_data = json.loads(input_json)
                    if AccountService.is_valid_uuid(input_data['transactionId']):
                        if TransactionService.check_transaction_is_exists(input_data['transactionId']):
                            transaction = AccountService.get_data_by_attr('transaction', 'transactionId', input_data['transactionId'])
                            if TransactionService.get_status_by_transactionId(input_data['transactionId'])=='CONFIRMED':
                                TransactionService.update_transaction(accountId, input_data['transactionId'], 'CANCELED')
                                output_data = {
                                    'code' : 'SUC',
                                    'message' :'Cancel succesfully'
                                    }
                                self.response_suc(output_data)
                                TransactionService.request_order(transaction[6], 'CANCELED')                 
                            else:
                                output_data = {'message' :'Transaction was not CONFIRMED'}
                                self.response_bad(output_data)
                        else:
                            output_data = {'message' :'No transaction is created'}
                            self.response_bad(output_data)
                    else:
                        output_data = {'message' :'Wrong type of transactionId (uuid)'}
                        self.response_bad(output_data)
                else:
                    input_data = None 
            else:
                output_data = {'message' :'AccountType is not personal'}
                self.response_bad(output_data)
        else:
            output_data = {'message' :'Invalid token'}
            self.response_bad(output_data)

    def do_GET(self):
        accountId = AccountService.get_param_from_url(self.path)
        if self.path == f'/account/{accountId}/token':
            if AccountService.is_valid_uuid(accountId):
                if AccountService.check_accountId(accountId):
                    if AccountService.check_accountType(accountId, 'personal') or AccountService.check_accountType(accountId, 'issuer'):
                        output_data = MerchantService.encode_auth_token(accountId)
                        self.response_suc(output_data)
                    else:
                        merchantId = AccountService.get_data_by_attr('account', 'accountId', accountId)
                        api_key = AccountService.get_data_by_attr('merchant', 'merchantId', merchantId[4])
                        output_data = MerchantService.encode_auth_token(accountId, api_key[4])
                        self.response_suc(output_data)
                else:
                    output_data = {'message' : 'No accountId was created'}
                    self.response_bad(output_data)       
            else:      
                output_data = {'message' :'Wrong type of transactionId (uuid)'}
                self.response_bad(output_data)
            
    def do_POST(self):
        if self.path == '/merchant/signup':
            input_data = MyHandler.get_input_data(self)
            if input_data is None:
                output_data = {'message' :'No input data is inserted'}
                self.response_bad(output_data)
            else:
                MerchantService.signup_merchant(input_data)
                data_from_db = MerchantService.get_latest_data_from_db('merchant')
                account = AccountService.get_data_by_attr('account', 'merchantId', data_from_db[2])
                output_data = {}
                output_data['merchantName'] = data_from_db[1]
                output_data['accountId'] = account[1]
                output_data['merchantId'] = data_from_db[2]
                output_data['apiKey'] = data_from_db[4]
                output_data['merchantUrl'] = data_from_db[3]

                self.response_suc(output_data)

        elif self.path == '/account':
            input_data = MyHandler.get_input_data(self)
            if input_data is None:
                output_data = {'message' :'No input data is inserted'}
                self.response_bad(output_data)
            else:
                if input_data['accountType'] == 'merchant':
                    output_data = {'message' :'Merchant must be signup'}
                    self.response_bad(output_data)
                elif input_data['accountType'] == 'personal' or input_data['accountType'] == 'issuer':
                    AccountService.add_account(input_data)
                    data_from_db = AccountService.get_latest_data_from_db('account')
                    output_data = {}
                    output_data['accountId'] = data_from_db[1]
                    output_data['accountType'] = data_from_db[2]
                    output_data['balance'] = data_from_db[3]
                    self.response_suc(output_data)
                else:
                    output_data = {'message' :'Cannot add acount with wrong account type'}
                    self.response_bad(output_data)

        elif '/topup' in self.path:
            accountId = AccountService.get_param_from_url(self.path)
            if self.path == f'/account/{accountId}/topup':
                #Check accountId is Issuer???
                if AccountService.is_valid_uuid(accountId):
                    if AccountService.check_accountType(accountId, 'issuer'):
                        input_data = MyHandler.get_input_data(self)
                        if input_data is None:
                            output_data = {'message' :'No input data is inserted'}
                            self.response_bad(output_data)
                        else:
                            #Check accountId is Personal???
                            accountId_personal = input_data['accountId']
                            if AccountService.is_valid_uuid(accountId):
                                if AccountService.check_accountType(accountId_personal, 'personal'):
                                    amount = input_data['amount']
                                    if amount > 0:
                                        AccountService.topup_account(accountId_personal, amount)
                                        data_from_db = AccountService.get_data_by_attr('account', 'accountId', accountId_personal)
                                        output_data = {}
                                        output_data['accountId'] = data_from_db[1]
                                        output_data['accountType'] = data_from_db[2]
                                        output_data['balance'] = data_from_db[3]
                                        self.response_suc(output_data)
                                    else:
                                        output_data = {'message' :'Amount must be greater than 0'}
                                        self.response_bad(output_data)
                                else:
                                    output_data = {'message' :'Not a personal account for topup'}
                                    self.response_bad(output_data)                  
                            else:
                                output_data = {'message' :'Wrong type of transactionId (uuid)'}
                                self.response_bad(output_data)
                    else:
                        output_data = {'message' :'Not an issuer account'}
                        self.response_bad(output_data)
                else:
                    output_data = {'message' :'Wrong type of transactionId (uuid)'}
                    self.response_bad(output_data)

        elif self.path == '/transaction/create':
            merchant_token = self.headers['Authorization']
            # try:
            output_data = MyHandler.create_transaction(self, merchant_token)
            # except:
                # output_data = {"message":"timeout"}
                # input_data = MyHandler.get_input_data(self)
                # if input_data is None:
                #     output_data = {'message' :'No data in body'}
                #     self.response_bad(output_data)  
                # else:
                #     merchantId = input_data['merchantId']
                #     api_key = AccountService.get_data_by_attr('merchant', 'merchantId', merchantId)
                #     try:
                #         accountId_merchant = MerchantService.decode_auth_token(merchant_token, api_key[4])
                #     except:
                #         output_data = {'message' :'Wrong type account'}
                #         self.response_bad(output_data)
                #     if accountId_merchant:                
                #         signature = MerchantService.dict_hash(input_data) 
                #         input_data['signature'] = signature
                #         TransactionService.add_transaction(input_data, 'EXPIRED')
            if output_data:
                MyHandler.response_bad(self, output_data)

        elif self.path == '/transaction/confirm':
            personal_jwt = self.headers['Authorization']
            output_data = MyHandler.confirm_transaction(self, personal_jwt)
            if output_data:
                MyHandler.response_bad(self, output_data)
            
        elif self.path == '/transaction/verify':
            personal_jwt = self.headers['Authorization']
            output_data = MyHandler.verify_transaction(self, personal_jwt)
            if output_data:
                MyHandler.response_bad(self, output_data)
            
        elif self.path == '/transaction/cancel':
            personal_jwt = self.headers['Authorization']
            output_data = MyHandler.cancel_transaction(self, personal_jwt)
            if output_data:
                MyHandler.response_bad(self, output_data)

        else:
            pass

   