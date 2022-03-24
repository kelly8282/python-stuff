import socket  ##required
import argparse ##gets argument from command line
import sys  ##system calls
import re  ## parsing string

BUFF_SIZE = 4096
TIMEOUT_SIZE = 2

neededInfo = { #contains everything that i need in my log 
    'url':None,
    'sName':None,
    'sIp':None, 
    'sPort':None,
    'Path':None, 
    'cIp':None,
    'cPort':None,
    'msg':None,
    'html_msg':None
}

parser = argparse.ArgumentParser(description='Getting the HTTP request input')
parser.add_argument('input', type=str, help='User input', nargs='+')
cmd_input = parser.parse_args().input

url = cmd_input[0]


http_exists = True
parsed = re.search(r"(?P<http>https*)://?(?P<site>(\w+\.?)+):?(?P<port>\d*)?(?P<path>/.*)?", url)

if(parsed == None):
    http_exists = False
    parsed = re.search(r"(?P<site>(\w+\.?)+):?(?P<port>\d*)?(?P<path>/.*)?", url)

#regex checking if they exist thru regex
check_host = re.findall("[a-z]+\.\w+\.[a-z]+", url) 
check_domain = re.findall("([a-zA-Z0-9]+\.[a-z]+)", url) 
check_ip = re.findall("([0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3})", url)

if (len(check_host) == 0 and len(check_domain) == 0 and len(check_ip) == 0):
    sys.exit("Couldn't find host " + url)

if(parsed == None):
    sys.exit("Parsed argument errored.")

if(http_exists == True):
    rawr = parsed.group('http')
    https_true = False ##cannot support https check if it is and if so print error
    if( rawr == "https"):
        https_true = True
    if (https_true == True ):
        sys.exit("HTTPS is not supported.")

##Port settings
rawr = parsed.group('port')
port_true = False
port_empty = False
if( rawr == None):
    port_empty = True
if( rawr == "443" ):
    port_true = True

if(port_empty == True):
    neededInfo['sPort'] = int(parsed.group('port'))
else:
    neededInfo['sPort'] = 80


# set sName and sIp
multi_input = False
rawr = parsed.group('site')
if(len(cmd_input) ==2):
    multi_input = True
if(multi_input == False):
    neededInfo['sName'] = rawr
    neededInfo['sIp'] = socket.gethostbyname(neededInfo['sName'])
if(multi_input == True):
    if (re.match("[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}", rawr)):
        neededInfo['sName'] = cmd_input[1]
        neededInfo['sIp'] = rawr
    else:
        neededInfo['sName'] = rawr
        neededInfo['sIp'] = cmd_input[1]

# setting path
rawr = parsed.group('path')
path_empty = False
if(rawr == None):
    path_empty = True
if(path_empty == True):
    neededInfo['Path'] = "/"
else:
    neededInfo['Path'] = rawr

sock =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)  


#start connection between source and and host 
sock.connect((neededInfo['sIp'], neededInfo['sPort']))
sock.settimeout(TIMEOUT_SIZE)
neededInfo['cIp'], neededInfo['cPort'] = sock.getsockname() #gets cip and cport

request = "GET {} HTTP/1.1\r\nHost:{}\r\n\r\n".format(neededInfo['Path'], neededInfo['sName'])
sock.send(request.encode()) #changing request (type string) need to encode to a byte 

#if the port is bad, we print to our Log file with the respective parameters
if(port_true == True):
    log = "Unsuccessful, 56, {}, {}, {}, {}, {}, {}, [Errno 54] Connection reset by peer\n\n".format(url,
    neededInfo['sName'], str(neededInfo['cIp']), str(neededInfo['sIp']), str(neededInfo['cPort']), 
    str(neededInfo['sPort']))
    f = open("Log.csv", "a")
    f.write(log)
    f.close()
    sys.exit("Port not supported")

#get the header
neededInfo['msg'] = ""
try:
    while True:
        pack = sock.recv(1) #getting one byte
        if("\r\n\r" in neededInfo['msg'] or pack == None): #see \r\n\r signals the end of the header file
            break
        neededInfo['msg'] = neededInfo['msg'] + pack.decode()
except:
    sock.close()
    sys.exit("Could not receieved information from message.")

msg_true = re.search(r"Content-Length: (\d+)",neededInfo['msg']) #get content length

msg_exists = False
if(msg_true != None):
    msg_true = int(msg_true.group(1))-len(neededInfo['msg'].encode())
    msg_exists = True

#get the rest of the message in html format if it exists 
neededInfo['html_msg'] = ""
if(msg_exists == True):
    try:
        while True:
            pack = sock.recv(BUFF_SIZE)
            len_size = False
            if (len(pack) == BUFF_SIZE):
                len_size = True
            if (len_size == False):
                neededInfo['html_msg'] = neededInfo['html_msg']+ pack.decode()
                break
            neededInfo['html_msg'] = neededInfo['html_msg']+ pack.decode()
    except Exception as e:
        sock.close()
        sys.exit("Could not receieved information from message.")
    # http_out = http_out + pack.decode()
    # neededInfo['html_msg'] = neededInfo['html_msg']+ pack.decode()

sock.close()

#set stattus based on above
http_status = re.search(r"(HTTP/.*)?", neededInfo['msg']).group(1)

#print the html content into my httpoutput.html file
f = open("HTTPoutput.html", "w")
f.write(neededInfo['html_msg'])
f.close()

#print to my log file with respective parameters
log = ""
print_message = ""

status_code = re.search(r"HTTP/\d{1}.?\d? (\d*)? \w+", http_status).group(1)

success = True
if(status_code != '200'):
    success = False
if(success == True):
    run_status = "Successful"
if(success == False):
    run_status = "Unsuccessful"

term_out = run_status + " " + url + " " + http_status
print(term_out)
if "chunked" in neededInfo['msg']:
    print("ERROR: Chunk encoding is not supported")


log = log +run_status + " "
log = log+ status_code + " "
log = log+ url + " "
log = log+ neededInfo['sName'] + " "     
log = log+ str(neededInfo['cIp']) + " " 
log = log+ str(neededInfo['sIp']) + " "    
log = log+ str(neededInfo['cPort']) + " "  
log = log+ str(neededInfo['sPort']) + " "    
log = log+ http_status                               
log = log + "\n\n"
f = open("Log.csv", "a")
f.write(log)
f.close()

