#ifdef DEBUG_ALL
#  ifndef DEBUG
#    define DEBUG
#  endif
#  ifndef WARNING
#    define WARNING
#  endif
#endif

#ifdef DEBUG
#  define WARNING
#endif

#ifdef PUBLIC_RELEASE
#  ifdef DEBUG
#    undef DEBUG
#  endif
#  ifdef WARNING
#    undef WARNING
#  endif
#endif
#undef GDG_DEBUG

#ifdef DEBUG

/**
 * The GDG_DEBUG macro is used to print normal debug messages to be seen only
 * during the development.
 */
#  define GDG_DEBUG(...) gdg_print_message (\
        GdgDebugMsg, \
        __func__, \
        __VA_ARGS__)
#else
/**
 * The GDG_DEBUG macro is used to print normal debug messages to be seen only
 * during the development.
 */
#  define GDG_DEBUG(...) { /* Nothing... */ }
#endif

#undef GDG_WARNING
#ifdef WARNING
/**
 * The GDG_WARNING is used to print warning messages to be seen only during the
 * development.
 */
#  define GDG_WARNING(...) gdg_print_message (\
        GdgWarningMsg, \
        __func__, \
        __VA_ARGS__)
#else
/**
 * The GDG_WARNING is used to print warning messages to be seen only during the
 * development.
 */
#  define GDG_WARNING(...) { /* Nothing... */ }
#endif

/**
 * Message level for the debug/warning print functions.
 */
typedef enum GdgMessageLevel
{
    GdgDebugMsg,
    GdgWarningMsg
} GdgMessageLevel;

#ifndef GDG_DEBUG_H
#define GDG_DEBUG_H

/** Terminal color: green bold. */
#define TERM_GREEN_BOLD "\033[1m\033[38;5;10m"
/** Terminal color: red. */
#define TERM_RED        "\033[38;5;9m"
/** Terminal reset sequence. */
#define TERM_NORMAL     "\033[0;39m"
/** Erase to end of line. */
#define TERM_ERASE_EOL  "\033[K"

void
gdg_print_message (
        GdgMessageLevel  type,
        const char       *function,
        const char       *formatstring,
        ...);

/**
 * A macro to print booleans.
 */
#define STR_BOOL(_boolval) ((_boolval ? "true" : "false"))

#endif
