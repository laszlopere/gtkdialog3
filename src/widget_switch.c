/*
 * widget_switch.c:
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <laszlopere@gmail.com>
 * Copyright (C) 2026       László Pere <laszlopere@gmail.com>
 * SPDX-License-Identifier: GPL-2.0-or-later
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
static void widget_switch_input_by_command(variable *var, char *command);
static void widget_switch_input_by_file(variable *var, char *filename);
static void widget_switch_input_by_items(variable *var);

/* Notes:
 * GtkSwitch uses "notify::active" signal instead of "toggled".
 * The callback signature is (GObject*, GParamSpec*, gpointer). */

static void on_switch_notify_active(GObject *gobject,
	GParamSpec *pspec, gpointer user_data)
{
	(void)pspec;
	widget_signal_executor(GTK_WIDGET(gobject),
		(AttributeSet *)user_data, "toggled");
}

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_switch_clear(variable *var)
{

	gtk_switch_set_active(GTK_SWITCH(var->Widget), FALSE);

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_switch_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;


	(void)Attr;
	(void)attr;
	(void)Type;

	widget = gtk_switch_new();


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_switch_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	(void)var;


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_switch_envvar_construct(GtkWidget *widget)
{
	gchar            *string;


	if (gtk_switch_get_active(GTK_SWITCH(widget))) {
		string = g_strdup("true");
	} else {
		string = g_strdup("false");
	}


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_switch_fileselect(
	variable *var, const char *name, const char *value)
{

	(void)var;
	(void)name;
	(void)value;

	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_switch_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gchar            *value;
	gint              initialised = FALSE;
	gint              is_active;


	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_switch_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_switch_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_switch_input_by_items(var);

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if (attributeset_is_avail(var->Attributes, ATTR_DEFAULT)) {
			value = attributeset_get_first(&element, var->Attributes, ATTR_DEFAULT);
			if ((strcasecmp(value, "true") == 0) ||
				(strcasecmp(value, "yes") == 0) || (atoi(value) == 1)) {
				is_active = 1;
			} else {
				is_active = 0;
			}
			gtk_switch_set_active(GTK_SWITCH(var->Widget), is_active);
		}
		if (attributeset_is_avail(var->Attributes, ATTR_HEIGHT))
			fprintf(stderr, "%s(): <height> not implemented for this widget.\n",
				__func__);
		if (attributeset_is_avail(var->Attributes, ATTR_WIDTH))
			fprintf(stderr, "%s(): <width> not implemented for this widget.\n",
				__func__);
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);

		/* Connect signals — GtkSwitch uses notify::active */
		g_signal_connect(G_OBJECT(var->Widget), "notify::active",
			G_CALLBACK(on_switch_notify_active), (gpointer)var->Attributes);
	}

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_switch_removeselected(variable *var)
{

	(void)var;

	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_switch_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	gchar            *act;
	gchar            *filename = NULL;
	gint              is_active;


	/* We'll use the output file filename if available */
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
			is_active = gtk_switch_get_active(GTK_SWITCH(var->Widget));
			if (is_active) fprintf(outfile, "%s", "true");
			else fprintf(outfile, "%s", "false");
			fclose(outfile);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for writing.\n",
				__func__, filename);
		}
	} else {
		fprintf(stderr, "%s(): No <output file> directive found.\n", __func__);
	}

}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_switch_input_by_command(variable *var, char *command)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;
	gint              is_active;


	if ((infile = widget_opencommand(command))) {
		if (fgets(line, 512, infile)) {
			line[512 - 1] = 0;
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;
			if ((strcasecmp(line, "true") == 0) ||
				(strcasecmp(line, "yes") == 0) || (atoi(line) == 1)) {
				is_active = 1;
			} else {
				is_active = 0;
			}
			gtk_switch_set_active(GTK_SWITCH(var->Widget), is_active);
		}
		widget_closecommand(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			command);
	}

}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_switch_input_by_file(variable *var, char *filename)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;
	gint              is_active;


	if ((infile = fopen(filename, "r"))) {
		if (fgets(line, 512, infile)) {
			line[512 - 1] = 0;
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;
			if ((strcasecmp(line, "true") == 0) ||
				(strcasecmp(line, "yes") == 0) || (atoi(line) == 1)) {
				is_active = 1;
			} else {
				is_active = 0;
			}
			gtk_switch_set_active(GTK_SWITCH(var->Widget), is_active);
		}
		fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}

}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_switch_input_by_items(variable *var)
{

	(void)var;

	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

}
