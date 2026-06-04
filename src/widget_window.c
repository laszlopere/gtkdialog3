/*
 * widget_window.c: 
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <laszlopere@gmail.com>
 * Copyright (C) 2011-2012  Thunor <thunorsif@hotmail.com>
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
extern gboolean option_centering;
extern gchar *option_dbus_name;
extern gboolean have_geometry_xy;
extern gboolean have_geometry_dxdy;
extern gint geometry_dx;
extern gint geometry_dy;
extern gint geometry_x;
extern gint geometry_y;

/* Local function prototypes, located at file bottom */
static void widget_window_input_by_command(variable *var, char *command);
static void widget_window_input_by_file(variable *var, char *filename);
static void widget_window_input_by_items(variable *var);
static void widget_window_fix_size(GtkWidget *window, gpointer data);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_window_clear(variable *var)
{


	/* Well, it can't be null because something changes it to
	 * "Unnamed Window", and since the default is PACKAGE when
	 * no title has been declared I'll clear it to that */

	gtk_window_set_title(GTK_WINDOW(var->Widget), PACKAGE);

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_window_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	gchar            *value;
	GError           *error = NULL;
	GList            *accel_group = NULL;
	GList            *element;
	gint              border_width;
	GtkWidget        *widget;
	stackelement      s;


	/* Create the window widget */
	widget = gtk_window_new(GTK_WINDOW_TOPLEVEL);  

	/* Set a default window title. When --dbus-name was given, prefer it
	 * over PACKAGE so the window is identifiable per-instance (e.g. for
	 * AT-SPI driven tests); an explicit <window> title still wins. */
	attributeset_set_if_unset(Attr, ATTR_LABEL,
		option_dbus_name != NULL ? option_dbus_name : PACKAGE);
	gtk_window_set_title(GTK_WINDOW(widget), 
		attributeset_get_first(&element, Attr, ATTR_LABEL));

	/* Set a default title bar theme icon */
	gtk_window_set_icon_name(GTK_WINDOW(widget), PACKAGE);

	/* If requested set a title bar image by filename */
	if (attr) {
		if ((value = get_tag_attribute(attr, "image-name")))
			gtk_window_set_icon_from_file(GTK_WINDOW(widget),
				find_pixmap(value), &error);
	}

	/* Set a default border width */
	border_width = 5;
	if (attr && (value = get_tag_attribute(attr, "margin")))	/* Deprecated */
		border_width = atoi(value);
	gtk_container_set_border_width(GTK_CONTAINER(widget), border_width);

	/* If we have geometry given in the command line, we set that */
	if (have_geometry_dxdy)
		gtk_widget_set_size_request(widget, geometry_dx, geometry_dy);
	if (have_geometry_xy)
		gtk_window_move(GTK_WINDOW(widget), geometry_x, geometry_y);
	if (option_centering)
		gtk_window_set_position(GTK_WINDOW(widget),
			GTK_WIN_POS_CENTER_ALWAYS);

	/* Pop the widgets that the window will contain and add them */
	s = pop();
	gtk_container_add(GTK_CONTAINER(widget), s.widgets[0]);

	/* Fix GTK3 height-for-width window sizing: connect a handler that
	 * fires once after realization to correct the window size.
	 * Without this, windows containing wrapping GtkLabels are sized
	 * too tall because GTK3 computes height for the minimum width
	 * (which wraps text into many lines) even though the window
	 * actually uses the natural (wider) width. */
	if (!have_geometry_dxdy) {
		g_signal_connect(widget, "map",
			G_CALLBACK(widget_window_fix_size), NULL);
	}

	/* Thunor: Each menu created will have an accelerator group
	 * for its menuitems which will require adding to the window */
	if (accel_groups) {
		accel_group = g_list_first(accel_groups);
		while (accel_group) {
			gtk_window_add_accel_group(GTK_WINDOW(widget),
				GTK_ACCEL_GROUP(accel_group->data));
			GDG_DEBUG("Adding accel_group=%p to window", accel_group->data);
			accel_group = accel_group->next;
		}
		g_list_free(accel_groups);
		accel_groups = NULL;
	}


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_window_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_window_envvar_construct(GtkWidget *widget)
{
	gchar            *string;


	/* Thunor: Variables are exported before a window is launched which
	 * can be a problem if launching from a launched window because
	 * launched windows are required to contain a variable that matches
	 * the name of the program's envvar and this results in the program
	 * being overwritten with the window title ;) It took me a day to
	 * find this issue because the error was being reported by the parser
	 * but the problem was located in action_launchwindow. So window
	 * variables can't be exported, they must be reserved for scripts.
	 * 
	 * string = g_strdup(gtk_window_get_title(GTK_WINDOW(widget))); */
	string = NULL;


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_window_fileselect(
	variable *var, const char *name, const char *value)
{


	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_window_refresh(variable *var)
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
			widget_window_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_window_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_window_input_by_items(var);

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
		g_signal_connect(G_OBJECT(var->Widget), "delete-event",
			G_CALLBACK(window_delete_event_handler), NULL);

	}

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_window_removeselected(variable *var)
{


	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_window_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	gchar            *act;
	gchar            *filename = NULL;


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
			fprintf(outfile, "%s", gtk_window_get_title(GTK_WINDOW(var->Widget)));
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

static void widget_window_input_by_command(variable *var, char *command)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;


	GDG_DEBUG("command: '%s'", command);

	/* Opening pipe for reading... */
	if ((infile = widget_opencommand(command))) {
		/* Just one line */
		if (fgets(line, 512, infile)) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;

			gtk_window_set_title(GTK_WINDOW(var->Widget), line);

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

static void widget_window_input_by_file(variable *var, char *filename)
{
	FILE             *infile;
	gchar             line[512];
	gint              count;


	if ((infile = fopen(filename, "r"))) {
		/* Just one line */
		if (fgets(line, 512, infile)) {
			/* Enforce end of string in case of max chars read */
			line[512 - 1] = 0;
			/* Remove the trailing [CR]LFs */
			for (count = strlen(line) - 1; count >= 0; count--)
				if (line[count] == 13 || line[count] == 10) line[count] = 0;

			gtk_window_set_title(GTK_WINDOW(var->Widget), line);

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

static void widget_window_input_by_items(variable *var)
{


	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Fix Size                                                            *
 ***********************************************************************
 * Work around a GTK3 height-for-width window sizing issue.
 *
 * GtkWindow computes its initial height to accommodate the child's
 * minimum height, which for height-for-width children (e.g. wrapping
 * GtkLabels) is the height needed at the minimum width. This is much
 * larger than the height needed at the natural (actual) width, causing
 * a large vertical gap below the content.
 *
 * Fix: after the window is mapped, an idle handler queries the correct
 * height for the actual allocated width, then sets the child's minimum
 * width to lock in that width and resizes the window to the correct
 * (smaller) height.
 ***********************************************************************/

static gboolean widget_window_fix_size_idle(gpointer data)
{
	GtkWidget        *window = GTK_WIDGET(data);
	GtkWidget        *child;
	GtkAllocation     alloc;
	gint              child_width;
	gint              min_height, nat_height;
	gint              border_width;
	gint              correct_height;

	child = gtk_bin_get_child(GTK_BIN(window));
	if (child == NULL)
		return FALSE;

	/* Get the current window size (GTK chose the width correctly) */
	gtk_widget_get_allocation(window, &alloc);
	border_width = gtk_container_get_border_width(GTK_CONTAINER(window));
	child_width = alloc.width - 2 * border_width;

	/* Compute the correct height for the actual width */
	gtk_widget_get_preferred_height_for_width(child, child_width,
		&min_height, &nat_height);

	correct_height = nat_height + 2 * border_width;

	if (correct_height < alloc.height) {
		/* Set child's min width to current width so the window's
		 * minimum height is recomputed for this width, allowing
		 * gtk_window_resize to shrink the height */
		gtk_widget_set_size_request(child, child_width, -1);
		gtk_window_resize(GTK_WINDOW(window), alloc.width, correct_height);
	}

	return FALSE;  /* Run only once */
}

static void widget_window_fix_size(GtkWidget *window, gpointer data)
{
	/* Defer to an idle handler so GTK has finished its initial sizing
	 * and will honour our set_size_request + resize */
	g_idle_add(widget_window_fix_size_idle, window);
}
