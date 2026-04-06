/*
 * widget_eventbox.c: 
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
static void widget_eventbox_input_by_command(variable *var, char *command);
static void widget_eventbox_input_by_file(variable *var, char *filename);
static void widget_eventbox_input_by_items(variable *var);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_eventbox_clear(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Clear not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_eventbox_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;
	stackelement      s;

	GDG_DEBUG("Entering.");

	/* Create the eventbox widget */
	widget = gtk_event_box_new();

	/* Pop the widgets that the eventbox will contain and add them */
	s = pop();
	gtk_container_add(GTK_CONTAINER(widget), s.widgets[0]);

	GDG_DEBUG("Exiting.");

	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_eventbox_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");

	GDG_DEBUG("Entering.");

	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_eventbox_envvar_construct(GtkWidget *widget)
{
	gchar            *string;

	GDG_DEBUG("Entering.");

	string = g_strdup("");

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_eventbox_fileselect(
	variable *var, const char *name, const char *value)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_eventbox_refresh(variable *var)
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
			widget_eventbox_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5)
			widget_eventbox_input_by_file(var, act + 5);
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_eventbox_input_by_items(var);

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if (attributeset_is_avail(var->Attributes, ATTR_LABEL))
			fprintf(stderr, "%s(): <label> not implemented for this widget.\n",
				__func__);
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

void widget_eventbox_removeselected(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_eventbox_save(variable *var)
{
	GDG_DEBUG("Entering.");

#if 0	/* Pointless since loading doesn't work at run-time */
	FILE             *outfile;
	GList            *element;
	gboolean          above_child;
	gboolean          visible_window;
	gchar            *act;
	gchar            *filename = NULL;
	gchar             string[32];
	/* We'll use the output file filename if available */
	act = attributeset_get_first(&element, var->Attributes, ATTR_OUTPUT);
	while (act) {
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			filename = act + 5;
			break;
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_OUTPUT);
	}

	/* If we have a valid filename then open it and dump the
	 * widget's data to it */
	if (filename) {
		if ((outfile = fopen(filename, "w"))) {

			above_child = gtk_event_box_get_above_child(GTK_EVENT_BOX(var->Widget));
			if (above_child) {
				strcpy(string, "true");
			} else {
				strcpy(string, "false");
			}
			visible_window = gtk_event_box_get_visible_window(GTK_EVENT_BOX(var->Widget));
			if (visible_window) {
				strcat(string, "|true");
			} else {
				strcat(string, "|false");
			}
			fprintf(outfile, "%s", string);

			/* Close the file */
			fclose(outfile);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for writing.\n",
				__func__, filename);
		}
	} else {
		fprintf(stderr, "%s(): No <output file> directive found.\n", __func__);
	}
#endif

	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_eventbox_input_by_command(variable *var, char *command)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): <input> not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_eventbox_input_by_file(variable *var, char *filename)
{
	GDG_DEBUG("Entering.");

#if 0	/* At run-time this has no effect -- shame */
	FILE             *infile;
	gchar             line[512];
	gint              count;
	list_t           *sliced;
	if ((infile = fopen(filename, "r"))) {
		/* Just one line */
		if (fgets(line, 512, infile)) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;

			sliced = linecutter(g_strdup(line), '|');
			GDG_DEBUG("line=%s", line);
			GDG_DEBUG("sliced->n_lines=%i", sliced->n_lines);
			GDG_DEBUG("sliced->line[0]=%s", sliced->line[0]);
			GDG_DEBUG("sliced->line[1]=%s", sliced->line[1]);
			for (count = 0; count < sliced->n_lines; count++) {
				if ((strcasecmp(sliced->line[count], "true") == 0) ||
					(strcasecmp(sliced->line[count], "yes") == 0) ||
					(atoi(sliced->line[count]) == 1)) {
					if (count == 0) {
GDG_DEBUG("setting count=%i TRUE", count);
						gtk_event_box_set_above_child(GTK_EVENT_BOX(
							var->Widget), TRUE);
					} else {
GDG_DEBUG("setting count=%i TRUE", count);
						gtk_event_box_set_visible_window(GTK_EVENT_BOX(
							var->Widget), TRUE);
					}
				} else if ((strcasecmp(sliced->line[count], "false") == 0) ||
					(strcasecmp(sliced->line[count], "no") == 0) ||
					(strcasecmp(sliced->line[count], "0") == 0)) {
					if (count == 0) {
GDG_DEBUG("setting count=%i FALSE", count);
						gtk_event_box_set_above_child(GTK_EVENT_BOX(
							var->Widget), FALSE);
					} else {
GDG_DEBUG("setting count=%i FALSE", count);
						gtk_event_box_set_visible_window(GTK_EVENT_BOX(
							var->Widget), FALSE);
					}
				}
			}
			if (sliced) list_t_free(sliced);	/* Free linecutter memory */
		}

		/* Close the file */
		fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}
#endif

	fprintf(stderr, "%s(): <input file> not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_eventbox_input_by_items(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}
