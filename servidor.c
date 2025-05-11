#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <tirpc/rpc/rpc.h>
#include "log_rpc.h"



// ----------------------------
// Constantes y estructuras
// ----------------------------

#define MAX_USERS 100
#define MAX_NAME_LEN 256
#define BUFFER_SIZE 1024

typedef struct FileEntry {
    char filename[256];       // Nombre del archivo
    char description[256];    // Descripción del archivo
    struct FileEntry* next;   // Puntero al siguiente archivo (lista enlazada)
} FileEntry;


typedef struct User {
    char name[MAX_NAME_LEN];   // Nombre del usuario
    int is_connected;          // Flag de conexión (1=conectado, 0=desconectado)
    char ip[INET_ADDRSTRLEN];  // Dirección IP del usuario
    int port;                  // Puerto de conexión del usuario
    FileEntry* files;          // Lista enlazada para los archivos publicados por el usuario
    struct User* next;         // Puntero al siguiente usuario (lista enlazada)
} User;

User* user_list = NULL;   // Lista global de usuarios registrados
CLIENT *log_clnt = NULL; // Cliente RPC para logging

pthread_mutex_t user_mutex = PTHREAD_MUTEX_INITIALIZER;

// ----------------------------
// FUNCIONES PARA EL MANEJO DE USUARIOS (register, unregister, connect, disconnect, list_users)
// ----------------------------

int register_user(const char* name) {
    pthread_mutex_lock(&user_mutex);

    // Verifica si el usuario ya existe
    User* current = user_list;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            pthread_mutex_unlock(&user_mutex);
            return 1; // Usuario ya existe
        }
        current = current->next;
    }

    // Para crear nuevo nodo (usuario)
    User* new_user = malloc(sizeof(User));
    if (!new_user) {
        pthread_mutex_unlock(&user_mutex);
        return 2; // Error
    }

    // Inicializamos todos los campos del usuario
    strncpy(new_user->name, name, MAX_NAME_LEN);
    new_user->is_connected = 0;
    new_user->ip[0] = '\0';
    new_user->port = 0;
    new_user->next = user_list;
    user_list = new_user;

    pthread_mutex_unlock(&user_mutex);
    return 0; // OK
}


int unregister_user(const char* name) {
    pthread_mutex_lock(&user_mutex);

    User* current = user_list;
    User* previous = NULL;

    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            if (previous == NULL) {
                user_list = current->next;
            } else {
                previous->next = current->next;
            }
            free(current);
            pthread_mutex_unlock(&user_mutex);
            return 0; // OK
        }
        previous = current;
        current = current->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return 1; // Usuario no encontrado
}

int connect_user(const char* name, const char* ip, int port) {
    pthread_mutex_lock(&user_mutex);

    User* current = user_list;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {  // Si el usuario está registrado...
            if (current->is_connected) {
                pthread_mutex_unlock(&user_mutex);
                return 2; // Ya conectado
            }

            current->is_connected = 1;
            strncpy(current->ip, ip, INET_ADDRSTRLEN);
            current->port = port;

            pthread_mutex_unlock(&user_mutex);
            return 0; // OK
        }
        current = current->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return 1; // Usuario no existe
}

int disconnect_user(const char* name) {
    pthread_mutex_lock(&user_mutex);

    User* current = user_list;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            if (!current->is_connected) {
                pthread_mutex_unlock(&user_mutex);
                return 2; // Usuario no está conectado
            }

            current->is_connected = 0;
            current->ip[0] = '\0';
            current->port = 0;

            pthread_mutex_unlock(&user_mutex);
            return 0; // OK
        }
        current = current->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return 1; // Usuario no existe
}

