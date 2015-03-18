# GroupMe Desktop Client #

A desktop application for the [GroupMe](https://groupme.com) messaging service.
Written in Python 3 and [wxPython (Phoenix)](http://wxpython.org/Phoenix/docs/html/index.html).
Uses [Groupy](https://pypi.python.org/pypi/GroupyAPI), an excellent GroupMe API wrapper for Python 3.

## Why? ##
I think a native desktop group chat client makes a team (especially of programmers) much more productive.
I set out to build a chat client like that of [HipChat](https://www.hipchat.com/downloads), but this is a long way from that.

## Development environment setup ##
1. [Create an application on GroupMe](https://dev.groupme.com/applications). Fill in the required details.
   Any URL should work for the Callback URL, but for some reason `localhost` does not.
2. [Install Python 3 (with pip)](https://www.python.org/downloads/)
3. Install dependencies  
  `pip install -r requirements.txt`
4. Copy `src/config_template.py` to `src/config.py`
5. Copy and paste the Redirect URL and Callback URL from the details page of the GroupMe application you just created into the relevant places in `src/config.py`.

## License ##
&copy; 2015, Neelabh Gupta. Open source license coming soon.
