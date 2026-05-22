/*
 * widget_buttonbox.c:
 * Gtkdialog - A small utility for fast and easy GUI building.
 * Copyright (C) 2003-2007  László Pere <laszlopere@gmail.com>
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

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_buttonbox_clear(variable *var)
{
	fprintf(stderr, "%s(): Clear not implemented for this widget.\n", __func__);
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_buttonbox_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	gchar            *value;
	gint              border_width;
	gint              n;
	GtkOrientation    orientation = GTK_ORIENTATION_HORIZONTAL;
	GtkButtonBoxStyle layout = GTK_BUTTONBOX_END;
	GtkWidget        *widget;
	stackelement      s;


	/* Support orientation attribute */
	if (attr &&
		(value = get_tag_attribute(attr, "orientation"))) {
		if (strcasecmp(value, "vertical") == 0)
			orientation = GTK_ORIENTATION_VERTICAL;
	}

	widget = gtk_button_box_new(orientation);
	gtk_box_set_spacing(GTK_BOX(widget), 6);

	/* Support layout attribute */
	if (attr &&
		(value = get_tag_attribute(attr, "layout"))) {
		if (strcasecmp(value, "spread") == 0)
			layout = GTK_BUTTONBOX_SPREAD;
		else if (strcasecmp(value, "edge") == 0)
			layout = GTK_BUTTONBOX_EDGE;
		else if (strcasecmp(value, "start") == 0)
			layout = GTK_BUTTONBOX_START;
		else if (strcasecmp(value, "end") == 0)
			layout = GTK_BUTTONBOX_END;
		else if (strcasecmp(value, "center") == 0)
			layout = GTK_BUTTONBOX_CENTER;
	}
	gtk_button_box_set_layout(GTK_BUTTON_BOX(widget), layout);

	if (attr &&
		(value = get_tag_attribute(attr, "margin"))) {
		border_width = atoi(value);
		gtk_container_set_border_width(GTK_CONTAINER(widget), border_width);
	}

	/* Pack the widgets into the container */
	s = pop();
	for (n = 0; n < s.nwidgets; ++n) {
		gtk_container_add(GTK_CONTAINER(widget), s.widgets[n]);
	}


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_buttonbox_envvar_all_construct(variable *var)
{
	return g_strdup("");
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_buttonbox_envvar_construct(GtkWidget *widget)
{
	return g_strdup("");
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_buttonbox_fileselect(
	variable *var, const char *name, const char *value)
{
	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_buttonbox_refresh(variable *var)
{
	gint              initialised = FALSE;


	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* Initialise these only once at start-up */
	if (!initialised) {
		/* Apply directives */
		if ((attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "false")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "disabled")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "no")) ||
			(attributeset_cmp_left(var->Attributes, ATTR_SENSITIVE, "0")))
			gtk_widget_set_sensitive(var->Widget, FALSE);
	}

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_buttonbox_removeselected(variable *var)
{
	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n", __func__);
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_buttonbox_save(variable *var)
{
	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);
}
