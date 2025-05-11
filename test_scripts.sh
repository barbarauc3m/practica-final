#!/bin/bash
# ==============================
# sequential_tests.sh
# Script de pruebas secuenciales para el cliente/servidor
# ==============================

SERVER=localhost
PORT=5000
CLIENT_CMD="python3 client.py -s $SERVER -p $PORT"

echo "--- Prueba: Registro usuario 'alice' ---"
echo -e "REGISTER alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Registro duplicado 'alice' ---"
echo -e "REGISTER alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Baja de usuario 'alice' ---"
echo -e "UNREGISTER alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Baja de usuario inexistente 'bob' ---"
echo -e "UNREGISTER bob
QUIT" | $CLIENT_CMD

echo "--- Prueba: Conectar usuario no registrado 'bob' ---"
echo -e "CONNECT bob
QUIT" | $CLIENT_CMD

echo "--- Prueba: Registro y conexión de 'alice' ---"
echo -e "REGISTER alice
CONNECT alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Conexión doble de 'alice' ---"
echo -e "CONNECT alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Publicar fichero 'doc.txt' ---"
echo -e "PUBLISH doc.txt Prueba_de_publicacion
QUIT" | $CLIENT_CMD

echo "--- Prueba: Publicar duplicado 'doc.txt' ---"
echo -e "PUBLISH doc.txt Prueba_de_publicacion
QUIT" | $CLIENT_CMD

echo "--- Prueba: Listar usuarios conectados ---"
echo -e "LIST_USERS
QUIT" | $CLIENT_CMD

echo "--- Prueba: Listar contenido de 'alice' ---"
echo -e "LIST_CONTENT alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Borrar fichero 'doc.txt' ---"
echo -e "DELETE doc.txt
QUIT" | $CLIENT_CMD

echo "--- Prueba: Listar contenido tras borrado ---"
echo -e "LIST_CONTENT alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Desconexión de 'alice' ---"
echo -e "DISCONNECT alice
QUIT" | $CLIENT_CMD

echo "--- Prueba: Baja de 'alice' final ---"
echo -e "UNREGISTER alice
QUIT" | $CLIENT_CMD

# ==============================
# concurrent_connect.sh
# Prueba de concurrencia: 100 clientes conectándose simultáneamente
# ==============================

# Registrar 100 usuarios
echo "Registrando 100 usuarios..."
for i in $(seq 1 100); do
  echo -e "REGISTER user$i
QUIT" | $CLIENT_CMD >/dev/null 2>&1
done
echo "Registro completado."


# Preparar directorio de logs
mkdir -p logs

# Conectar 100 usuarios en paralelo
echo "Iniciando conexiones concurrentes..."
for i in $(seq 1 100); do
  (
    echo -e "CONNECT user$i
QUIT" | $CLIENT_CMD > logs/connect_user$i.log 2>&1
  ) &
done

wait
echo "Todas las conexiones finalizadas."

