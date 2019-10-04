# Webtenna Example Script

The Webtenna Python project is an example script that demonstrates how you can use an offline computer with an attached [goTenna Mesh](http://gotennamesh.com) radio to make REST API calls via a mesh gateway. This script also provides a basic example of how to use an offline computer to run a [Blockstack DApp](https://docs.blockstack.org/develop/dapp_principles.html) in [Firefox](#firefox) via the goTenna Mesh network .

This project uses the goTenna [Public SDK](https://gotenna.com/pages/sdk#sdk-signup) and [mitmproxy](https://mitmproxy.org/) project as building blocks to proxy REST API calls over the mesh.

## <a name='Environment'></a>Environment

The first step in order to use the examples that follow is to prepare the environment.

For Python, create a virtual environment with the packages listed in the `requirements.txt` file of this directory. For example, if using *virtualenvwrapper*, run the following:

```
mkvirtualenv --python=`which python3` -r requirements.txt webtenna
```

Note this virtual environment will be required for all example scripts described in this page. Hence, once you open a new terminal session in order to launch txtenna.py, ensure you activate the environment again. For example, assuming you are using `virtualenvwrapper`, run the following on every new terminal session:

 ```
 workon webtenna
 ```
 
 Use the 'deactivate' command if you want to stop using the environment.

You will also need to do the following:

* request a free SDK Token, from goTenna [here](https://www.gotenna.com/pages/sdk).
* plug a [goTenna Mesh](https://gotennamesh.com) device into the USB port of your computer (RPi, PC, Mac, Linux, etc)
* both the off-grid and gateway nodes should use the same SDK Token and region values, otherwise they won't communicate.

> IMPORTANT: Make sure your goTennas are upgraded to firmware 1.1.12 or higher following the [instructions from the goTenna Python SDK](https://github.com/gotenna/PublicSDK/blob/master/python-public-sdk/Mesh%20Firmware%20Upgrade%20to%201.1.12.pdf).

> WARNING: This project has not had a professional security review and should only be used for research and testing.

# How does it work
  
    $ workon webtenna
    $ python webtenna.py -h
    
    To launch off-grid script through mitmproxy:
        $ mitmproxy --ssl-insecure -s webtenna.py --set sdk_token=<sdk token> --set gid=<gid> --set region=<region id>
        
    To launch on-grid gateway:
        $ webtenna.py --sdk_token=<sdk token> --gid=<gid> --region=<region id>

    arguments:
        <sdk token>           The token for the goTenna SDK from 
        <gid>                 Unique GID for node (eg. 1234567890)
        <region id>           The geo region number you are in (eg. 1 = USA, 2 = EU )

# Troubleshooting

* You may need to install the [77-gotenna.rules](https://github.com/gotenna/PublicSDK/blob/master/python-public-sdk/77-gotenna.rules) file for linux systems that use the udev device manager.
* If you change your SDK Token, delete the .goTenna file created by txtenna.py .
* Either use sudo to run Python or use chmod to grant access to your USB serial device if you see this error:

        SerialException: [Errno 13] could not open port /dev/ttyACM0: [Errno 13] Permission denied: '/dev/ttyACM0'
        ERROR:goTenna.driver.Driver:Failed to connect to device!
* You can plug in two goTennas and test communication between them from different shell windows.

# Curl

Some tips for using curl to test webtenna:

Test in curl with:

    $ curl -x http://127.0.0.1:8080 https://core.blockstack.org/v1/names/aaron.id
        Or
    $ curl -x http://127.0.0.1:8080 https://hub.blockstack.org/hub_info

# Firefox

Some tips for using [Firefox](https://www.mozilla.org/) to test webtenna with a [Blockstack DApp](https://docs.blockstack.org/develop/dapp_principles.html):

You may first need to add the mitm proxy cert located in ~/.mitmproxy to the Firefox trusted certificates.

You should setup a manual HTTP proxy configuration to 127.0.0.1 and port 8080 for all protocols.

From the 'About:config' menu, set the following settings to minimize bandwidth and increase timeouts:

* toolkit.telemetry.archive.enabled = false
* toolkit.telemetry.enabled = false
* toolkit.telemetry.rejected = true
* toolkit.telemetry.server = <clear value>
* toolkit.telemetry.unified = false
* toolkit.telemetry.unifiedIsOptIn = false
* Toolkit.telemetry.prompted = 2
* Toolkit.telemetry.rejected = true
* Network.captive-portal-service.enabled = false
* Network.http.max-persistent-connections-per-server = 1
* Network.http.response.timeout = 300

From 'About:preferences#privacy'
* set 'Content Blocking' to 'Strict'
* untick all the checkboxes under "Firefox Data Collection and Use" and restart Firefox.