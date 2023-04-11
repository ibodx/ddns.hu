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

app = Flask(__name__, template_folder='/root/ddnsApp')
api = Api(app)
app.secret_key = 'super secret key'
dnsserver_ip = '10.20.10.249'
zone = 'ddns.org'

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

@app.route('/update_record', methods=['POST'])
def update_record():
    # Get the domain name and new IP address from the form data
    domain_name = request.form['domain_name']
    new_ip_address = request.form['new_ip_address']

    # Get the user's email and access token from the session
    email = session.get('email')
    token = session.get('access_token')

    # Update the IP address of the matching record in the MongoDB collection
    dns_col.update_one({'email': email, 'domain_name': domain_name}, {'$set': {'ip_address': new_ip_address}})
    print(new_ip_address)

    # Update the A record in the DNS server
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver_ip]
    update = dns.update.Update(zone)
    update.replace(domain_name.rstrip('.ddns.org'),86400, dns.rdatatype.A, new_ip_address)
    response = dns.query.tcp(update, dnsserver_ip, timeout=5)
    print(response)

    # Thaw the zone
    subprocess.run(['rndc', 'thaw', zone])

    # Execute rndc sync command
    result = subprocess.run(['rndc', 'sync', zone])

    # Redirect the user back to the main page
    return redirect(url_for('index'))


@app.route('/remove_record', methods=['POST', 'DELETE'])
def remove_record():

    # Get the domain name from the form data
    domain_name = request.form['domain_name']

    # Get the user's email and access token from the session
    email = session['email']
    access_token = session['access_token']

    # Remove the matching record from the MongoDB collection
    dns_col.delete_one({'domain_name': domain_name})

    # Query the DNS records associated with the logged-in user's email
    dns_records = list(dns_col.find({'email': email}))

    # remove records from the DNS server
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dnsserver_ip]
    update = dns.update.Update(zone)
    update.delete(domain_name.rstrip('.ddns.org'))
    response = dns.query.tcp(update, dnsserver_ip, timeout=5)
    print(response)

    # Thaw the zone
    subprocess.run(['rndc', 'thaw', zone])

    # Execute rndc sync command
    result = subprocess.run(['rndc', 'sync', zone])

    # Redirect the user back to the main page
    return redirect(url_for('index'))

def verify_token(domain_name, access_token):
    # Look for document with given domain_name and access_token
    dns_record = dns_col.find_one({'domain_name': domain_name, 'access_token': access_token})

    if dns_record is None:
        return None
    else:
        return dns_record

# Resource for updating an existing DNS record (( API ))
class UpdateDNSRecord(Resource):
    def put(self):

        # Get info from Header
        data = request.get_json()
        domain_name = data['domain_name']
        new_ip_address = data['ip_address']
        access_token = None
        #  Extract the actual token value
        auth_header = request.headers.get('Authorization')
        if auth_header:
            access_token = auth_header.split(" ")[1]

        # Check token
        dns_record = verify_token(domain_name, access_token)
        print(dns_record)

        if dns_record is not None:
            result = dns_col.update_one({'domain_name': domain_name}, {'$set': {'ip_address': new_ip_address}})

            # update records in DNS server:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dnsserver_ip]
            update = dns.update.Update(zone)
            update.replace(domain_name.rstrip('.ddns.org'), 86400, dns.rdatatype.A, new_ip_address)
            response = dns.query.tcp(update, dnsserver_ip, timeout=5)
            # Thaw the zone
            subprocess.run(['rndc', 'thaw', 'ddns.org'])
            # Execute rndc sync command
            result = subprocess.run(['rndc', 'sync', zone])
            if response.rcode() == dns.rcode.NOERROR:
                return {'message': 'A record updated successfully. New IP now is: {}'.format( new_ip_address)}
            else:
                return {'message': 'A record update failed.'}, 500
        else:
            return {'message': 'Invalid token'}, 401


# Add resources to API
api.add_resource(UpdateDNSRecord, '/update_dns_record')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

