/*
gcc -o servidor servidor.c -lpthread
./servidor -p 5000
*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <netinet/in.h>

// ----------------------------
// Constantes y estructuras
// ----------------------------

#define MAX_USERS 100
#define MAX_NAME_LEN 256
#define BUFFER_SIZE 1024

typedef struct User {
    char name[MAX_NAME_LEN];
    struct User* next;
} User;

User* user_list = NULL;
pthread_mutex_t user_mutex = PTHREAD_MUTEX_INITIALIZER;

// ----------------------------
// Función para agregar usuario
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

    // Crear nuevo nodo
    User* new_user = malloc(sizeof(User));
    if (!new_user) {
        pthread_mutex_unlock(&user_mutex);
        return 2; // Error
    }
    strncpy(new_user->name, name, MAX_NAME_LEN);
    new_user->next = user_list;
    user_list = new_user;

    pthread_mutex_unlock(&user_mutex);
    return 0; // OK
}

// ----------------------------
// Manejo de clientes
// ----------------------------

void* client_handler(void* arg) {
    int client_sock = *(int*)arg;
    free(arg);

    char buffer[BUFFER_SIZE];
    int len = recv(client_sock, buffer, BUFFER_SIZE, 0);
    if (len <= 0) {
        close(client_sock);
        return NULL;
    }

    buffer[len] = '\0';

    // Parsear operación
    char* op = buffer;
    char* user = strchr(op, '\0') + 1;

    if (strcmp(op, "REGISTER") == 0) {
        int result = register_user(user);
        char code = (char)result;
        send(client_sock, &code, 1, 0);
        printf("s> OPERATION REGISTER FROM %s\n", user);
    } else {
        char code = 2;
        send(client_sock, &code, 1, 0);
    }

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
