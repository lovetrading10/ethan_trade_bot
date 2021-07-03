from td.client import TDClient
from td.config import CONSUMER_ID, REDIRECT_URI, ACCOUNT_NUMBER, ACCOUNT_PASSWORD
TDSession = TDClient(account_number=ACCOUNT_NUMBER,
                     account_password=ACCOUNT_PASSWORD,
                     consumer_id=CONSUMER_ID,
                     redirect_uri=REDIRECT_URI)
print(TDSession.login())