#include "gdg_debug.h"

#include <stdio.h>
#include <stdarg.h>

void
gdg_print_message (
        GdgMessageLevel   type,
        const char        *function,
        const char        *formatstring,
        ...)
{
    FILE          *stream = stderr;
    va_list        args;

    va_start (args, formatstring);
    switch (type)
    {
        case GdgDebugMsg:
            fprintf (stream, "%s%s%s: ",
                    TERM_GREEN_BOLD, function, TERM_NORMAL);
            vfprintf (stream, formatstring, args);
            break;

        case GdgWarningMsg:
            fprintf (stream, "%s%s%s: ",
                    TERM_RED, function, TERM_NORMAL);
            vfprintf (stream, formatstring, args);
            break;
    }
    va_end(args);

    fprintf(stream, TERM_ERASE_EOL "\n");
    fflush(stream);
}
