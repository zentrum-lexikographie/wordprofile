#!/usr/bin/python

import getpass
import logging
import time
import xmlrpc.server
from argparse import ArgumentParser

from wp_server import WortprofilQuery

parser = ArgumentParser()
parser.add_argument("--user", type=str, help="database username", required=True)
parser.add_argument("--database", type=str, help="database name", required=True)
parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
parser.add_argument("--db-hostname", default="localhost", type=str, help="XML-RPC hostname")
parser.add_argument("--passwd", action="store_true", help="ask for database password")
parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
parser.add_argument('--spec', type=str, required=True, help="Angabe der Settings-Datei (*.xml)")
parser.add_argument('--log', dest='logfile', type=str,
                    default="./log/wp_" + time.strftime("%d_%m_%Y") + ".log",
                    help="Angabe der log-Datei (Default: log/wp_{date}.log)")
args = parser.parse_args()

logger = logging.getLogger('wordprofile')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
fh = logging.FileHandler(args.logfile)
ch.setLevel(logging.DEBUG)
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)
logger.addHandler(fh)


class RequestHandler(xmlrpc.server.SimpleXMLRPCRequestHandler):
    # Restrict to a particular path.
    rpc_paths = ('/RPC2',)

    def do_POST(self):
        client_ip, port = self.client_address
        # Log client IP and Port
        logger.info('Client IP: %s - Port: %s' % (client_ip, port))
        try:
            # get arguments
            data = self.rfile.read(int(self.headers["content-length"]))
            # Log client request
            logger.info('Client request: \n  %s\n' % data)

            response = self.server._marshaled_dispatch(
                data, getattr(self, '_dispatch', None)
            )
        except:  # This should only happen if the module is buggy
            # internal error, report as HTTP server error
            self.send_response(500)
            self.end_headers()
        else:
            # got a valid XML RPC response
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)


def main():
    logger.info('user: ' + args.user)
    logger.info('db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user

    # Create server
    server = xmlrpc.server.SimpleXMLRPCServer((args.hostname, int(args.port)),
                                              requestHandler=RequestHandler, logRequests=False, allow_none=True)
    # register function information
    server.register_introspection_functions()
    # register wortprofil
    server.register_instance(
        WortprofilQuery(args.db_hostname, args.user, db_password, args.database, args.port, args.spec))
    # Run the server's main loop
    server.serve_forever()


if __name__ == '__main__':
    main()
