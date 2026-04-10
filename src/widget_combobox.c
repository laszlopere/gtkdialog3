/*
 * widget_combobox.c:
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <pipas@linux.pte.hu>
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
static void widget_combobox_input_by_command(variable *var, char *command);
static void widget_combobox_input_by_file(variable *var, char *filename);
static void widget_combobox_input_by_items(variable *var);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_combobox_clear(variable *var)
{
	GtkTreeModel     *model;
	gint              n_items, i;


	/* Remove all items from the combo box text model */
	model = gtk_combo_box_get_model(GTK_COMBO_BOX(var->Widget));
	n_items = gtk_tree_model_iter_n_children(model, NULL);
	for (i = n_items - 1; i >= 0; i--)
		gtk_combo_box_text_remove(GTK_COMBO_BOX_TEXT(var->Widget), i);

	/* Clear the entry */
	gtk_entry_set_text(GTK_ENTRY(gtk_bin_get_child(GTK_BIN(var->Widget))), "");

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_combobox_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;


	widget = gtk_combo_box_text_new_with_entry();


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_combobox_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_combobox_envvar_construct(GtkWidget *widget)
{
	gchar            *string;
	gchar            *text;


	text = (gchar*)gtk_entry_get_text(GTK_ENTRY(gtk_bin_get_child(GTK_BIN(widget))));
	string = g_strdup(text);


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_combobox_fileselect(
	variable *var, const char *name, const char *value)
{


	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_combobox_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gint              initialised = FALSE;


	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_combobox_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			widget_combobox_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_combobox_input_by_items(var);

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

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_combobox_removeselected(variable *var)
{


	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_combobox_save(variable *var)
{


	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_combobox_input_by_command(variable *var, char *command)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;


	GDG_DEBUG("command: '%s'", command);

	/* Opening pipe for reading... */
	if ((infile = widget_opencommand(command))) {
		/* Read the file one line at a time (trailing [CR]LFs are read too) */
		while (fgets(line, 512, infile)) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;
			gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(var->Widget), line);
		}
		/* Close the file */
		widget_closecommand(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			command);
	}

}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_combobox_input_by_file(variable *var, char *filename)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;


	if ((infile = fopen(filename, "r"))) {
		/* Read the file one line at a time (trailing [CR]LFs are read too) */
		while (fgets(line, 512, infile)) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;
			gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(var->Widget), line);
		}
		/* Close the file */
		fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}

}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_combobox_input_by_items(variable *var)
{
	GList            *element;
	gchar            *text;


	g_assert(var->Attributes != NULL && var->Widget != NULL);

	text = attributeset_get_first(&element, var->Attributes, ATTR_ITEM);
	if (text == NULL)
		return;

	while (text != NULL) {
		gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(var->Widget), text);
		text = attributeset_get_next(&element, var->Attributes, ATTR_ITEM);
	}

}
