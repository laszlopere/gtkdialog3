/*
 * widget_text.c: 
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  L�szl� Pere <pipas@linux.pte.hu>
 * Copyright (C) 2011-2012  Thunor <thunorsif@hotmail.com>
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
#include <gtk/gtk.h>
#include "config.h"
#include "gtkdialog.h"
#include "attributes.h"
#include "automaton.h"
#include "widgets.h"
#include "signals.h"
#include "tag_attributes.h"


#include "gdg_debug.h"
/* Local function prototypes, located at file bottom */
static void widget_text_input_by_command(variable *var, char *command);
static void widget_text_input_by_file(variable *var, char *filename);
static void widget_text_input_by_items(variable *var);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_text_clear(variable *var)
{

	GDG_DEBUG("Entering.");

	gtk_label_set_text(GTK_LABEL(var->Widget), "");

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_text_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GList            *element;
	GtkWidget        *widget;
	gchar            *value;

	GDG_DEBUG("Entering.");

	/* Set a default label if unset */
	attributeset_set_if_unset(Attr, ATTR_LABEL, "text");

	widget = gtk_label_new(attributeset_get_first(&element, Attr, ATTR_LABEL));

	/* Apply this property now to prevent visible resizing when shown */
	if (attr &&
		(value = get_tag_attribute(attr, "use-markup")) &&
		((strcasecmp(value, "true") == 0) ||
		(strcasecmp(value, "yes") == 0) || (atoi(value) == 1))) {
		gtk_label_set_use_markup(GTK_LABEL(widget), TRUE);
	}

	/* Enable line wrapping by default.
	 * In GTK3's height-for-width geometry, a wrapping label requests
	 * only its minimum width (longest word) by default, causing the
	 * window to be too narrow. Set width-chars to the longest line
	 * length so the label requests enough space for its content. */
	gtk_label_set_line_wrap(GTK_LABEL(widget), TRUE);
	{
		const gchar *label_text;
		gchar *plain_text = NULL;

		label_text = gtk_label_get_text(GTK_LABEL(widget));
		if (label_text) {
			/* Strip Pango markup if present to get visible text length */
			if (gtk_label_get_use_markup(GTK_LABEL(widget)))
				pango_parse_markup(label_text, -1, 0,
					NULL, &plain_text, NULL, NULL);

			const gchar *p = plain_text ? plain_text : label_text;
			gint max_len = 0, cur_len = 0;
			while (*p) {
				if (*p == '\n') {
					if (cur_len > max_len) max_len = cur_len;
					cur_len = 0;
				} else {
					cur_len++;
				}
				p++;
			}
			if (cur_len > max_len) max_len = cur_len;
			if (max_len > 0)
				gtk_label_set_width_chars(GTK_LABEL(widget), max_len);
			g_free(plain_text);
		}
	}

	GDG_DEBUG("Exiting.");

	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_text_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");

	GDG_DEBUG("Entering.");

	/* This function should not be connected-up by default */

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_text_envvar_construct(GtkWidget *widget)
{
	gchar            *string;

	GDG_DEBUG("Entering.");

	string = g_strdup(gtk_label_get_text(GTK_LABEL(widget)));

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_text_fileselect(
	variable *var, const char *name, const char *value)
{

	GDG_DEBUG("Entering.");

	gtk_label_set_text(GTK_LABEL(var->Widget), value);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_text_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gint              initialised = FALSE;

	GDG_DEBUG("Entering.");

	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_text_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_text_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_text_input_by_items(var);

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if (attributeset_is_avail(var->Attributes, ATTR_DEFAULT))
			fprintf(stderr, "%s(): <default> not implemented for this widget.\n",
				__func__);
		if (attributeset_is_avail(var->Attributes, ATTR_HEIGHT))
			fprintf(stderr, "%s(): <height> not implemented for this widget.\n",
				__func__);
		if (attributeset_is_avail(var->Attributes, ATTR_WIDTH))
			fprintf(stderr, "%s(): <width> not implemented for this widget.\n",
				__func__);
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||	/* Deprecated */
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);

		/* Connect signals */

	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_text_removeselected(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_text_save(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_text_input_by_command(variable *var, char *command)
{
	FILE             *infile;
	GString          *text = g_string_sized_new(512);
	gchar             line[512];

	GDG_DEBUG("Entering.");

	GDG_DEBUG("command: '%s'", command);

	/* Opening pipe for reading... */
	if ((infile = widget_opencommand(command))) {
		/* Read the file one line at a time */
		while (fgets(line, 512, infile)) {
			g_string_append(text, line);
		}

		if (gtk_label_get_use_markup(GTK_LABEL(var->Widget))) {
			gtk_label_set_markup(GTK_LABEL(var->Widget), text->str);
		} else {
			gtk_label_set_text(GTK_LABEL(var->Widget), text->str);
		}
		g_string_free(text, TRUE);

		/* Close the file */
		widget_closecommand(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			command);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_text_input_by_file(variable *var, char *filename)
{
	FILE             *infile;
	GString          *text = g_string_sized_new(512);
	gchar             line[512];

	GDG_DEBUG("Entering.");

	if ((infile = fopen(filename, "r"))) {
		/* Read the file one line at a time */
		while (fgets(line, 512, infile)) {
			g_string_append(text, line);
		}

		if (gtk_label_get_use_markup(GTK_LABEL(var->Widget))) {
			gtk_label_set_markup(GTK_LABEL(var->Widget), text->str);
		} else {
			gtk_label_set_text(GTK_LABEL(var->Widget), text->str);
		}
		g_string_free(text, TRUE);

		/* Close the file */
		fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_text_input_by_items(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}
