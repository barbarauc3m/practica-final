
struct log_action_args {
    string user<256>;       
    string operation<512>;   
    string timestamp<32>;   
};

program LOGPROG {
    version LOGVERS {
        void LOG_ACTION(log_action_args) = 1;
    } = 1;
} = 100495755;
