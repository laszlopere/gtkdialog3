/*
 * widget_list.c:
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <laszlopere@gmail.com>
 * Copyright (C) 2011-2012  Thunor <thunorsif@hotmail.com>
 * Copyright (C) 2026       László Pere <laszlopere@gmail.com>
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
/* Column index for our single-column list store */
enum {
	LIST_COLUMN_TEXT = 0,
	LIST_NUM_COLUMNS
};

/* Local function prototypes, located at file bottom */
static void widget_list_input_by_command(variable *var, char *filename,
	gint command_or_file);
static void widget_list_input_by_file(variable *var, char *filename);
static void widget_list_input_by_items(variable *var);

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_list_clear(variable *var)
{
	GtkListStore     *store;


	store = GTK_LIST_STORE(gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget)));
	gtk_list_store_clear(store);

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_list_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;
	GtkListStore     *store;
	GtkCellRenderer  *renderer;
	GtkTreeViewColumn *column;
	GtkTreeSelection *selection;


	/* Create a list store with a single text column */
	store = gtk_list_store_new(LIST_NUM_COLUMNS, G_TYPE_STRING);

	/* Create a tree view with this model */
	widget = gtk_tree_view_new_with_model(GTK_TREE_MODEL(store));
	g_object_unref(store);  /* The tree view holds a reference now */

	/* Hide the column header since the old GtkList had none */
	gtk_tree_view_set_headers_visible(GTK_TREE_VIEW(widget), FALSE);

	/* Add a text column renderer */
	renderer = gtk_cell_renderer_text_new();
	column = gtk_tree_view_column_new_with_attributes(
		"Text", renderer, "text", LIST_COLUMN_TEXT, NULL);
	gtk_tree_view_append_column(GTK_TREE_VIEW(widget), column);

	/* Set selection mode to single */
	selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(widget));
	gtk_tree_selection_set_mode(selection, GTK_SELECTION_SINGLE);


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_list_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_list_envvar_construct(GtkWidget *widget)
{
	GtkTreeSelection *selection;
	GtkTreeModel     *model;
	GtkTreeIter       iter;
	gchar            *string;


	selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(widget));
	if (gtk_tree_selection_get_selected(selection, &model, &iter)) {
		gtk_tree_model_get(model, &iter, LIST_COLUMN_TEXT, &string, -1);
	} else {
		string = g_strdup("");
	}


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_list_fileselect(
	variable *var, const char *name, const char *value)
{


	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_list_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gchar            *value;
	gint              initialised = FALSE;
	gint              selected_row;


	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_list_input_by_command(var, act + 8, TRUE);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_list_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_list_input_by_items(var);

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if (attributeset_is_avail(var->Attributes, ATTR_LABEL))
			fprintf(stderr, "%s(): <label> not implemented for this widget.\n",
				__func__);
		if (attributeset_is_avail(var->Attributes, ATTR_DEFAULT))
			fprintf(stderr, "%s(): <default> not implemented for this widget.\n",
				__func__);
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||	/* Deprecated */
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);

		/* Connect signals - use cursor-changed for GtkTreeView */
		g_signal_connect(G_OBJECT(var->Widget), "cursor-changed",
			G_CALLBACK(on_any_widget_cursor_changed_event),
			(gpointer)var->Attributes);

	}

	/* Select specified row if requested */
	if (var->widget_tag_attr) {
		/* Get selected-row (custom) */
		if ((value = get_tag_attribute(var->widget_tag_attr, "selected-row"))) {
			selected_row = atoi(value);
			if (selected_row >= 0) {
				GtkTreePath *path;
				path = gtk_tree_path_new_from_indices(selected_row, -1);
				gtk_tree_view_set_cursor(GTK_TREE_VIEW(var->Widget),
					path, NULL, FALSE);
				gtk_tree_path_free(path);
			}
		}
	}

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_list_removeselected(variable *var)
{
	GtkTreeSelection *selection;
	GtkTreeModel     *model;
	GtkTreeIter       iter;


	selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(var->Widget));
	if (gtk_tree_selection_get_selected(selection, &model, &iter)) {
		gtk_list_store_remove(GTK_LIST_STORE(model), &iter);
	}

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_list_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	GtkTreeModel     *model;
	GtkTreeIter       iter;
	gchar            *act;
	gchar            *filename = NULL;
	gchar            *string;
	gint              count = 0;
	gboolean          valid;


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

			/* Iterate the list store and write each row's text */
			model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
			valid = gtk_tree_model_get_iter_first(model, &iter);
			while (valid) {
				gtk_tree_model_get(model, &iter, LIST_COLUMN_TEXT, &string, -1);
				GDG_DEBUG("row text='%s'", string);
				if (count == 0) {
					fprintf(outfile, "%s", string);
				} else {
					fprintf(outfile, "\n%s", string);
				}
				count++;
				g_free(string);
				valid = gtk_tree_model_iter_next(model, &iter);
			}

			/* Close the file */
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

static void widget_list_input_by_command(variable *var, char *filename,
	gint command_or_file)
{
	FILE             *infile;
	GtkListStore     *store;
	GtkTreeIter       iter;
	gchar             line[512];
	gint              count;


	if (command_or_file) {
		infile = widget_opencommand(filename);
	} else {
		infile = fopen(filename, "r");
	}

	/* Opening pipe for reading... */
	if (infile) {
		store = GTK_LIST_STORE(gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget)));

		/* Read the file one line at a time (trailing [CR]LFs are read too) */
		while (fgets(line, 512, infile) != NULL) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;

			/* Append a new row with the text */
			gtk_list_store_append(store, &iter);
			gtk_list_store_set(store, &iter, LIST_COLUMN_TEXT, line, -1);
		}
		/* Close the file */
		if (command_or_file)
			widget_closecommand(infile);
		else
			fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}

}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_list_input_by_file(variable *var, char *filename)
{

	widget_list_input_by_command(var, filename, FALSE);

}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_list_input_by_items(variable *var)
{
	GList            *element;
	GtkListStore     *store;
	GtkTreeIter       iter;
	gchar            *text;


	g_assert(var->Attributes != NULL && var->Widget != NULL);

	text = attributeset_get_first(&element, var->Attributes, ATTR_ITEM);
	if (text == NULL)
		return;

	store = GTK_LIST_STORE(gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget)));

	while (text != NULL) {
		gtk_list_store_append(store, &iter);
		gtk_list_store_set(store, &iter, LIST_COLUMN_TEXT, text, -1);
		text = attributeset_get_next(&element, var->Attributes, ATTR_ITEM);
	}

}
