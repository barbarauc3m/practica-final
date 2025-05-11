# test2.sh: Prueba listado de archivos correcto
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test2: Prueba listado de archivos correcto =="
$CLIENT <<EOF
REGISTER carol
CONNECT carol
PUBLISH file1.txt "Descripción 1"
PUBLISH file2.txt "Descripción 2"
LIST_CONTENT carol
DISCONNECT carol
UNREGISTER carol
QUIT
EOF