import pymongo
import subprocess
from flask import Flask, render_template, request, session, redirect, url_for, make_response
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
from flask_restful import reqparse, abort, Api, Resource
from functools import wraps
from pymongo import MongoClient, collection
import authomatic
from oauth_config import CONFIG
from datetime import datetime
import dns
import dns.resolver
import dns.update

# Instantiate Authomatic.
authomatic = Authomatic(CONFIG, 'Welkom#1', report_errors=False)

# Connect to MongoDB
connection_string = "mongodb+srv://ibrahemalloush:Welkom1@clustertest.umprcd2.mongodb.net/"
client = pymongo.MongoClient(connection_string)
db = client['dnsTest']
dns_col = db['dns_records']

app = Flask(__name__, template_folder='/root/testApp')
api = Api(app)
app.secret_key = 'super secret key'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    # We need response object for the WerkzeugAdapter.
    response = make_response()
    # Log the user in, pass it the adapter and the provider name.
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)

    # If there is no LoginResult object, the login procedure is still pending.
    if result:
        if result.user:
            # We need to update the user to get more info.
            result.user.update()

            # Store the result object in the session for later use
            #session['result'] = result.

            # Store the necessary information in the session for later use
            session['email'] = result.user.email
            session['access_token'] = result.user.credentials.token

            # get info out of the header and save in DB
            email = result.user.email

            # Query the DNS records associated with the logged-in user's email
            dns_records = list(dns_col.find({'email': email}))

        # The rest happens inside the template.
        return render_template('login.html', result=result, dns_records=dns_records)

    # Don't forget to return the response.
    return response


@app.route('/add_record', methods=['POST', 'DELETE'])
def add_record():
    # Get the domain name and IP address from the form data
    domain_name = request.form['domain_name']
    ip_address = request.form['ip_address']

    # Get the user's email and access token from the session
    email = session.get('email')
    token = session.get('access_token')

    # Get the current date and time
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Insert the new record into the MongoDB collection
    record = {'email': email, 'domain_name': domain_name + '.ddns.org', 'ip_address': ip_address, 'access_token': token,
              'last_change': now}
    dns_col.insert_one(record)

    # Add the A record to the DNS server
    dnsserver_ip = '10.20.20.1'
    zone = 'ddns.org'
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver_ip]
    update = dns.update.Update(zone)
    update.add(domain_name, 86400, dns.rdatatype.A, ip_address)
    response = dns.query.tcp(update, dnsserver_ip,timeout=5)
    print(response)

    # Thaw the zone
    subprocess.run(['rndc', 'thaw', 'ddns.org'])
   
    # Execute rndc sync command
    result = subprocess.run(['rndc', 'sync', zone])

   # Redirect the user back to the main page
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc', host='0.0.0.0', port=5000)

