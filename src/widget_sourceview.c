/*
 * widget_sourceview.c:
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <pipas@linux.pte.hu>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

/* Includes */
#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <gtk/gtk.h>
#include "config.h"
#include "gtkdialog.h"
#include "widget_sourceview.h"
#include "attributes.h"
#include "automaton.h"
#include "widgets.h"
#include "signals.h"
#include "tag_attributes.h"
#include "gdg_debug.h"
#if HAVE_GTKSOURCEVIEW
#include <gtksourceview/gtksource.h>
#endif

#define GTKSOURCEVIEW_WARNING "The sourceview (GtkSourceView) widget requires \
a version of gtkdialog built with libgtksourceview."

/* Local function prototypes */
static void widget_sourceview_input_by_file(variable *var, char *filename);

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_sourceview_clear(variable *var)
{
	GDG_DEBUG("Entering.");

	gtk_text_buffer_set_text(gtk_text_view_get_buffer(
		GTK_TEXT_VIEW(var->Widget)), "", 0);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_sourceview_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;

	GDG_DEBUG("Entering.");

#if HAVE_GTKSOURCEVIEW
	{
		GtkSourceBuffer          *buffer;
		GtkSourceLanguageManager *lm;
		GtkSourceLanguage        *lang = NULL;
		gchar                    *value;

		lm = gtk_source_language_manager_get_default();

		/* Get language from tag attribute: <sourceview language="c"> */
		if (attr && (value = get_tag_attribute(attr, "language"))) {
			lang = gtk_source_language_manager_get_language(lm, value);
			if (!lang)
				g_warning("sourceview: unknown language '%s'", value);
		}

		buffer = gtk_source_buffer_new_with_language(
			lang ? lang : gtk_source_language_manager_get_language(lm, "text"));
		if (!buffer)
			buffer = gtk_source_buffer_new(NULL);

		gtk_source_buffer_set_highlight_syntax(buffer, lang != NULL);

		widget = gtk_source_view_new_with_buffer(buffer);
		gtk_source_view_set_show_line_numbers(GTK_SOURCE_VIEW(widget), TRUE);
		gtk_source_view_set_highlight_current_line(GTK_SOURCE_VIEW(widget), TRUE);
		gtk_source_view_set_tab_width(GTK_SOURCE_VIEW(widget), 4);
		gtk_source_view_set_auto_indent(GTK_SOURCE_VIEW(widget), TRUE);

		/* Apply custom tag attributes */
		if (attr) {
			if ((value = get_tag_attribute(attr, "show-line-numbers"))) {
				gtk_source_view_set_show_line_numbers(GTK_SOURCE_VIEW(widget),
					strcasecmp(value, "true") == 0 || atoi(value) == 1);
			}
			if ((value = get_tag_attribute(attr, "highlight-current-line"))) {
				gtk_source_view_set_highlight_current_line(GTK_SOURCE_VIEW(widget),
					strcasecmp(value, "true") == 0 || atoi(value) == 1);
			}
			if ((value = get_tag_attribute(attr, "tab-width"))) {
				gtk_source_view_set_tab_width(GTK_SOURCE_VIEW(widget), atoi(value));
			}
			if ((value = get_tag_attribute(attr, "font-name"))) {
				PangoFontDescription *fd = pango_font_description_from_string(value);
				gchar *css = g_strdup_printf(
					"textview { font-family: %s; font-size: %dpt; }",
					pango_font_description_get_family(fd),
					pango_font_description_get_size(fd) / PANGO_SCALE);
				GtkCssProvider *provider = gtk_css_provider_new();
				gtk_css_provider_load_from_data(provider, css, -1, NULL);
				gtk_style_context_add_provider(
					gtk_widget_get_style_context(widget),
					GTK_STYLE_PROVIDER(provider),
					GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
				g_object_unref(provider);
				g_free(css);
				pango_font_description_free(fd);
			}

			widget_set_tag_attributes(widget, attr);
		}
	}
#else
	widget = gtk_label_new(GTKSOURCEVIEW_WARNING);
#endif

	GDG_DEBUG("Exiting.");
	return widget;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_sourceview_envvar_construct(GtkWidget *widget)
{
	GtkTextBuffer    *buffer;
	GtkTextIter       start, end;
	gchar            *string;

	GDG_DEBUG("Entering.");

	buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(widget));
	gtk_text_buffer_get_start_iter(buffer, &start);
	gtk_text_buffer_get_end_iter(buffer, &end);
	string = gtk_text_buffer_get_text(buffer, &start, &end, TRUE);

	GDG_DEBUG("Exiting.");
	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_sourceview_fileselect(
	variable *var, const char *name, const char *value)
{
	GDG_DEBUG("Entering.");
	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);
	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_sourceview_refresh(variable *var)
{
	GList            *element;
	GtkTextBuffer    *text_buffer;
	gchar            *act;
	gint              initialised = FALSE;

	GDG_DEBUG("Entering.");

	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_sourceview_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* Initialise these only once at start-up */
	if (!initialised) {
		if (attributeset_is_avail(var->Attributes, ATTR_DEFAULT)) {
			text_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(var->Widget));
			gtk_text_buffer_set_text(text_buffer, attributeset_get_first(
				&element, var->Attributes, ATTR_DEFAULT), -1);
		}
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_sourceview_removeselected(variable *var)
{
	GDG_DEBUG("Entering.");
	gtk_text_buffer_delete_selection(gtk_text_view_get_buffer(
		GTK_TEXT_VIEW(var->Widget)), FALSE, TRUE);
	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_sourceview_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	GtkTextBuffer    *buffer;
	GtkTextIter       start, end;
	gchar            *act;
	gchar            *filename = NULL;
	gchar            *text;

	GDG_DEBUG("Entering.");

	act = attributeset_get_first(&element, var->Attributes, ATTR_OUTPUT);
	while (act) {
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			filename = act + 5;
			break;
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_OUTPUT);
	}

	if (filename) {
		if ((outfile = fopen(filename, "w"))) {
			buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(var->Widget));
			gtk_text_buffer_get_start_iter(buffer, &start);
			gtk_text_buffer_get_end_iter(buffer, &end);
			text = gtk_text_buffer_get_text(buffer, &start, &end, FALSE);
			fprintf(outfile, "%s", text);
			fclose(outfile);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for writing.\n",
				__func__, filename);
		}
	} else {
		fprintf(stderr, "%s(): No <output file> directive found.\n", __func__);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_sourceview_input_by_file(variable *var, char *filename)
{
	GtkTextBuffer    *buffer;
	gchar            *filebuffer;
	gint              infile;
	ssize_t           bytes_read;
	struct stat       st;

	GDG_DEBUG("Entering.");

	if (stat(filename, &st) == 0) {
		filebuffer = g_malloc(st.st_size);
		infile = open(filename, O_RDONLY);
		if (infile != -1) {
			bytes_read = read(infile, filebuffer, st.st_size);
			close(infile);
			buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(var->Widget));
			if (bytes_read > 0)
				gtk_text_buffer_set_text(buffer, filebuffer, bytes_read);
			else
				gtk_text_buffer_set_text(buffer, "", 0);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n",
				__func__, filename);
		}
		g_free(filebuffer);
	} else {
		fprintf(stderr, "%s(): Couldn't stat '%s'.\n", __func__, filename);
	}

	GDG_DEBUG("Exiting.");
}
