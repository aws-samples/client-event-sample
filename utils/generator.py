import argparse
import boto3
import json
import random
import time
import requests

class Options:
    minutes = 0
    entries = 0
    errors = False

options = Options()

parser = argparse.ArgumentParser(description='Generate analytic events for EventBridge, sending every 10s')
parser.add_argument('--minutes', help='minutes to run for', type=int)
parser.add_argument('--batch', help='size of batch generate, max of 10', type=int)
parser.add_argument('--loyalty', help='include loyalty purchases')
parser.add_argument('--userid', help='userid to send events from')
parser.add_argument('--password', help='user password')
parser.add_argument('--region', help='region where EB Analytics is deployed')
parser.add_argument('--appclientid', help='application clientID for userpool')
parser.add_argument('--apiid', help='API ID for API Gatway instance')

args = parser.parse_args()
print(f'{args.minutes}')

class Generator:
    minutes = 0
    batch = 0
    loyalty = False
    user_id = ""
    password = ""
    region = ""
    app_client_id = ""
    api_id = ""
    event_types = ['shopping', 'searching', 'paging', 'purchase']
    event_types_purchases = ['shopping', 'searching', 'paging', 'purchase', 'loyaltypurchase']
    use_event_types = []
    search_detail_terms = ['games',' books', 'movies', 'music']
    cognito = boto3.client('cognito-idp')
    headers = {}
    url = ""
    
    def __init__(self, args):
        self.minutes = args.minutes
        self.batch = args.batch
        if self.batch > 10:
            self.batch = 10
        if args.loyalty.lower() == "true":
            self.loyalty = True
        else:
            self.loyalty = False
        self.user_id = args.userid
        self.password = args.password
        self.region = args.region
        self.app_client_id = args.appclientid
        self.api_id = args.apiid
        if self.loyalty:
            self.use_event_types = self.event_types_purchases
        else:
            self.use_event_types = self.event_types
        self.url = f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/prod/event"
        print('Generator Initialized')

    def login(self):
        results = self.cognito.initiate_auth(AuthFlow='USER_PASSWORD_AUTH', ClientId=self.app_client_id,
            AuthParameters={'USERNAME': self.user_id, 'PASSWORD': self.password})
        self.headers["Authorization"] = f"{results['AuthenticationResult']['AccessToken']}"
        self.headers["Content-Type"] = "application/json"
        print('Authorization Successful')
        
    def generate_events(self):
        curr_time = time.time()
        random.seed()
        stop_time = curr_time + (60 * self.minutes)
        while curr_time <= stop_time:
            print('Generating a new batch')
            entry_array = []
            for i in range(0, self.batch):
                event_type = random.choice(self.use_event_types)
                entry = ""
                if event_type == 'shopping':
                    entry = {"entry": "{\"eventType\": \"shopping\", \"schemaVersion\":1, \"data\": {\"itemSku\":123}}}"}
                elif event_type == 'searching':
                    entry = {"entry": "{\"eventType\": \"searching\", \"schemaVersion\":1, \"data\": {\"searchTerm\":\"games\"}}"}
                elif event_type == 'paging':
                    entry = {"entry": "{\"eventType\": \"paging\", \"schemaVersion\":2 ,\"data\": {\"searchTerm\":\"games\", \"page\": 3}}"}
                elif event_type == 'purchase':
                    entry = {"entry": "{\"eventType\": \"purchase\", \"schemaVersion\":2 ,\"data\": {\"itemSku\":123}}"}
                elif event_type == 'loyaltypurchase':
                    entry = {"entry": "{\"eventType\": \"loyaltypurchase\", \"schemaVersion\":2 ,\"data\": {\"itemSku\":123}, \"ticket\" : {\"ticket\": {\"subject\": \"Loyalty customer purchase\", \"comment\": {\"body\": \"This customer has made a loyalty purchase\"}}}}"}
                print(entry)
                entry_array.append(entry)
            print('sending events')
            data = { "entries" : entry_array }
            data = json.dumps(data)
            print(f"posting {data}")
            response = requests.post(self.url, data=data, headers=self.headers)
            print(response)
            print(response.json())
            time.sleep(10)
            curr_time = time.time()
            
def main():
    generator = Generator(args)
    generator.login()
    generator.generate_events()

if __name__ == "__main__":
    main()
    
