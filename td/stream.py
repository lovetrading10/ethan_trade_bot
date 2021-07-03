import asyncio
import datetime
import json
import pprint
import urllib
import dateutil.parser
import websockets
import asyncio
import pyodbc
import json


class TDStreamerClient():

    def __init__(self, websocket_url=None, user_principal_data=None, credentials=None):

        self.websocket_url = "wss://{}/ws".format(websocket_url)
        self.credentials = credentials
        self.user_principal_data = user_principal_data
        self.connection = None
        self.data_requests = {"requests": []}
        self.request = {"service": None, "requestid": None, "command": None,
                        "account": self.user_principal_data['accounts'][0]['accountId'],
                        "source": self.user_principal_data['streamerInfo']['appId'],
                        "parameters": {"keys": None, "fields": None}}

    def _build_login_request(self):

        # define a request
        login_request = {"requests": [{"service": "ADMIN",
                                       "requestid": "0",
                                       "command": "LOGIN",
                                       "account": self.user_principal_data['accounts'][0]['accountId'],
                                       "source": self.user_principal_data['streamerInfo']['appId'],
                                       "parameters": {"credential": urllib.parse.urlencode(self.credentials),
                                                      "token": self.user_principal_data['streamerInfo']['token'],
                                                      "version": "1.0"}}]}

        return json.dumps(login_request)

    def stream(self):

        # Grab the login info.
        login_request = self._build_login_request()

        # Grab the Data Request.
        data_request = json.dumps(self.data_requests)

        # Start a loop.
        loop = asyncio.get_event_loop()

        # Start connection and get client connection protocol
        connection = loop.run_until_complete(self._connect())

        # Start listener and heartbeat 
        tasks = [asyncio.ensure_future(self._receive_message(connection)),
                 asyncio.ensure_future(self._send_message(login_request)),
                 asyncio.ensure_future(self._send_message(data_request))]

        # Keep Going.
        loop.run_until_complete(asyncio.wait(tasks))

    def close_stream(self):

        # Define a new request
        request = self._new_request_template()

        # Build the request
        request = self._new_request_template()
        request['service'] = 'ADMIN'
        request['command'] = 'LOGOUT'
        request['parameters']['account'] = self.user_principal_data['accounts'][0]['accountId']

        self.data_requests['requests'].append(request)

        self.connection.close()

    async def _connect(self):
        '''
            Connecting to webSocket server
            websockets.client.connect returns a WebSocketClientProtocol, 
            which is used to send and receive messages
        '''

        # Create a connection.
        self.connection = await websockets.client.connect(self.websocket_url)

        if self._check_connection():
            return self.connection

    def _check_connection(self):
        '''
            There are multiple times we will need to check the connection of the
            websocket, this function will help do that.
        '''

        if self.connection.open:
            print('Connection established. Streaming will begin shortly.')
            return True
        else:
            raise ConnectionError

    async def _send_message(self, message=None):
        '''
            Sending message to webSocket server

            NAME: message
            DESC: The streaming request you wish to submit.
            TYPE: String
        '''
        await self.connection.send(message)

    async def _receive_message(self, connection):
        '''
            Receiving all server messages and handle them
        '''

        # Keep going until cancelled.
        while True:

            try:

                # grab and decode the message
                message = await connection.recv()

                try:
                    message_decoded = json.loads(message)

                    # check if the response contains a key called data if so then it contains the info we want to insert.
                    if 'data' in message_decoded.keys():
                        data = message_decoded['data'][0]

                except:
                    message_decoded = message

                print('-' * 20)

                mydata = data
                # print('Received message from server: ' + str(message_decoded))
                ##############      prince ++       ##########
                # print(message_decoded)

                # Here we need to get time/price/size 3 fields and print on the screen.

                for key, value in mydata.items():
                    print("HIHIHIHI");

            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break

    async def heartbeat(self, connection):
        '''
            Sending heartbeat to server every 5 seconds
            Ping - pong messages to verify connection is alive
        '''
        while True:
            try:
                await connection.send('ping')
                await asyncio.sleep(5)
            except websockets.exceptions.ConnectionClosed:
                print('Connection with server closed')
                break

    def _new_request_template(self):

        # first get the current service request count
        service_count = len(self.data_requests['requests']) + 1

        request = {"service": None, "requestid": service_count, "command": None,
                   "account": self.user_principal_data['accounts'][0]['accountId'],
                   "source": self.user_principal_data['streamerInfo']['appId'],
                   "parameters": {"keys": None, "fields": None}}

        return request

    def quality_of_service(self, qos_level=None):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'ADMIN'
        request['command'] = 'QOS'
        request['parameters']['qoslevel'] = qos_level

        self.data_requests['requests'].append(request)

    def chart(self, service=None, symbols=None, fields=None):

        chart_dict = {'key': 0, 'open_price': 1, 'high_price': 2, 'low_price': 3, 'close_price': 4, 'volume': 5,
                      'sequence': 6, 'chart_time': 7, 'chart_day': 8}
        field_nums = [str(chart_dict[field]) for field in fields if field in chart_dict]

        # Build the request
        request = request = self._new_request_template()
        request['service'] = service
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def actives(self, service=None, venue=None, duration=None):

        # Build the request
        request = self._new_request_template()
        request['service'] = service
        request['command'] = 'SUBS'
        request['parameters']['keys'] = venue + '-' + duration
        request['parameters']['fields'] = '1'

        self.data_requests['requests'].append(request)

    def account_activity(self):

        # NOTE: If ACCT_ACTIVITY is one of the streaming requests, then the request MUST BE
        # on a SSL secure connection (HTTPS)

        # Build the request
        request = self._new_request_template()
        request['service'] = 'ACCT_ACTIVITY'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ''
        request['parameters']['fields'] = '0,1,2,3'

        self.data_requests['requests'].append(request)

    def chart_history(self, service=None, symbols=None, frequency=None, period=None):

        # NOTE: snapshot History via the stream server should no longer be used. Please use
        # PriceHistory instead

        # Build the request
        request = self._new_request_template()
        request['service'] = 'CHART_HISTORY_FUTURES'
        request['command'] = 'GET'
        request['parameters']['symbols'] = '/ES'
        request['parameters']['frequency'] = 'm1'
        request['parameters']['period'] = 'd1'

        self.data_requests['requests'].append(request)

    def level_one_quotes(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'QUOTE'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def level_one_options(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'OPTION'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def level_one_futures(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'LEVELONE_FUTURES'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def level_one_forex(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'LEVELONE_FOREX'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def level_one_futures_options(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'LEVELONE_FUTURES_OPTIONS'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def news_headline(self, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = 'NEWS_HEADLINE'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    def timesale(self, service=None, symbols=None, fields=None):

        field_nums = [str(field) for field in fields]

        # Build the request
        request = self._new_request_template()
        request['service'] = service
        request['command'] = 'SUBS'
        request['parameters']['keys'] = ','.join(symbols)
        request['parameters']['fields'] = ','.join(field_nums)

        self.data_requests['requests'].append(request)

    '''
        EXPERIMENTATION SECTION

        NO GUARANTEE THESE WILL WORK.
    '''

    def level_two_quotes(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'LISTED_BOOK'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'IBM'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    def level_two_quotes_nyse(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'NYSE_BOOK'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'IBM'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    def level_two_options(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'OPTIONS_BOOK'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'MSFT_013120C115'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    def level_two_nasdaq(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'NASDAQ_BOOK'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'MSFT'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    def level_two_futures(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'FUTURES_BOOK'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = '/ES'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    def level_two_forex(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'OPRA'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'EUR/USD'
        request['parameters']['fields'] = '0,1,2'

        self.data_requests['requests'].append(request)

    '''
        NOT WORKING
    '''

    def news_history(self):

        # OFFICIALLY DEAD

        # Build the request
        request = self._new_request_template()
        request['service'] = 'NEWS'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'IBM'
        request['parameters']['fields'] = 1576828800000

        self.data_requests['requests'].append(request)

    def level_two_quotes_nasdaq(self):

        # Build the request
        request = self._new_request_template()
        request['service'] = 'TOTAL_VIEW'
        request['command'] = 'SUBS'
        request['parameters']['keys'] = 'AAPL'
        request['parameters']['fields'] = '0,1,2,3'

        self.data_requests['requests'].append(request)
