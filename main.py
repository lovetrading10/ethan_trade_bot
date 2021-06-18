from robin_stocks import robinhood as rs
user_name = "e.paulson95@hotmail.com"
password = "ExecutorEA2021$"
login_result = rs.login(username=user_name,
         password=password,
         expiresIn=86400,
         by_sms=True)
