#ifndef LOGGING_H
#define LOGGING_H

#include <iostream>
#include <string>

// Define log levels using an enum
enum class LogLevel {
    NONE = 0,
    ERROR = 1,
    WARN = 2,
    INFO = 3,
    DEBUG = 4
};

// TODO: Set the current log level
constexpr LogLevel CURRENT_LOG_LEVEL = LogLevel::ERROR;

// Helper function to convert log level to string
inline std::string logLevelToString(LogLevel level) {
    switch (level) {
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::WARN:  return "WARN";
        case LogLevel::INFO:  return "INFO";
        case LogLevel::DEBUG: return "DEBUG";
        default:              return "NONE";
    }
}

// Macro for logging with levels
#define LOG(level, msg) \
    if (level <= CURRENT_LOG_LEVEL) { \
        std::cout << logLevelToString(level) << " " << __FILE__ << ":" << __LINE__ << " - " << msg << std::endl; \
    }

#define LOG_ERROR(msg) LOG(LogLevel::ERROR, msg)
#define LOG_WARN(msg) LOG(LogLevel::WARN, msg)
#define LOG_INFO(msg) LOG(LogLevel::INFO, msg)
#define LOG_DEBUG(msg) LOG(LogLevel::DEBUG, msg)

#endif // LOGGING_H