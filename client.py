# python3 client.py -s localhost -p 5000

from enum import Enum
import argparse
# Nuevos imports
import socket
import threading
import os
import requests

def get_datetime_from_web():
    try:
        response = requests.get("http://127.0.0.1:8000/datetime", timeout=2)
        response.raise_for_status()
        data = response.json()
        # 'datetime' es la clave que devuelve FastAPI
        return data.get("datetime", "00/00/0000 00:00:00")
    except Exception:
        return "00/00/0000 00:00:00"



class client :

    # ******************** TYPES *********************
    # *
    # * @brief Return codes for the protocol methods
    class RC(Enum) :
        OK = 0
        ERROR = 1
        USER_ERROR = 2

    # ****************** ATTRIBUTES ******************
    _server = None
    _port = -1
    # Nuevos atributos:
    _listen_port = None
    _listen_socket = None
    _listen_thread = None
    _current_user = None
    _running = True

    # ******************** METHODS *******************


    @staticmethod
    def  register(user) :
        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"REGISTER\0" + user.encode() + b"\0" + timestamp.encode() + b"\0")
                response = s.recv(1)
                
                if response == b'\x00':
                    print("c> REGISTER OK")
                    return client.RC.OK
                elif response == b'\x01':
                    print("c> USERNAME IN USE")
                    return client.RC.USER_ERROR
                else:
                    print("c> REGISTER FAIL")
                    return client.RC.ERROR
        except Exception as e:
            print("c> REGISTER FAIL")
            return client.RC.ERROR

   
    @staticmethod
    def  unregister(user) :
        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"UNREGISTER\0" + user.encode() + b"\0" + timestamp.encode() + b"\0")
                response = s.recv(1)
                
                if response == b'\x00':
                    print("c> UNREGISTER OK")
                    return client.RC.OK
                elif response == b'\x01':
                    print("c> USER DOES NOT EXIST")
                    return client.RC.USER_ERROR
                else:
                    print("c> UNREGISTER FAIL")
                    return client.RC.ERROR
        except Exception as e:
            print("c> UNREGISTER FAIL")
            return client.RC.ERROR

    @staticmethod
    def handle_client_request(conn):
        # Leemos en bucle hasta encontrar el delimitador \0 dos veces (lo que indica que tenemos el comando y el nombre del archivo completo)
        try:
            # timestamp = get_datetime_from_web()

            data = bytearray()
            while b'\0' not in data or data.count(b'\0') < 2:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk

            if data.startswith(b"GET_FILE"):
                parts = data.split(b'\0')
                if len(parts) >= 2:
                    filename = parts[1].decode()
                    if os.path.exists(filename):
                        conn.sendall(b'\x00')  # OK
                        file_size = os.path.getsize(filename)
                        timestamp = get_datetime_from_web()

                        # Enviar encabezado separado por '\0' (file_size\0timestamp\0)
                        header = f"{file_size}\0{timestamp}\0".encode()
                        conn.sendall(header)

                        # Enviar archivo
                        with open(filename, 'rb') as f:
                            while True:
                                chunk = f.read(4096)
                                if not chunk:
                                    break
                                conn.sendall(chunk)
                    else:
                        conn.sendall(b'\x01')  # Archivo no existe

        except Exception as e:
            print(f"c> Error al manejar GET_FILE: {e}")
        finally:
            conn.close()


    
    @staticmethod
    def connect(user):
        try:
            timestamp = get_datetime_from_web()

            # 1. Crear socket de escucha (servidor) en un puerto libre
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.bind(('', 0))  # El sistema elige un puerto libre
            listen_socket.listen(5)
            client._listen_socket = listen_socket
            client._listen_port = listen_socket.getsockname()[1]
            client._current_user = user

            # 2. Crear el hilo que escuchará peticiones
            def listen():
                while client._running:
                    try:
                        conn, addr = listen_socket.accept()
                        client.handle_client_request(conn)
                        # conn.close()
                    except Exception as e:
                        print(f"c> Error en el hilo de escucha: {e}")
                        break

            client._listen_thread = threading.Thread(target=listen, daemon=True)
            client._listen_thread.start()

            # 3. Conectar con el servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"CONNECT\0" + user.encode() + b"\0" + str(client._listen_port).encode() + b'\0' + timestamp.encode() + b"\0") # + b"\0")
                response = s.recv(1) # Para recibir 1 byte (que es el resultado de la operación (0, 1, 2, 3))

            # 4. Interpretar respuesta
            if response == b'\x00':
                print("c> CONNECT OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> CONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response == b'\x02':
                print("c> USER ALREADY CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("c> CONNECT FAIL")
                return client.RC.ERROR

        except Exception as e:
            print("c> CONNECT FAIL")
            return client.RC.ERROR

    
    @staticmethod
    def disconnect(user):
        try:
            timestamp = get_datetime_from_web()

            # 1. Enviar mensaje al servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"DISCONNECT\0" + user.encode() + b"\0" + timestamp.encode() + b"\0")
                response = s.recv(1)

            # 2. Interpretar respuesta del servidor
            if response == b'\x00':
                print("c> DISCONNECT OK")
            elif response == b'\x01':
                print("c> DISCONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response == b'\x02':
                print("c> DISCONNECT FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("c> DISCONNECT FAIL")
                return client.RC.ERROR

            # 3. Parar el hilo y cerrar el socket de escucha
            client._running = False
            if client._listen_socket:
                try:
                    client._listen_socket.close()
                except:
                    pass
                client._listen_socket = None

            client._listen_thread = None
            client._listen_port = None
            client._current_user = None

            return client.RC.OK

        except Exception as e:
            print("c> DISCONNECT FAIL")
            return client.RC.ERROR


    @staticmethod
    def publish(fileName, description):
        if client._current_user is None:
            print("c> PUBLISH FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"PUBLISH\0" +
                        client._current_user.encode() + b"\0" +
                        fileName.encode() + b"\0" +
                        description.encode() + b"\0" + timestamp.encode() + b"\0")

                response = s.recv(1)

            if response == b'\x00':
                print("c> PUBLISH OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> PUBLISH FAIL, USER DOES NOT EXIST")
            elif response == b'\x02':
                print("c> PUBLISH FAIL, USER NOT CONNECTED")
            elif response == b'\x03':
                print("c> PUBLISH FAIL, CONTENT ALREADY PUBLISHED")
            else:
                print("c> PUBLISH FAIL")
            return client.RC.USER_ERROR

        except Exception as e:
            print("c> PUBLISH FAIL")
            return client.RC.ERROR


    @staticmethod
    def delete(fileName):
        if client._current_user is None:
            print("c> DELETE FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"DELETE\0" +
                        client._current_user.encode() + b"\0" +
                        fileName.encode() + b"\0" + timestamp.encode() + b"\0")

                response = s.recv(1)

            if response == b'\x00':
                print("c> DELETE OK")
                return client.RC.OK
            elif response == b'\x01':
                print("c> DELETE FAIL, USER DOES NOT EXIST")
            elif response == b'\x02':
                print("c> DELETE FAIL, USER NOT CONNECTED")
            elif response == b'\x03':
                print("c> DELETE FAIL, FILE NOT FOUND")
            else:
                print("c> DELETE FAIL")
            return client.RC.USER_ERROR

        except Exception as e:
            print("c> DELETE FAIL")
            return client.RC.ERROR


    @staticmethod
    def listusers():
        if client._current_user is None:
            print("c> LIST_USERS FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"LIST_USERS\0" + client._current_user.encode() + b"\0" + timestamp.encode() + b"\0")

                result = s.recv(1)
                if result == b'\x01':
                    print("c> LIST_USERS FAIL, USER DOES NOT EXIST")
                    return client.RC.USER_ERROR
                elif result == b'\x02':
                    print("c> LIST_USERS FAIL, USER NOT CONNECTED")
                    return client.RC.USER_ERROR
                elif result != b'\x00':
                    print("c> LIST_USERS FAIL")
                    return client.RC.ERROR

                # Leer el resto de la información (número y lista)
                data = bytearray()
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                entries = data.split(b'\0')
                if len(entries) < 1:
                    print("c> LIST_USERS FAIL")
                    return client.RC.ERROR

                num_users = int(entries[0].decode())
                print("c> LIST_USERS OK")
                idx = 1
                for _ in range(num_users):
                    if idx + 2 >= len(entries):
                        break
                    name = entries[idx].decode()
                    ip = entries[idx + 1].decode()
                    port = entries[idx + 2].decode()
                    print(f"     {name} {ip} {port}")
                    idx += 3

                return client.RC.OK

        except Exception:
            print("c> LIST_USERS FAIL")
            return client.RC.ERROR


    @staticmethod
    def listcontent(user):
        if client._current_user is None:
            print("c> LIST_CONTENT FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR

        try:
            timestamp = get_datetime_from_web()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"LIST_CONTENT\0" +
                        client._current_user.encode() + b"\0" +
                        user.encode() + b"\0" + timestamp.encode() + b"\0")

                result = s.recv(1)
                if result == b'\x01':
                    print("c> LIST_CONTENT FAIL, USER DOES NOT EXIST")
                    return client.RC.USER_ERROR
                elif result == b'\x02':
                    print("c> LIST_CONTENT FAIL, USER NOT CONNECTED")
                    return client.RC.USER_ERROR
                elif result == b'\x03':
                    print("c> LIST_CONTENT FAIL, REMOTE USER DOES NOT EXIST")
                    return client.RC.USER_ERROR
                elif result != b'\x00':
                    print("c> LIST_CONTENT FAIL")
                    return client.RC.ERROR

                # Leer datos
                data = bytearray()
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk

                entries = data.split(b'\0')
                if len(entries) < 1:
                    print("c> LIST_CONTENT FAIL")
                    return client.RC.ERROR

                count = int(entries[0].decode())
                print("c> LIST_CONTENT OK")
                for i in range(1, 1 + count):
                    print(entries[i].decode())

                return client.RC.OK

        except Exception:
            print("c> LIST_CONTENT FAIL")
            return client.RC.ERROR


    @staticmethod
    def getfile(user, remote_fileName, local_fileName):
        if client._current_user is None:
            print("c> GET_FILE FAIL, NOT CONNECTED")
            return client.RC.USER_ERROR
                
        try:
            timestamp = get_datetime_from_web()

            # Paso 1: Obtener IP y puerto del usuario remoto desde el servidor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((client._server, client._port))
                s.sendall(b"GET_FILE\0" + 
                        client._current_user.encode() + b"\0" +
                        user.encode() + b"\0" +
                        remote_fileName.encode() + b"\0" + timestamp.encode() + b"\0")
                
                result = s.recv(1)
                if result == b'\x01':
                    print("c> GET_FILE FAIL, FILE NOT EXIST")
                    return client.RC.USER_ERROR
                elif result != b'\x00':
                    print("c> GET_FILE FAIL")
                    return client.RC.ERROR

                # Leer IP y puerto
                ip = b''
                while True:
                    chunk = s.recv(1)
                    if chunk == b'\0':
                        break
                    ip += chunk

                port_str = b''
                while True:
                    chunk = s.recv(1)
                    if chunk == b'\0':
                        break
                    port_str += chunk

                ip_addr = ip.decode()
                port = int(port_str.decode())

            # Paso 2: Conectar con el cliente destino
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                #print(f"Ip_addr: {ip_addr}, Port: {port}")
                s.connect((ip_addr, port))
                s.sendall(b"GET_FILE\0" + remote_fileName.encode() + b"\0" + timestamp.encode() + b"\0")

                result = s.recv(1)
                if result == b'\x01':
                    print("c> GET_FILE FAIL, FILE NOT EXIST")
                    return client.RC.USER_ERROR
                elif result != b'\x00':
                    print("c> GET_FILE FAIL")
                    return client.RC.ERROR

                # Leer tamaño del archivo
                size_str = b''
                while True:
                    chunk = s.recv(1)
                    if chunk == b'\0':
                        break
                    size_str += chunk

                # Leer timestamp
                timestamp_str = b''
                while True:
                    chunk = s.recv(1)
                    if chunk == b'\0':
                        break
                    timestamp_str += chunk

                file_size = int(size_str.decode())
                timestamp = timestamp_str.decode()

                # Descargar archivo por bloques
                received = 0
                with open(local_fileName, 'wb') as f:
                    while received < file_size:
                        chunk = s.recv(min(4096, file_size - received))
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)


                if received == file_size:
                    print("c> GET_FILE OK")
                    return client.RC.OK
                else:
                    os.remove(local_fileName)
                    print("c> GET_FILE FAIL (incomplete file)")
                    return client.RC.ERROR

        except Exception as e:
            print(f"c> GET_FILE FAIL ({e})")
            return client.RC.ERROR


    # *
    # **
    # * @brief Command interpreter for the client. It calls the protocol functions.
    @staticmethod
    def shell():

        while (True) :
            try :
                command = input("c> ")
                line = command.split(" ")
                if (len(line) > 0):

                    line[0] = line[0].upper()

                    if (line[0]=="REGISTER") :
                        if (len(line) == 2) :
                            client.register(line[1])
                        else :
                            print("Syntax error. Usage: REGISTER <userName>")

                    elif(line[0]=="UNREGISTER") :
                        if (len(line) == 2) :
                            client.unregister(line[1])
                        else :
                            print("Syntax error. Usage: UNREGISTER <userName>")

                    elif(line[0]=="CONNECT") :
                        if (len(line) == 2) :
                            client.connect(line[1])
                        else :
                            print("Syntax error. Usage: CONNECT <userName>")
                    
                    elif(line[0]=="PUBLISH") :
                        if (len(line) >= 3) :
                            #  Remove first two words
                            description = ' '.join(line[2:])
                            client.publish(line[1], description)
                        else :
                            print("Syntax error. Usage: PUBLISH <fileName> <description>")

                    elif(line[0]=="DELETE") :
                        if (len(line) == 2) :
                            client.delete(line[1])
                        else :
                            print("Syntax error. Usage: DELETE <fileName>")

                    elif(line[0]=="LIST_USERS") :
                        if (len(line) == 1) :
                            client.listusers()
                        else :
                            print("Syntax error. Use: LIST_USERS")

                    elif(line[0]=="LIST_CONTENT") :
                        if (len(line) == 2) :
                            client.listcontent(line[1])
                        else :
                            print("Syntax error. Usage: LIST_CONTENT <userName>")

                    elif(line[0]=="DISCONNECT") :
                        if (len(line) == 2) :
                            client.disconnect(line[1])
                        else :
                            print("Syntax error. Usage: DISCONNECT <userName>")

                    elif(line[0]=="GET_FILE") :
                        if (len(line) == 4) :
                            client.getfile(line[1], line[2], line[3])
                        else :
                            print("Syntax error. Usage: GET_FILE <userName> <remote_fileName> <local_fileName>")

                    elif(line[0]=="QUIT") :
                        if (len(line) == 1) :
                            break
                        else :
                            print("Syntax error. Use: QUIT")
                    else :
                        print("Error: command " + line[0] + " not valid.")
            except Exception as e:
                print("Exception: " + str(e))

    # *
    # * @brief Prints program usage
    @staticmethod
    def usage() :
        print("Usage: python3 client.py -s <server> -p <port>")


    # *
    # * @brief Parses program execution arguments
    @staticmethod
    def  parseArguments(argv) :
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', type=str, required=True, help='Server IP')
        parser.add_argument('-p', type=int, required=True, help='Server Port')
        args = parser.parse_args()

        if (args.s is None):
            parser.error("Usage: python3 client.py -s <server> -p <port>")
            return False

        if ((args.p < 1024) or (args.p > 65535)):
            parser.error("Error: Port must be in the range 1024 <= port <= 65535");
            return False;
        
        client._server = args.s
        client._port = args.p

        return True


    # ******************** MAIN *********************
    @staticmethod
    def main(argv) :
        if (not client.parseArguments(argv)) :
            client.usage()
            return

        #  Write code here
        client.shell()
        print("+++ FINISHED +++")
    

if __name__=="__main__":
    client.main([])