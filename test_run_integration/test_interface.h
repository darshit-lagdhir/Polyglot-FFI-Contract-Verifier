
    #ifndef TEST_INTERFACE_H
    #define TEST_INTERFACE_H
    
    #include <stdint.h>
    
    // Simple struct with padding
    struct Config {
        int32_t mode;
        void* data;
    };
    
    // Function with non-null constraint
    int process(struct Config* cfg);
    
    // Function with buffer-length relationship
    int write_buffer(uint8_t* buffer, uint32_t size);
    
    // Function with ownership transfer
    struct Config* create_config(int32_t mode);
    void destroy_config(struct Config* cfg);
    
    #endif // TEST_INTERFACE_H
    