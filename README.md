**DDNS App**

This is a dynamic DNS (DDNS) app that allows users to update their IP address and domain name in a MongoDB database. The app uses Flask for web development and Authomatic for authentication. The app also includes a RESTful API, which enables users to update existing DNS records.

Getting Started
To run the app, follow these steps:

Install the required Python packages listed in requirements.txt.
Set up a MongoDB database and update the connection_string variable in the app.py file with your database connection string.
Create an oauth_config.py file with your authentication provider's configuration details. Refer to the config.py.example file for an example of how to structure this file.
Run the app by executing the app.py file.
Features
The DDNS app allows users to:

Log in with various authentication providers.
Add new DNS records to the database by entering a domain name and IP address.
Update the IP address of an existing DNS record by specifying the domain name and new IP address.
Remove an existing DNS record by specifying the domain name.
Use the API to update the IP address of an existing DNS record.
API Usage
The DDNS app includes a RESTful API that enables users to update existing DNS records. To use the API, send a PUT request to /api/update_record, including the following parameters in the request body:

domain_name: The domain name associated with the DNS record to update.
ip_address: The new IP address to associate with the DNS record.
In addition, you must include an Authorization header with a valid access token for the DNS record you wish to update.

If the update is successful, the API will return a response with a status code of 200. Otherwise, it will return a response with an appropriate error code and message.
