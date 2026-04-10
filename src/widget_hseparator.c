/*
 * widget_hseparator.c: 
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
static void widget_hseparator_input_by_command(variable *var, char *command);
static void widget_hseparator_input_by_file(variable *var, char *filename);
static void widget_hseparator_input_by_items(variable *var);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_hseparator_clear(variable *var)
{


	fprintf(stderr, "%s(): Clear not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_hseparator_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;


	if (Type == WIDGET_HSEPARATOR) {
		/* Thunor: My first new widget :) */
		widget = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
	} else {
		widget = gtk_separator_new(GTK_ORIENTATION_VERTICAL);
	}


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_hseparator_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_hseparator_envvar_construct(GtkWidget *widget)
{
	gchar            *string;


	string = g_strdup("");


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_hseparator_fileselect(
	variable *var, const char *name, const char *value)
{


	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_hseparator_refresh(variable *var)
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
			widget_hseparator_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_hseparator_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_hseparator_input_by_items(var);

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

void widget_hseparator_removeselected(variable *var)
{


	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_hseparator_save(variable *var)
{


	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_hseparator_input_by_command(variable *var, char *command)
{


	fprintf(stderr, "%s(): <input> not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_hseparator_input_by_file(variable *var, char *filename)
{


	fprintf(stderr, "%s(): <input file> not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_hseparator_input_by_items(variable *var)
{


	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

}
