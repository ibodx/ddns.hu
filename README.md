DDNS App

This is a dynamic DNS (DDNS) app that allows users to associate a dynamic IP address (which changes frequently) with a static hostname. This enables you to access devices or services on your home network, such as a web server or a remote desktop, using a memorable hostname (e.g., myserver.duckdns.org) instead of having to remember a string of numbers (i.e., the IP address). For storing data I was using MongoDB Atlas database (Cloud version). The app uses Flask for web development and Authomatic for Oauth 2.0 authentication. The app also includes a RESTful API, which enables users to update existing DNS records.

Getting Started
To run the app, follow these steps:

1. Install the required Python packages listed in requirements.txt.
2. Set up a MongoDB database and update the connection_string variable in the app.py file with your database connection string.
3. Create an oauth_config.py file with your authentication provider's configuration details. Refer to the oauth_config.py file for an example of how to structure this file.
4. Run the app by executing the app.py file.

Features
The DDNS app allows users to:

- Log in with various authentication providers.
- Add new DNS records by entering a domain name and IP address.
- Update the IP address of an existing DNS record by specifying the domain name and new IP address.
- Remove an existing DNS record by specifying the domain name.
- Use the API to update the IP address of an existing DNS record.

API Usage
The DDNS app includes a RESTful API that enables users to update existing DNS records. To use the API, send a PUT request to /api/update_dns_record, including the following parameters in the request body:

- domain_name: The domain name associated with the DNS record to update.
- ip_address: The new IP address to associate with the DNS record.
- token you have gotten after logging in that is associated with your e-mail address

If the update is successful, the API will return a response with a status code of 200. Otherwise, it will return a response with an appropriate error code and message.


Example: (It might be handy to take a look at the screendumps)

If you add a new dns record (subdomain) - let's say 'test.com'; this will then be added as a FQDN eg. 'test.com.ddns.org' (in my case 'ddns.org') with the ip-address you provided. 
So you actually don't need to fully write the whole FQDN when adding it throug the website or the API. The backend code will take care of the rest.
