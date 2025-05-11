
# test4.sh: Prueba eliminación de archivo correcta
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test4: Prueba eliminación de archivo correcta =="
$CLIENT <<EOF
REGISTER dave
CONNECT dave
PUBLISH temp.txt "Temporal"
LIST_CONTENT dave
DELETE temp.txt
LIST_CONTENT dave
DISCONNECT dave
UNREGISTER dave
QUIT
EOF