int list_connected_users(char* buffer, int max_len) {
    pthread_mutex_lock(&user_mutex);

    int pos = 0;
    User* current = user_list;
    while (current) {
        if (current->is_connected) {
            // Formatear la línea: "NOMBRE IP PORT\0"
            char line[INET_ADDRSTRLEN + MAX_NAME_LEN + 10]; // Suficiente espacio para nombre, IP y puerto
            int line_len = snprintf(line, sizeof(line), "%s %s %d", current->name, current->ip, current->port);
            
            // Verificar si hay espacio en el buffer
            if (pos + line_len + 1 >= max_len - 1) { // +1 por el \0 adicional
                pthread_mutex_unlock(&user_mutex);
                return -1; // No hay espacio
            }

            // Copiar la línea al buffer
            memcpy(buffer + pos, line, line_len + 1); // +1 para incluir el \0
            pos += line_len + 1;
        }
        current = current->next;
    }

    buffer[pos++] = '\0'; // Doble \0 final
    pthread_mutex_unlock(&user_mutex);
    return pos; // Número de bytes escritos
}


// ----------------------------
// FUNCIONES PARA LA GESTIÓN DE ARCHIVOS (publish, delete, list_content, get_file)
// ----------------------------

int publish_file(const char* username, const char* filename, const char* description) {
    pthread_mutex_lock(&user_mutex);

    User* user = user_list;
    while (user) {
        if (strcmp(user->name, username) == 0) {
            if (!user->is_connected) {
                pthread_mutex_unlock(&user_mutex);
                return 2; // Usuario no conectado
            }

            // Verificar si ya publicó ese archivo
            FileEntry* f = user->files;
            while (f) {
                if (strcmp(f->filename, filename) == 0) {
                    pthread_mutex_unlock(&user_mutex);
                    return 3; // Archivo ya publicado
                }
                f = f->next;
            }

            // Crear nuevo archivo
            FileEntry* new_file = malloc(sizeof(FileEntry));
            if (!new_file) {
                pthread_mutex_unlock(&user_mutex);
                return 4; // Error de memoria
            }

            strncpy(new_file->filename, filename, 256);
            strncpy(new_file->description, description, 256);
            new_file->next = user->files;
            user->files = new_file;

            pthread_mutex_unlock(&user_mutex);
            return 0; // OK
        }
        user = user->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return 1; // Usuario no existe
}

int delete_file(const char* username, const char* filename) {
    pthread_mutex_lock(&user_mutex);

    User* user = user_list;
    while (user) {
        if (strcmp(user->name, username) == 0) {
            if (!user->is_connected) {
                pthread_mutex_unlock(&user_mutex);
                return 2; // No conectado
            }

            FileEntry* prev = NULL;
            FileEntry* current = user->files;

            while (current) {
                if (strcmp(current->filename, filename) == 0) {
                    if (prev == NULL) {
                        user->files = current->next;
                    } else {
                        prev->next = current->next;
                    }
                    free(current);
                    pthread_mutex_unlock(&user_mutex);
                    return 0; // OK
                }
                prev = current;
                current = current->next;
            }

            pthread_mutex_unlock(&user_mutex);
            return 3; // Archivo no encontrado
        }
        user = user->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return 1; // Usuario no existe
}

int list_user_files(const char* requester, const char* target, char* buffer, int max_len) {
    pthread_mutex_lock(&user_mutex);

    User* req = NULL;
    User* tgt = NULL;
    User* current = user_list;

    while (current) {
        if (strcmp(current->name, requester) == 0) req = current;
        if (strcmp(current->name, target) == 0) tgt = current;
        current = current->next;
    }

    if (!req) {
        pthread_mutex_unlock(&user_mutex);
        return 1; // Usuario que realiza la operación no existe
    }

    if (!req->is_connected) {
        pthread_mutex_unlock(&user_mutex);
        return 2; // Usuario no conectado
    }

    if (!tgt) {
        pthread_mutex_unlock(&user_mutex);
        return 3; // Usuario remoto no existe
    }

    // Contar archivos publicados
    int count = 0;
    FileEntry* f = tgt->files;
    while (f) {
        count++;
        f = f->next;
    }

    int pos = snprintf(buffer, max_len, "%d", count);
    buffer[pos++] = '\0';  // Añadimos manualmente el \0 que separa cadenas

    if (pos < 0 || pos >= max_len) {
        pthread_mutex_unlock(&user_mutex);
        return 4;
    }

    f = tgt->files;
    while (f) {
        int len = strlen(f->filename) + 1;
        if (pos + len >= max_len) {
            pthread_mutex_unlock(&user_mutex);
            return 4; // Error por falta de espacio
        }
        memcpy(buffer + pos, f->filename, len);
        pos += len;
        f = f->next;
    }

    pthread_mutex_unlock(&user_mutex);
    return pos; // devuelve bytes escritos si éxito
}

// Para get_file
User* get_user_by_name(const char* name) {
    pthread_mutex_lock(&user_mutex);
    User* current = user_list;
    while (current != NULL) {
        if (strcmp(current->name, name) == 0) {
            pthread_mutex_unlock(&user_mutex);
            return current;
        }
        current = current->next;
    }
    pthread_mutex_unlock(&user_mutex);
    return NULL;
}

// ----------------------------
// Manejo de clientes
// ----------------------------

void* client_handler(void* arg) {
    // 1. Obtener socket del cliente y liberar memoria del argumento
    int client_sock = *(int*)arg;
    free(arg);

    // 2. Recibir datos del cliente
    char buffer[BUFFER_SIZE];
    int len = recv(client_sock, buffer, BUFFER_SIZE, 0);
    if (len <= 0) {
        close(client_sock);
        return NULL;
    }
    buffer[len] = '\0';  // Le añadimos \0 al final de la cadena

    // 3. Parsear operación y usuario
    char* op = buffer;
    char* user = strchr(op, '\0') + 1;

    // 4. Manejo de timestamp
    char *timestamp;

    if (strcmp(op, "CONNECT") == 0) {
        char *port_str = strchr(user, '\0') + 1;
        timestamp = strchr(port_str, '\0') + 1;
    } 
    else if (strcmp(op, "PUBLISH") == 0) {
        char *filename = strchr(user, '\0') + 1;
        char *description = strchr(filename, '\0') + 1;
        timestamp = strchr(description, '\0') + 1;
    }
    else if (strcmp(op, "DELETE") == 0) {
        char *filename = strchr(user, '\0') + 1;
        timestamp = strchr(filename, '\0') + 1;
    }
    else if (strcmp(op, "LIST_CONTENT") == 0) {
        char *target_user = strchr(user, '\0') + 1;
        timestamp = strchr(target_user, '\0') + 1;
    }
    else if (strcmp(op, "GET_FILE") == 0) {
        char *target_user = strchr(user, '\0') + 1;
        char *filename = strchr(target_user, '\0') + 1;
        timestamp = strchr(filename, '\0') + 1;
    }
    else {
        // Operaciones simples: REGISTER, UNREGISTER, DISCONNECT, LIST_USERS
        timestamp = strchr(user, '\0') + 1;
    }

    // 5. Verificación del formato básico
    if (user >= buffer + len) {
        printf("s> Invalid message format\n");
        char resultado = 2;
        send(client_sock, &resultado, 1, 0);
        close(client_sock);
        return NULL;
    }
    if (timestamp >= buffer + len) {
        printf("s> Invalid message format\n");
        char resultado = 2;
        send(client_sock, &resultado, 1, 0);
        close(client_sock);
        return NULL;
    }

    char resultado = 2; // Valor por defecto: error

     // 6. Preparar args para RPC
     char operation_str[512];
     memset(operation_str, 0, sizeof(operation_str));  // Limpiamos el buffer

    //// Asignamos el nombre de la operación ANTES de la llamada RPC
    if (strcmp(op, "REGISTER") == 0) {
        strncpy(operation_str, "REGISTER", sizeof(operation_str));
    } else if (strcmp(op, "UNREGISTER") == 0) {
        strncpy(operation_str, "UNREGISTER", sizeof(operation_str));
    } else if (strcmp(op, "CONNECT") == 0) {
        strncpy(operation_str, "CONNECT", sizeof(operation_str));
    } else if (strcmp(op, "DISCONNECT") == 0) {
        strncpy(operation_str, "DISCONNECT", sizeof(operation_str));
    } else if (strcmp(op, "PUBLISH") == 0) {
        char *filename = strchr(user, '\0') + 1;
        char *description = strchr(filename, '\0') + 1;
        timestamp = strchr(description, '\0') + 1;
        // Formato: "PUBLISH filename"
        snprintf(operation_str, sizeof(operation_str), "PUBLISH %s", filename);
    } else if (strcmp(op, "DELETE") == 0) {
        char *filename = strchr(user, '\0') + 1;
        timestamp = strchr(filename, '\0') + 1;        
        // Formato: "DELETE filename"
        snprintf(operation_str, sizeof(operation_str), "DELETE %s", filename);
    } else if (strcmp(op, "GET_FILE") == 0) {
        strncpy(operation_str, "GET_FILE", sizeof(operation_str));
    } else if (strcmp(op, "LIST_USERS") == 0) {
        strncpy(operation_str, "LIST_USERS", sizeof(operation_str));
    } else if (strcmp(op, "LIST_CONTENT") == 0) {
        strncpy(operation_str, "LIST_CONTENT", sizeof(operation_str));
    }

    //// Construimos los args 
    struct log_action_args args;
    args.user      = (char*)user;
    args.operation = operation_str;
    args.timestamp = (char*)timestamp;

    //// Definimos el timeout en una variable (sin coma al final)
    struct timeval timeout = { 5, 0 };

    //// Invocamos la macro con 7 args EXACTOS
    enum clnt_stat st = clnt_call(
    log_clnt,                       /* CLIENT * */
        LOG_ACTION,                      /* procedimiento */
        (xdrproc_t)xdr_log_action_args, /* xdr args */
        (caddr_t)&args,                 /* puntero args */
        (xdrproc_t)xdr_bool,            /* xdr result */
        (caddr_t)&resultado,            /* puntero result */
        timeout                         /* struct timeval */
    );

    printf("s> op='%s' | user='%s'\n", op, user);


    // 7. Procesar cada tipo de operación
    if (strcmp(op, "REGISTER") == 0) {
        resultado = (char)register_user(user);
        printf("s> OPERATION REGISTER FROM %s at %s\n", user, timestamp);

        strcpy(operation_str, "REGISTER");

    } else if (strcmp(op, "UNREGISTER") == 0) {
        resultado = (char)unregister_user(user);
        printf("s> OPERATION UNREGISTER FROM %s at %s\n", user, timestamp);

        strcpy(operation_str, "UNREGISTER");

    } else if (strcmp(op, "DISCONNECT") == 0) {
        resultado = (char)disconnect_user(user);
        printf("s> OPERATION DISCONNECT FROM %s at %s\n", user, timestamp);

        strcpy(operation_str, "DISCONNECT");

    } else if (strcmp(op, "CONNECT") == 0) {
        char* port_str = strchr(user, '\0') + 1;
        char* timestamp = strchr(port_str, '\0') + 1; 

        if (port_str >= buffer + len) {
            resultado = 3;
        } else {
            int client_port = atoi(port_str);

            struct sockaddr_in addr;
            socklen_t addr_len = sizeof(addr);

            getpeername(client_sock, (struct sockaddr*)&addr, &addr_len);

            char client_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &addr.sin_addr, client_ip, INET_ADDRSTRLEN);

            resultado = (char)connect_user(user, client_ip, client_port);
            printf("s> OPERATION CONNECT FROM %s (%s:%d) at %s\n", user, client_ip, client_port, timestamp);

            strcpy(operation_str, "CONNECT");
        }

    } else if (strcmp(op, "LIST_USERS") == 0) {
        printf("s> OPERATION LIST_USERS FROM %s at %s\n", user, timestamp);

        pthread_mutex_lock(&user_mutex);
        User* requester = user_list;
        int found = 0;
        while (requester) {
            if (strcmp(requester->name, user) == 0) {
                found = 1;
                break;
            }
            requester = requester->next;
        }

        if (!found) {
            pthread_mutex_unlock(&user_mutex);
            char code = 1; // USER DOES NOT EXIST
            send(client_sock, &code, 1, 0);
            close(client_sock);
            return NULL;
        }

        if (!requester->is_connected) {
            pthread_mutex_unlock(&user_mutex);
            char code = 2; // USER NOT CONNECTED
            send(client_sock, &code, 1, 0);
            close(client_sock);
            return NULL;
        }

        // Contar usuarios conectados
        int count = 0;
        User* u = user_list;
        while (u) {
            if (u->is_connected) count++;
            u = u->next;
        }

        // Enviar código de éxito
        char ok = 0;
        send(client_sock, &ok, 1, 0);

        // Enviar número de usuarios como cadena con '\0'
        char count_str[10];
        snprintf(count_str, sizeof(count_str), "%d", count);
        send(client_sock, count_str, strlen(count_str) + 1, 0);

        // Enviar nombre, IP y puerto de cada usuario
        u = user_list;
        while (u) {
            if (u->is_connected) {
                send(client_sock, u->name, strlen(u->name) + 1, 0);
                send(client_sock, u->ip, strlen(u->ip) + 1, 0);
                char port_str[10];
                snprintf(port_str, sizeof(port_str), "%d", u->port);
                send(client_sock, port_str, strlen(port_str) + 1, 0);
            }
            u = u->next;
        }

        strcpy(operation_str, "LIST USERS");

        pthread_mutex_unlock(&user_mutex);
        close(client_sock);
        return NULL;

        
    } else if (strcmp(op, "PUBLISH") == 0) {
        char* filename = strchr(user, '\0') + 1;
        char* description = strchr(filename, '\0') + 1;
        char* timestamp = strchr(description, '\0') + 1;

        if (description >= buffer + len) {
            resultado = 4;
        } else {
            resultado = (char)publish_file(user, filename, description);
            printf("s> OPERATION PUBLISH FROM %s: %s (%s) at %s\n", user, filename, description, timestamp);

            snprintf(operation_str, sizeof(operation_str),"PUBLISH %s", filename);
        }

    } else if (strcmp(op, "DELETE") == 0) {
        char* filename = strchr(user, '\0') + 1;
        char* timestamp = strchr(filename, '\0') + 1;

        if (filename >= buffer + len) {
            resultado = 4; // Mal formato
        } else {
            resultado = (char)delete_file(user, filename);
            printf("s> OPERATION DELETE FROM %s: %s at %s\n", user, filename, timestamp);
            snprintf(operation_str, sizeof(operation_str), "DELETE %s", filename);
        }

    } else if (strcmp(op, "LIST_CONTENT") == 0) {
        char* target_user = strchr(user, '\0') + 1;
        char* timestamp = strchr(target_user, '\0') + 1;
        if (target_user >= buffer + len) {
            char code = 4;
            send(client_sock, &code, 1, 0);
            close(client_sock);
            return NULL;
        }

        char list_buffer[BUFFER_SIZE];
        int result = list_user_files(user, target_user, list_buffer, BUFFER_SIZE);

        if (result >= 0) {
            char ok = 0;
            send(client_sock, &ok, 1, 0);
            send(client_sock, list_buffer, result, 0);
        } else {
            char err_code = (char)result;
            send(client_sock, &err_code, 1, 0);
        }
        printf("s> OPERATION LIST_CONTENT FROM %s TO %s at %s\n", user, target_user, timestamp);

        strcpy(operation_str, "LIST CONTENT");

        close(client_sock);
        return NULL;

    } else if (strcmp(op, "GET_FILE") == 0) {
        char* target_user = strchr(user, '\0') + 1; // Coge target_user como todo lo que hay detrás del primer \0
        char* filename = strchr(target_user, '\0') + 1;  // Coge filename como lo que hay detras del \0 en target_user (o sea el segundo \0)
        char* timestamp = strchr(filename, '\0') + 1;

        if (filename >= buffer + len) {
            resultado = 2; // Formato incorrecto
        } else {
            User* requester = get_user_by_name(user);
            User* target = get_user_by_name(target_user);
            
            if (!requester || !requester->is_connected) {
                resultado = 2; // Usuario no existe o no conectado
            } else if (!target || !target->is_connected) {
                resultado = 2; // Usuario destino no existe o no conectado
            } else {
                // Verificar si el archivo existe en el usuario destino
                FileEntry* f = target->files;
                int file_exists = 0;
                while (f) {
                    if (strcmp(f->filename, filename) == 0) {
                        file_exists = 1;
                        break;
                    }
                    f = f->next;
                }
                
                if (file_exists) {
                    // Enviar información de conexión del usuario destino
                    printf("s> OPERATION GET_FILE FROM %s TO %s: %s at %s\n", user, target_user, filename, timestamp);
                    resultado = 0; // Éxito
                    send(client_sock, &resultado, 1, 0);
                    
                    // Enviar IP y puerto del usuario destino
                    send(client_sock, target->ip, strlen(target->ip) + 1, 0);
                    char port_str[10];
                    snprintf(port_str, sizeof(port_str), "%d", target->port);
                    send(client_sock, port_str, strlen(port_str) + 1, 0);
                    
                    close(client_sock);
                    return NULL;
                } else {
                    resultado = 1; // Archivo no existe
                }
            }
            printf("s> OPERATION GET_FILE FROM %s TO %s: %s at %s\n", user, target_user, filename, timestamp);

            snprintf(operation_str, sizeof(operation_str), "GET_FILE %s", filename);
        }

        } else {
            printf("s> UNKNOWN OPERATION: %s at %s\n", op, timestamp);
            resultado = 3;
    }

    // 8. Enviar respuesta al cliente y cerrar
    send(client_sock, &resultado, 1, 0);
    close(client_sock);
    return NULL;
}


// ----------------------------
// Main
// ----------------------------

int main(int argc, char* argv[]) {
    if (argc != 3 || strcmp(argv[1], "-p") != 0) {
        fprintf(stderr, "Uso: %s -p <port>\n", argv[0]);
        exit(1);
    }

    int port = atoi(argv[2]);
    if (port < 1024 || port > 65535) {
        fprintf(stderr, "Puerto fuera de rango (1024-65535)\n");
        exit(1);
    }

    int server_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sock < 0) {
        perror("socket");
        exit(1);
    }

    struct sockaddr_in server_addr = {
        .sin_family = AF_INET,
        .sin_port = htons(port),
        .sin_addr.s_addr = INADDR_ANY
    };

    if (bind(server_sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        close(server_sock);
        exit(1);
    }

    if (listen(server_sock, 10) < 0) {
        perror("listen");
        close(server_sock);
        exit(1);
    }

    printf("s> init server 127.0.0.1:%d\ns>\n", port);

    /* 1) Leer la IP del servidor RPC desde la variable de entorno */
    char *rpc_host = getenv("LOG_RPC_IP");
    if (!rpc_host) {
        fprintf(stderr, "ERROR: tienes que exportar LOG_RPC_IP\n");
        exit(1);
    }

    /* 2) Crear cliente RPC sobre TCP */
    log_clnt = clnt_create(rpc_host, LOGPROG, LOGVERS, "tcp");
    if (log_clnt == NULL) {
        clnt_pcreateerror("Error conectando al servidor RPC");
        exit(1);
    }

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        int* client_sock = malloc(sizeof(int));
        *client_sock = accept(server_sock, (struct sockaddr*)&client_addr, &addr_len);
        if (*client_sock < 0) {
            perror("accept");
            free(client_sock);
            continue;
        }

        pthread_t tid;
        pthread_create(&tid, NULL, client_handler, client_sock);
        pthread_detach(tid); // No hay necesidad de hacer join
    }

    close(server_sock);
    return 0;
}
