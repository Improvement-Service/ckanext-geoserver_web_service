# ckanext-geoserver_webservice

A Simple Exentension that allows you to use your ckan apikeys with geoserver-authkey extension. sysadmin will have the ability to add and remove roles from a user using the new geoserver_roles tab located on the user read page. 



## Requirements

A running geoserver instance with [geoserver authkey module](https://docs.geoserver.org/latest/en/user/extensions/authkey/index.html) installed. 

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.6 and earlier | not tested    |
| 2.7             | not tested    |
| 2.8             | not tested    |
| 2.9             | yes           |       


## Installation

To install ckanext-geoserver_webservice:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/n00dl3nate@gmail.com/ckanext-geoserver_webservice.git
    cd ckanext-geoserver_webservice
    pip install -e .
	pip install -r requirements.txt

3. Add `geoserver_webservice` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

	# A List of default roles that will be available to all ckan users.
	ckanext.geoserver_webservice.default_roles = CKAN
    # Role options that can be added to a ckan user.
    ckanext.geoserver_webservice.role_options = PSGA SGN
    # whether a user can view roles they have assinged to them 
    ckanext.geoserver_webservice.user_view_roles = false



## Developer installation

To install ckanext-geoserver_webservice for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/n00dl3nate@gmail.com/ckanext-geoserver_webservice.git
    cd ckanext-geoserver_webservice
    python setup.py develop
    pip install -r dev-requirements.txt


## Geoserver Setup

### Create new user group service

In geoserver GUI goto security > Users, Groups, Roles and add a new group service. Select AuthKEY WebService Body Response and input these details into the correct fields. <br>
name: ckan_webservice_group <br>
password encryption: digest<br>
password policy: default<br>
Web Service Response Roles Search Regular Expression: ^.*?\"roles\"\s*:\s*\"([^\"]+)\".*$ <br>

### Create New Authentication Filter
In geoserver GUI goto security > Authentication and add a new Authentication Filter. Select AuthKEY as Authentication filter type input these details into the correct fields. <br>
name: ckan_authkey_filter <br>
name of url parameter: authkey <br>
authentication key to use mapper: Web Service <br>
web Service URL: http://<your_ckan_instance>/api/3/action/geoserver_webservice?authkey={key} <br>
web service response user search regular expression: ^.*?\"username\"\s*:\s*\"([^\"]+)\".*$ <br>
read timeout: 10 <br>
connection timeout: 5 <br>
user/group service: ckan_webservice_group <br>

Now you will just need to create some roles and data access rules.

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-geoserver_webservice

If ckanext-geoserver_webservice should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
