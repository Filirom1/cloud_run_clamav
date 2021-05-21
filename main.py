import os
import clamd
import subprocess
import datetime
import google.cloud.storage
from flask import Flask, request

def get_timestamp():
    return datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S UTC")

def parse_resource_name(path):
    _, _, _, b, _, *o = path.split("/")
    key = "/".join(o)
    client =  google.cloud.storage.Client()
    return client.bucket(b).get_blob(key)

def start_clamd():
    print("clamd starting")
    process = subprocess.Popen(["/usr/sbin/clamd","--foreground"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        line = process.stdout.readline()
        if line:
            pass
            #print(line.decode("utf-8").replace('\n', ''))
        if b"TCP: Bound to" in line:
            print("clamd started")
            break

app = Flask(__name__)
start_clamd()

@app.route('/', methods=['POST'])
def post_http():
    method_name = request.headers.get('ce-methodname')
    resource_name = request.headers.get('ce-resourcename')
    print(f"{method_name} : {resource_name}")
    if method_name != 'storage.objects.create':
        return "BYE"

    blob = parse_resource_name(resource_name)
    if not blob:
        print(f"{resource_name} is null")
        return "NULL"

    print(f"SCAN {blob}")
    cd = clamd.ClamdNetworkSocket(host="127.0.0.1", port=3310)
    cd.ping()
    status = "CLEAN" 
    signataure = "N/A"
    with blob.open("rb", chunk_size=1024) as f:
        cd_response = cd.instream(f)
        cd_status = cd_response['stream']
        if 'FOUND' in cd_status:
            status = "INFECTED"
            signature = cd_status[1]

    metadata = { "timesetamp": get_timestamp(), "status": status, "signature": signataure}
    print(f"Update METADATA {blob}: {metadata}")
    blob.metadata = metadata
    blob.patch()
    return f"DONE {blob}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
