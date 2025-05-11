# test7.sh: Prueba eliminar archivo inexistente
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test7: Intentar eliminar archivo que no existe =="
$CLIENT <<EOF
REGISTER grace
CONNECT grace
LIST_CONTENT grace
DELETE ghost.txt
DISCONNECT grace
UNREGISTER grace
QUIT
EOF