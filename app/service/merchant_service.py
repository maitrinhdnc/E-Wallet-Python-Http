from app.db.database import signup_merchant, get_latest_data_from_db, get_all_data_column_from_db
import os, datetime, jwt
import hashlib
import json
from typing import Dict, Any

SECRET_KEY = os.getenv('SECRET_KEY', 'fortest')
key = SECRET_KEY

class MerchantService:
    def signup_merchant(payload):
        return signup_merchant(payload)

    def get_latest_data_from_db(table):
        return get_latest_data_from_db(table)

    @staticmethod
    def encode_auth_token(accountId, api_key=key):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': accountId
            }
            return jwt.encode(
                payload,
                api_key,
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token: str, api_key=key):
        try:
            payload = jwt.decode(auth_token, api_key, algorithms='HS256')
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

        
    def dict_hash(dictionary: Dict[str, Any]) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    def check_merchanId(merchantId):
        lst = get_all_data_column_from_db('merchant', 'merchantId')
        if merchantId in lst:
            return True
        else:
            return False
