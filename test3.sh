# test3.sh: Prueba descarga de archivo correcta
#!/bin/bash
SERVER=localhost
PORT=5000
CLIENT="python3 client.py -s $SERVER -p $PORT"

echo "== Test3: Prueba descarga de archivo correcta =="

# Crear FIFO para Alice
echo "Preparando cliente Alice..."
FIFO=alice.fifo
rm -f $FIFO
mkfifo $FIFO
# Lanzar cliente Alice leyendo del FIFO
echo "Iniciando Alice client en background"
$CLIENT < $FIFO > alice.log 2>&1 &
ALICE_PID=$!

# Enviar comandos a Alice via FIFO
echo -e "REGISTER alice
CONNECT alice
PUBLISH archivo.txt Informe2025
" > $FIFO
# Esperar a que Alice esté escuchando
echo "Esperando que Alice arranque listener..."
sleep 2

# Bob: registrar, conectar y descargar
echo "Ejecutando Bob..."
$CLIENT <<EOF
REGISTER bob
CONNECT bob
GET_FILE alice archivo.txt downloaded_archivo.txt
DISCONNECT bob
UNREGISTER bob
QUIT
EOF

# Finalizar Alice: desconectar y unregister
echo "Cerrando Alice..."
echo -e "DISCONNECT alice
UNREGISTER alice
QUIT
" > $FIFO
sleep 1
kill $ALICE_PID 2>/dev/null
rm -f $FIFO