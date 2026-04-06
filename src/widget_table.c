/*
 * widget_table.c:
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
#include "stringman.h"
#include "tag_attributes.h"


#include "gdg_debug.h"
/* Local function prototypes, located at file bottom */
static void widget_table_input_by_command(variable *var, char *filename,
	gint command_or_file);
static void widget_table_input_by_file(variable *var, char *filename);
static void widget_table_input_by_items(variable *var);
static void widget_table_click_column_callback(GtkTreeViewColumn *column,
	gpointer user_data);
gboolean widget_table_changed_callback(GtkTreeSelection *treeselection,
	variable *var);
gint widget_table_natcmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data);
gint widget_table_natcasecmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data);
static gint _widget_table_natcmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data, gint sensitive);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_table_clear(variable *var)
{
	GtkTreeModel     *model;

	GDG_DEBUG("Entering.");

	model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
	gtk_list_store_clear(GTK_LIST_STORE(model));

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_table_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GList            *element;
	GtkCellRenderer  *renderer;
	GtkListStore     *store;
	GtkTreeSelection *selection;
	GtkTreeViewColumn *col;
	GtkWidget        *widget;
	GType            *column_types;
	gchar            *value;
	gint              column;
	gint              n_columns;
	gint              sort_function;
	list_t           *sliced = NULL;

	GDG_DEBUG("Entering.");

	/* Determine column count and titles from label attribute */
	if (attributeset_is_avail(Attr, ATTR_LABEL)) {
		sliced = linecutter(g_strdup(attributeset_get_first(
			&element, Attr, ATTR_LABEL)), '|');
		n_columns = sliced->n_lines;
	} else {
		n_columns = 1;
	}

	/* Create a GtkListStore with n_columns of G_TYPE_STRING */
	column_types = g_new(GType, n_columns);
	for (column = 0; column < n_columns; column++)
		column_types[column] = G_TYPE_STRING;
	store = gtk_list_store_newv(n_columns, column_types);
	g_free(column_types);

	/* Create the GtkTreeView */
	widget = gtk_tree_view_new_with_model(GTK_TREE_MODEL(store));
	g_object_unref(store);

	/* Add columns with text cell renderers */
	for (column = 0; column < n_columns; column++) {
		renderer = gtk_cell_renderer_text_new();
		if (sliced && column < sliced->n_lines && sliced->line[column]) {
			col = gtk_tree_view_column_new_with_attributes(
				sliced->line[column], renderer, "text", column, NULL);
		} else {
			col = gtk_tree_view_column_new_with_attributes(
				"", renderer, "text", column, NULL);
		}
		gtk_tree_view_column_set_resizable(col, TRUE);
		gtk_tree_view_append_column(GTK_TREE_VIEW(widget), col);
	}

	if (sliced) list_t_free(sliced);	/* Free linecutter memory */

	if (attr) {
		/* Get sort-function (custom) */
		if ((value = get_tag_attribute(attr, "sort-function"))) {
			sort_function = atoi(value);
			if (sort_function == 1) {
				for (column = 0; column < n_columns; column++)
					gtk_tree_sortable_set_sort_func(GTK_TREE_SORTABLE(store),
						column, widget_table_natcmp,
						GINT_TO_POINTER(column), NULL);
			} else if (sort_function == 2) {
				for (column = 0; column < n_columns; column++)
					gtk_tree_sortable_set_sort_func(GTK_TREE_SORTABLE(store),
						column, widget_table_natcasecmp,
						GINT_TO_POINTER(column), NULL);
			}
		}
		/* Get auto-sort: set the sort column on the model */
		if ((value = get_tag_attribute(attr, "auto-sort")) &&
			((strcasecmp(value, "true") == 0) || (strcasecmp(value, "yes") == 0) ||
			(atoi(value) == 1))) {
			gint sort_col = 0;
			GtkSortType sort_type_val = GTK_SORT_ASCENDING;
			/* Get sort-column (custom) */
			if ((value = get_tag_attribute(attr, "sort-column")))
				sort_col = atoi(value);
			/* Get sort-type (custom) */
			if ((value = get_tag_attribute(attr, "sort-type")))
				sort_type_val = (GtkSortType)atoi(value);
			gtk_tree_sortable_set_sort_column_id(GTK_TREE_SORTABLE(store),
				sort_col, sort_type_val);
		}
		/* Get column-header-active (custom) */
		if ((value = get_tag_attribute(attr, "column-header-active"))) {
			sliced = linecutter(g_strdup(value), '|');
			for (column = 0; column < sliced->n_lines; column++) {
				col = gtk_tree_view_get_column(GTK_TREE_VIEW(widget), column);
				if (col) {
					if ((strcasecmp(sliced->line[column], "true") == 0) ||
						(strcasecmp(sliced->line[column], "yes") == 0) ||
						(atoi(sliced->line[column]) == 1)) {
						gtk_tree_view_column_set_clickable(col, TRUE);
					} else {
						gtk_tree_view_column_set_clickable(col, FALSE);
					}
				}
			}
			if (sliced) list_t_free(sliced);	/* Free linecutter memory */
		}
		/* Get column-visible (custom) */
		if ((value = get_tag_attribute(attr, "column-visible"))) {
			sliced = linecutter(g_strdup(value), '|');
			for (column = 0; column < sliced->n_lines; column++) {
				col = gtk_tree_view_get_column(GTK_TREE_VIEW(widget), column);
				if (col) {
					if ((strcasecmp(sliced->line[column], "true") == 0) ||
						(strcasecmp(sliced->line[column], "yes") == 0) ||
						(atoi(sliced->line[column]) == 1)) {
						gtk_tree_view_column_set_visible(col, TRUE);
					} else {
						gtk_tree_view_column_set_visible(col, FALSE);
					}
				}
			}
			if (sliced) list_t_free(sliced);	/* Free linecutter memory */
		}
		/* Get selection-mode (custom) */
		if ((value = get_tag_attribute(attr, "selection-mode"))) {
			selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(widget));
			if (strcasecmp(value, "multiple") == 0 ||
				atoi(value) == GTK_SELECTION_MULTIPLE) {
				gtk_tree_selection_set_mode(selection, GTK_SELECTION_MULTIPLE);
			} else if (strcasecmp(value, "browse") == 0 ||
				atoi(value) == GTK_SELECTION_BROWSE) {
				gtk_tree_selection_set_mode(selection, GTK_SELECTION_BROWSE);
			} else if (strcasecmp(value, "none") == 0 ||
				atoi(value) == GTK_SELECTION_NONE) {
				gtk_tree_selection_set_mode(selection, GTK_SELECTION_NONE);
			} else {
				gtk_tree_selection_set_mode(selection, GTK_SELECTION_SINGLE);
			}
		}
	}

	GDG_DEBUG("Exiting.");

	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_table_envvar_all_construct(variable *var)
{
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	gchar            *line;
	gchar            *string;
	gchar            *text;
	gchar            *value;
	gint              column = 0;
	gint              row = 0;
	gboolean          valid;

	GDG_DEBUG("Entering.");

	/* Which column should we export */
	if (var->widget_tag_attr) {
		/* Get exported-column */
		if ((value = get_tag_attribute(var->widget_tag_attr, "exported-column")))
			column = atoi(value);
	}

	model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
	line = g_strdup_printf("%s_ALL=\"", var->Name);
	valid = gtk_tree_model_get_iter_first(model, &iter);
	while (valid) {
		gtk_tree_model_get(model, &iter, column, &string, -1);
		if (row == 0) {
			text = g_strconcat(line, "'", string ? string : "", "'", NULL);
		} else {
			text = g_strconcat(line, " '", string ? string : "", "'", NULL);
		}
		g_free(line);
		line = text;
		g_free(string);
		row++;
		valid = gtk_tree_model_iter_next(model, &iter);
	}
	string = g_strconcat(line, "\"\n", NULL);
	g_free(line);

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_table_envvar_construct(GtkWidget *widget)
{
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	GtkTreeSelection *selection;
	gchar            *line;
	gchar            *string;
	gchar            *text;
	gchar            *value;
	gint              column = 0;
	gint              selectionmode = GTK_SELECTION_SINGLE;
	gboolean          initialrow;
	GList            *selected_rows, *node;
	variable         *var = find_variable_by_widget(widget);

	GDG_DEBUG("Entering.");

	if (var->widget_tag_attr) {
		/* Get current selection-mode */
		if ((value = get_tag_attribute(var->widget_tag_attr, "selection-mode")))
			selectionmode = atoi(value);
		/* Get exported-column */
		if ((value = get_tag_attribute(var->widget_tag_attr, "exported-column")))
			column = atoi(value);
	}

	GDG_DEBUG("widget=%p selectionmode=%i column=%i", widget, selectionmode, column);

	selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(widget));
	model = gtk_tree_view_get_model(GTK_TREE_VIEW(widget));

	if (selectionmode == GTK_SELECTION_NONE) {
		string = g_strdup("");	/* Nothing is selected */
	} else if (selectionmode == GTK_SELECTION_MULTIPLE) {
		initialrow = TRUE;
		line = g_strdup("");
		selected_rows = gtk_tree_selection_get_selected_rows(selection, &model);
		for (node = selected_rows; node != NULL; node = node->next) {
			GtkTreePath *path = (GtkTreePath *)node->data;
			if (gtk_tree_model_get_iter(model, &iter, path)) {
				gtk_tree_model_get(model, &iter, column, &string, -1);
				if (initialrow) {
					text = g_strconcat(line, string ? string : "", NULL);
					initialrow = FALSE;
				} else {
					text = g_strconcat(line, "\n", string ? string : "", NULL);
				}
				g_free(line);
				line = text;
				g_free(string);
			}
		}
		g_list_foreach(selected_rows, (GFunc)gtk_tree_path_free, NULL);
		g_list_free(selected_rows);
		string = line;
	} else {
		/* Default GTK_SELECTION_SINGLE and GTK_SELECTION_BROWSE */
		if (gtk_tree_selection_get_selected(selection, &model, &iter)) {
			gtk_tree_model_get(model, &iter, column, &value, -1);
			string = value ? value : g_strdup("");
		} else {
			string = g_strdup("");
		}
	}

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_table_fileselect(
	variable *var, const char *name, const char *value)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_table_refresh(variable *var)
{
	GList            *element;
	GtkTreePath      *path;
	GtkTreeSelection *selection;
	gchar            *act;
	gchar            *value;
	gint              initialised = FALSE;
	gint              selected_row;

	GDG_DEBUG("Entering.");

	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = (gint)(intptr_t)g_object_get_data(G_OBJECT(var->Widget), "_initialised");

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_table_input_by_command(var, act + 8, TRUE);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_table_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_table_input_by_items(var);

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if (attributeset_is_avail(var->Attributes, ATTR_DEFAULT))
			fprintf(stderr, "%s(): <default> not implemented for this widget.\n",
				__func__);
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||	/* Deprecated */
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);

		/* Connect signals */
		/* cursor-changed on the GtkTreeView */
		g_signal_connect(G_OBJECT(var->Widget), "cursor-changed",
			G_CALLBACK(on_any_widget_cursor_changed_event), (gpointer)var->Attributes);
		/* selection "changed" signal routed through a local callback */
		selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(var->Widget));
		g_signal_connect(selection, "changed",
			G_CALLBACK(widget_table_changed_callback), (gpointer)var);

		/* Connect "clicked" signal on each column header for sorting */
		{
			gint n_cols = gtk_tree_model_get_n_columns(
				gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget)));
			gint i;
			for (i = 0; i < n_cols; i++) {
				GtkTreeViewColumn *tvcol = gtk_tree_view_get_column(
					GTK_TREE_VIEW(var->Widget), i);
				if (tvcol && gtk_tree_view_column_get_clickable(tvcol)) {
					g_object_set_data(G_OBJECT(tvcol), "_column-index",
						GINT_TO_POINTER(i));
					g_signal_connect(tvcol, "clicked",
						G_CALLBACK(widget_table_click_column_callback),
						(gpointer)var);
				}
			}
		}
	}

	if (var->widget_tag_attr) {
		/* Get selected-row (custom) */
		if ((value = get_tag_attribute(var->widget_tag_attr, "selected-row"))) {
			selected_row = atoi(value);
			if (selected_row >= 0) {
				selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(var->Widget));
				path = gtk_tree_path_new_from_indices(selected_row, -1);
				gtk_tree_selection_select_path(selection, path);
				gtk_tree_view_scroll_to_cell(GTK_TREE_VIEW(var->Widget),
					path, NULL, FALSE, 0, 0);
				gtk_tree_path_free(path);
			}
		}
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_table_removeselected(variable *var)
{
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	GtkTreeSelection *selection;
	gchar            *value;
	gint              selectionmode = GTK_SELECTION_SINGLE;
	GList            *selected_rows, *node, *row_refs = NULL;

	GDG_DEBUG("Entering.");

	if (var->widget_tag_attr) {
		/* Get current selection-mode */
		if ((value = get_tag_attribute(var->widget_tag_attr, "selection-mode")))
			selectionmode = atoi(value);
	}

	GDG_DEBUG("widget=%p selectionmode=%i", var->Widget, selectionmode);

	selection = gtk_tree_view_get_selection(GTK_TREE_VIEW(var->Widget));
	model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));

	if (selectionmode == GTK_SELECTION_NONE) {
		/* Nothing to do */
	} else if (selectionmode == GTK_SELECTION_MULTIPLE) {
		/* Collect row references first, then remove, since paths
		 * become invalid after removal */
		selected_rows = gtk_tree_selection_get_selected_rows(selection, &model);
		for (node = selected_rows; node != NULL; node = node->next) {
			GtkTreePath *path = (GtkTreePath *)node->data;
			GtkTreeRowReference *ref = gtk_tree_row_reference_new(model, path);
			row_refs = g_list_prepend(row_refs, ref);
		}
		g_list_foreach(selected_rows, (GFunc)gtk_tree_path_free, NULL);
		g_list_free(selected_rows);

		for (node = row_refs; node != NULL; node = node->next) {
			GtkTreeRowReference *ref = (GtkTreeRowReference *)node->data;
			GtkTreePath *path = gtk_tree_row_reference_get_path(ref);
			if (path) {
				if (gtk_tree_model_get_iter(model, &iter, path))
					gtk_list_store_remove(GTK_LIST_STORE(model), &iter);
				gtk_tree_path_free(path);
			}
			gtk_tree_row_reference_free(ref);
		}
		g_list_free(row_refs);
	} else {
		/* Default GTK_SELECTION_SINGLE and GTK_SELECTION_BROWSE */
		if (gtk_tree_selection_get_selected(selection, &model, &iter)) {
			gtk_list_store_remove(GTK_LIST_STORE(model), &iter);
		}
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_table_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	gchar            *act;
	gchar            *filename = NULL;
	gchar            *line;
	gchar            *string;
	gchar            *text;
	gint              column, columnmax;
	gint              row = 0;
	gboolean          valid;

	GDG_DEBUG("Entering.");

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

			model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
			columnmax = gtk_tree_model_get_n_columns(model);

			valid = gtk_tree_model_get_iter_first(model, &iter);
			while (valid) {

				line = g_strdup("");
				for (column = 0; column < columnmax; column++) {

					gtk_tree_model_get(model, &iter, column, &string, -1);

					if (column == 0) {
						text = g_strconcat(line, string ? string : "", NULL);
					} else {
						text = g_strconcat(line, "|", string ? string : "", NULL);
					}
					g_free(line);
					line = text;
					g_free(string);
				}
				if (row == 0) {
					fprintf(outfile, "%s", line);
				} else {
					fprintf(outfile, "\n%s", line);
				}
				g_free(line);

				row++;
				valid = gtk_tree_model_iter_next(model, &iter);
			}

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
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_table_input_by_command(variable *var, char *filename,
	gint command_or_file)
{
	FILE             *infile;
	GtkListStore     *store;
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	gchar             line[512];
	gint              count;
	gint              col;
	gint              n_columns;
	list_t           *sliced;

	GDG_DEBUG("Entering.");

	if (command_or_file) {
		infile = widget_opencommand(filename);
	} else {
		infile = fopen(filename, "r");
	}

	/* Opening pipe for reading... */
	if (infile) {
		model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
		store = GTK_LIST_STORE(model);
		n_columns = gtk_tree_model_get_n_columns(model);

		/* Read the file one line at a time (trailing [CR]LFs are read too) */
		while (fgets(line, 512, infile) != NULL) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;
			sliced = linecutter(g_strdup(line), '|');
			gtk_list_store_append(store, &iter);
			for (col = 0; col < n_columns; col++) {
				if (col < sliced->n_lines && sliced->line[col]) {
					gtk_list_store_set(store, &iter, col, sliced->line[col], -1);
				} else {
					gtk_list_store_set(store, &iter, col, "", -1);
				}
			}
			if (sliced) list_t_free(sliced);	/* Free linecutter memory */
		}
		/* Close the file */
		pclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_table_input_by_file(variable *var, char *filename)
{
	GDG_DEBUG("Entering.");

	widget_table_input_by_command(var, filename, FALSE);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_table_input_by_items(variable *var)
{
	GList            *element;
	GtkListStore     *store;
	GtkTreeIter       iter;
	GtkTreeModel     *model;
	gchar            *text;
	gint              col;
	gint              n_columns;
	list_t           *sliced;

	GDG_DEBUG("Entering.");

	g_assert(var->Attributes != NULL && var->Widget != NULL);

	model = gtk_tree_view_get_model(GTK_TREE_VIEW(var->Widget));
	store = GTK_LIST_STORE(model);
	n_columns = gtk_tree_model_get_n_columns(model);

	text = attributeset_get_first(&element, var->Attributes, ATTR_ITEM);
	while (text != NULL) {
		sliced = linecutter(g_strdup(text), '|');
		gtk_list_store_append(store, &iter);
		for (col = 0; col < n_columns; col++) {
			if (col < sliced->n_lines && sliced->line[col]) {
				gtk_list_store_set(store, &iter, col, sliced->line[col], -1);
			} else {
				gtk_list_store_set(store, &iter, col, "", -1);
			}
		}
		if (sliced) list_t_free(sliced);	/* Free linecutter memory */
		text = attributeset_get_next(&element, var->Attributes, ATTR_ITEM);
	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Click Column Callback                                               *
 ***********************************************************************/
/* Table Widget Behaviour
 * ----------------------
 * Assuming that the default sort direction is ascending:
 *
 * Click column 0 and it'll sort ascending.
 * Click column 1 and it'll sort ascending.
 * Click column 1 and it'll sort descending having flipped.
 * Click column 0 and it'll sort descending.
 * Click column 1 and it'll sort descending.
 */

static void widget_table_click_column_callback(GtkTreeViewColumn *tvcol,
	gpointer user_data)
{
	variable         *var = (variable *)user_data;
	GtkWidget        *widget = var->Widget;
	GtkTreeModel     *model;
	gint              column;
	gint              last_column = -1;
	GtkSortType       sort_type;
	gint              current_sort_col;

	GDG_DEBUG("Entering.");

	column = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(tvcol), "_column-index"));
	model = gtk_tree_view_get_model(GTK_TREE_VIEW(widget));

	/* Get last recorded column if it exists */
	if (g_object_get_data(G_OBJECT(widget), "_last-column") != NULL) {
		last_column = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(widget), "_last-column"));
		last_column--;
	}

	GDG_DEBUG("column=%i last-column=%i", column, last_column);

	/* Get the current sort type from the model */
	gtk_tree_sortable_get_sort_column_id(GTK_TREE_SORTABLE(model),
		&current_sort_col, &sort_type);

	/* If last recorded column matches column then flip sort direction */
	if (last_column == column) {
		sort_type = (sort_type == GTK_SORT_ASCENDING) ?
			GTK_SORT_DESCENDING : GTK_SORT_ASCENDING;
	}

	/* Store "last-column" as a piece of widget data (recreated if exists) */
	/* Warning: Storing zero kills the piece of data so we have to
	 * maintain it with +1 on set, -1 on get */
	g_object_set_data(G_OBJECT(widget), "_last-column",
		GINT_TO_POINTER(column + 1));

	/* Set the sort column and type - sorting happens automatically */
	gtk_tree_sortable_set_sort_column_id(GTK_TREE_SORTABLE(model),
		column, sort_type);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Changed Callback                                                    *
 ***********************************************************************/

gboolean widget_table_changed_callback(GtkTreeSelection *treeselection,
	variable *var)
{
	GDG_DEBUG("Entering.");

	GDG_DEBUG("treeselection=%p var->Widget=%p", treeselection, var->Widget);

	/* Pass the correct var->Widget which will be the GtkTreeView */
	on_any_widget_changed_event(var->Widget, var->Attributes);

	GDG_DEBUG("Exiting.");

	return TRUE;
}

/***********************************************************************
 * Natural Compare                                                     *
 ***********************************************************************/

gint widget_table_natcmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data)
{
	return _widget_table_natcmp(model, a, b, user_data, TRUE);
}

gint widget_table_natcasecmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data)
{
	return _widget_table_natcmp(model, a, b, user_data, FALSE);
}

static gint _widget_table_natcmp(GtkTreeModel *model, GtkTreeIter *a,
	GtkTreeIter *b, gpointer user_data, gint sensitive)
{
	gchar            *r1 = NULL;
	gchar            *r2 = NULL;
	gint              retval;

	GDG_DEBUG("Entering.");

	gtk_tree_model_get(model, a, GPOINTER_TO_INT(user_data), &r1, -1);
	gtk_tree_model_get(model, b, GPOINTER_TO_INT(user_data), &r2, -1);

	GDG_DEBUG("r1=\"%s\" r2=\"%s\"", r1, r2);

	retval = strnatcmp(r1, r2, sensitive);

	g_free(r1);
	g_free(r2);

	GDG_DEBUG("Exiting.");

	return retval;
}
