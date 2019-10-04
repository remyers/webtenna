from connection import Connection
import base58
import getopt
import json
import pickle
from mitmproxy import flowfilter, http, ctx
import requests 
import threading
import time
import sys
from utilities import hexdump, naturalsize

MAGIC = b'http  '
METHODS = ('POST', 'GET', 'PUT', 'OPTIONS')

class Webtenna:

    def __init__(self):
        self.remote_host=""
        self.connection = Connection(server=1)
        self.queue = self.connection.events.socket_queue
        self.threads = []

    def start_gateway(self, sdk_token, gid, region):
        # connect to goTenna
        self.connection.sdk_token(sdk_token)
        self.connection.set_gid(int(gid))
        self.connection.set_geo_region(int(region))

        t = threading.Thread(target=self.process_requests, args=())
        t.start()

    def process_requests(self):
        while True:
            if self.queue.empty():
                time.sleep(10)
            else:
                data = self.queue.get()
                print(f"[GATEWAY] process_requests: received web request from mesh {naturalsize(len(data))}")

                url_len = int.from_bytes(data[0:4], byteorder='big', signed=False)
                url = data[4:4+url_len]
                method_index = int.from_bytes(data[4+url_len:5+url_len], byteorder='big', signed=False)
                mp_data_serialized = data[5+url_len:]
                mp_data = pickle.loads(mp_data_serialized)

                if METHODS[method_index] == 'GET':
                    data = requests.get(url)
                elif METHODS[method_index] == 'POST':
                    data = requests.post( url, data=mp_data )
                elif METHODS[method_index] == 'OPTIONS':
                    data = requests.options( url )
                elif METHODS[method_index] == 'PUT':
                    data = requests.put( url, data=mp_data )
                else:
                    data = requests.get(url)

                response_data = MAGIC + data.status_code.to_bytes(4, byteorder='big', signed=False) + data.text.encode('utf-8')
                if len(response_data) > 210*11:
                    response_data = MAGIC + int(413).to_bytes(4, byteorder='big', signed=False)
                
                print(f"[GATEWAY] process_requests: send response {naturalsize(len(response_data))}")
                self.connection.send_jumbo((base58.b58encode_check(response_data)).decode())

            time.sleep(1)

    """
    This example shows how to send a reply from the proxy immediately
    without sending any data to the remote server.
    """
    def request(self, flow):
        # pretty_url takes the "Host" header of the request into account, which
        # is useful in transparent mode where we usually only have the IP otherwise.
        url_filter=['.ico','.png','.jpg','.gif']
        if self.remote_host in flow.request.pretty_url:
            if any(x in flow.request.pretty_url for x in url_filter):
                # construct error response from request sent to mesh
                flow.response = http.HTTPResponse.make(
                    413,  # status code: request too large
                    "",  # (optional) content
                    {'content-type': 'text/plain'}  # (optional) headers
                )
                return

            flow.intercept()
            mp_data = dict(flow.request.multipart_form.fields)
            data = self.receiver(method=flow.request.method, url=flow.request.pretty_url, mp_data=mp_data)
            t = threading.Thread(target=self.response_thread, args=(flow,))
            self.threads.append(t)
            t.start()

    def receiver(self, method, url, mp_data):
        """Receives messages from the socket and sends them out-of-band
        """

        print("[MESH] recv socket: started!")
        url_len_bytes = len(url).to_bytes(4, byteorder='big', signed=False)
        mp_data_serialized=pickle.dumps(mp_data)
        method_val = METHODS.index(method).to_bytes(1, byteorder='big', signed=False)
        data = url_len_bytes + url.encode('utf-8') + method_val + mp_data_serialized

        print(f"[MESH] recv socket: received {naturalsize(len(data))} of data.")
        hexdump(data)
        final_data = MAGIC + data
        print(f"[MESH] recv socket: sending data to mesh network")
        # send data received from the socket out of band
        self.connection.send_jumbo((base58.b58encode_check(final_data)).decode())

    def response_thread(self, flow):
        while True:
            if self.queue.empty():
                time.sleep(10)
            else:
                data = self.queue.get()
                print(f"[MESH] process_response: received web response from mesh {naturalsize(len(data))}")

                status_code = int.from_bytes(data[0:4], byteorder='big', signed=False)
                text = data[4:]

                # construct response from request sent to mesh
                flow.response = http.HTTPResponse.make(
                    status_code,  # (optional) status code
                    text,  # (optional) content
                    {'content-type': 'application/json'}  # (optional) headers
                )

                # resume flow and exit loop
                flow.resume()
                break

    def load(self, loader):
        ctx.log.info("Registering options")
        loader.add_option("remote_host", str, "", "Only proxy remote hosts that match filter.")
        loader.add_option("sdk_token", str, "", "goTenna SDK Token.")
        loader.add_option("gid",int, 0, "goTenna GID.")
        loader.add_option("region",int, 0, "goTenna Geographic Region Id")

    def configure(self, updated):
        if "remote_host" in updated:
            ctx.log.info("'remote_host' option value: %s" % ctx.options.remote_host)
            self.remote_host = ctx.options.remote_host
        if "sdk_token" in updated:
            ctx.log.info("'sdk_token' option value: %s" % ctx.options.sdk_token)
            self.connection.sdk_token(ctx.options.sdk_token)
        if "gid" in updated:
            ctx.log.info("'gid' option value: %s" % ctx.options.gid)
            self.connection.set_gid(int(ctx.options.gid))
        if "region" in updated:
            ctx.log.info("'region' option value: %s" % ctx.options.region)
            self.connection.set_geo_region(int(ctx.options.region))

if __name__ == "__main__":
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv,"ht:g:r:",["sdk_token=","gid=","region="])
    except getopt.GetoptError:
        print ('webtenna.py --sdk_token=<sdk token> --gid=<gid> --region=<region id>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('\nTo launch off-grid script through mitmproxy:')
            print ('\t$ mitmproxy --ssl-insecure -s webtenna.py --set sdk_token=<sdk token> --set gid=<gid> --set region=<region id>')
            print ('\nTo launch on-grid gateway:')
            print ('\t$ webtenna.py --sdk_token=<sdk token> --gid=<gid> --region=<region id>')
            print ('\narguments:')
            print ('\t<sdk token>           The token for the goTenna SDK from')
            print ('\t<gid>                 Unique GID for node (eg. 1234567890)')
            print ('\t<region id>           The geo region number you are in (eg. 1 = USA, 2 = EU )')
            sys.exit()
        elif opt in ("-t", "--sdk_token"):
            sdk_token = arg
        elif opt in ("-g", "--gid"):
            gid = int(arg)
        elif opt in ("-r", "--region"):
            region = int(arg)

    webtenna=Webtenna()
    webtenna.start_gateway(sdk_token, gid, region)

else:
    addons = [
        Webtenna()
    ] 