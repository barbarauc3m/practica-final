# test6.sh: Prueba descarga de archivo inexistente
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test6: Intentar descargar archivo que no existe =="
$CLIENT <<EOF
REGISTER frank
CONNECT frank
LIST_CONTENT frank
GET_FILE frank nofile.txt new.txt
DISCONNECT frank
UNREGISTER frank
QUIT
EOF

