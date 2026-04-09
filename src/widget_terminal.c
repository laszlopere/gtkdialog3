/*
 * widget_terminal.c: 
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
#include "widget_terminal.h"
#include "attributes.h"
#include "automaton.h"
#include "widgets.h"
#include "signals.h"
#include "tag_attributes.h"
#include "gdg_debug.h"
#if HAVE_VTE
#include <vte/vte.h>
#endif


#define VTE_WARNING "The terminal (VteTerminal) widget requires \
a version of gtkdialog built with libvte."

/* Local function prototypes, located at file bottom */
static void widget_terminal_input_by_command(variable *var, char *command);
static void widget_terminal_input_by_file(variable *var, char *filename);
static void widget_terminal_input_by_items(variable *var);

/* Notes: */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_terminal_clear(variable *var)
{
	GDG_DEBUG("Entering.");

#if HAVE_VTE
	/* This won't result in child-exited being emitted */
	vte_terminal_reset(VTE_TERMINAL(var->Widget), TRUE, TRUE);
	widget_terminal_fork_command(var->Widget, var->widget_tag_attr);
#endif

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/
GtkWidget *widget_terminal_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;
#if HAVE_VTE
	GdkRGBA           color;
	GList            *element;
	gchar             tagattribute[256];
	gchar            *value;
	gint              width = -1, height = -1;
#endif

	GDG_DEBUG("Entering.");

#if HAVE_VTE
	/* Read declared directives */
	if (attributeset_is_avail(Attr, ATTR_WIDTH))
		width = atoi(attributeset_get_first(&element, Attr, ATTR_WIDTH));
	if (attributeset_is_avail(Attr, ATTR_HEIGHT))
		height = atoi(attributeset_get_first(&element, Attr, ATTR_HEIGHT));

	widget = vte_terminal_new();
	
	/* Until I added this, none of the functions that set various text
	 * foreground and background colours worked so I'm presuming that
	 * creating a new VteTerminal doesn't create a full palette */
	/* Default colors are set automatically in VTE 2.91 */

	if (attr) {
		/* The gtk property "font-desc" requires a pointer to a
		 * PangoFontDescription but the application developer can't pass
		 * anything other than a string here, so we'll convert it using
		 * a dedicated gtk function and then kill the tag attribute else
		 * widget_set_tag_attributes() will try to set it later */
		strcpy(tagattribute, "font-desc");
		if ((value = get_tag_attribute(attr, tagattribute))) {
			vte_terminal_set_font(VTE_TERMINAL(widget), pango_font_description_from_string(value));
			kill_tag_attribute(attr, tagattribute);
		}

		/* Again, "background-tint-color" requires a pointer to a
		 * GdkColor struct but we can convert a string like "#ff00ff" */
		strcpy(tagattribute, "background-tint-color");
		if ((value = get_tag_attribute(attr, tagattribute))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				/* background tint removed in VTE 2.91 */
			}
			kill_tag_attribute(attr, tagattribute);
		}

		/* Get custom tag attribute "font-name" */
		if ((value = get_tag_attribute(attr, "font-name"))) {
			vte_terminal_set_font(VTE_TERMINAL(widget), pango_font_description_from_string(value));
		}

		/* Get custom tag attribute "text-background-color" */
		if ((value = get_tag_attribute(attr, "text-background-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				vte_terminal_set_color_background(VTE_TERMINAL(widget), &color);  /* Uses GdkRGBA in VTE 2.91 */
			}
		}

		/* Get custom tag attribute "text-foreground-color" */
		if ((value = get_tag_attribute(attr, "text-foreground-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				vte_terminal_set_color_foreground(VTE_TERMINAL(widget), &color);
			}
		}

		/* Get custom tag attribute "bold-foreground-color" */
		if ((value = get_tag_attribute(attr, "bold-foreground-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				vte_terminal_set_color_bold(VTE_TERMINAL(widget), &color);
			}
		}

		/* Get custom tag attribute "dim-foreground-color" */
		if ((value = get_tag_attribute(attr, "dim-foreground-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				/* vte_terminal_set_color_dim removed in VTE 2.91 */
			}
		}

		/* Get custom tag attribute "cursor-background-color" */
		if ((value = get_tag_attribute(attr, "cursor-background-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				vte_terminal_set_color_cursor(VTE_TERMINAL(widget), &color);
			}
		}

		/* Get custom tag attribute "highlight-background-color" */
		if ((value = get_tag_attribute(attr, "highlight-background-color"))) {
			/* Parse the RGB value to create the necessary GdkColor.
			 * This function doesn't like trailing whitespace so it
			 * needs to be stripped first with g_strstrip() */ 
			if (gdk_rgba_parse(&color, g_strstrip(value))) {
				GDG_DEBUG("valid colour found");
				vte_terminal_set_color_highlight(VTE_TERMINAL(widget), &color);
			}
		}
	}

	/* Set width and height if both supplied */
	if (width != -1 && height != -1)
		vte_terminal_set_size(VTE_TERMINAL(widget), width, height);

	/* And off we go... */
	widget_terminal_fork_command(widget, attr);
#else
	/* If libvte support is missing then create a label instead */
	widget = gtk_label_new(VTE_WARNING);
#endif

	GDG_DEBUG("Exiting.");

	return widget;
}

/***********************************************************************
 * Fork Command                                                        *
 ***********************************************************************/

void widget_terminal_fork_command(GtkWidget *widget, tag_attr *attr)
{
#if HAVE_VTE
	static gchar     *argv0 = "/bin/sh";
	gchar            *argv[128], *envv[128];
	gchar             tagattribute[256];
	gchar            *value;
	gchar            *working_directory = NULL;
	gint              count;
	/* spawn_async doesn't return pid synchronously */
#endif

	GDG_DEBUG("Entering.");

#if HAVE_VTE
	/* Initialise strings */
	for (count = 0; count < 128; count++) {
		argv[count] = NULL;
		envv[count] = NULL;
	}
	argv[0] = argv0;	/* Set a default command otherwise it segfaults */

	if (attr) {
		/* The "current-directory-uri" can only be set when we fork a
		 * command (there's no function for it) so we set it now */
		if ((value = get_tag_attribute(attr, "current-directory-uri")))
			working_directory = value;

		/* Get custom tag attributes argv and envv */
		for (count = 0; count < 128; count++) {
			sprintf(tagattribute, "argv%i", count);
			if ((value = get_tag_attribute(attr, tagattribute)))
				argv[count] = value;
			GDG_DEBUG("%s=%s", tagattribute, value);
			sprintf(tagattribute, "envv%i", count);
			if ((value = get_tag_attribute(attr, tagattribute)))
				envv[count] = value;
			GDG_DEBUG("%s=%s", tagattribute, value);
		}
	}

	GDG_DEBUG("working_directory=%s", working_directory);
	GDG_DEBUG("argv=%p *argv=%s argv[0]=%s argv[1]=%s",
		argv, *argv, argv[0], argv[1]);
	GDG_DEBUG("envv=%p *envv=%s envv[0]=%s envv[1]=%s",
		envv, *envv, envv[0], envv[1]);

	vte_terminal_spawn_async(VTE_TERMINAL(widget),
		VTE_PTY_DEFAULT,
		working_directory,
		argv,
		envv,
		G_SPAWN_SEARCH_PATH,
		NULL,
		NULL,
		NULL,
		-1,
		NULL,
		NULL,
		NULL);

	/* PID is no longer synchronously available with spawn_async */
	g_object_set_data(G_OBJECT(widget), "_pid", GINT_TO_POINTER(0));

#endif

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_terminal_envvar_all_construct(variable *var)
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

gchar *widget_terminal_envvar_construct(GtkWidget *widget)
{
#if HAVE_VTE
	gchar             envvar[32];
#endif
	gchar            *string;

	GDG_DEBUG("Entering.");

#if HAVE_VTE
	sprintf(envvar, "%i", GPOINTER_TO_INT(g_object_get_data(G_OBJECT(widget), "_pid")));
	string = g_strdup(envvar);
#else
	string = g_strdup("");
#endif

	GDG_DEBUG("Exiting.");

	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_terminal_fileselect(
	variable *var, const char *name, const char *value)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/
void widget_terminal_refresh(variable *var)
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
			widget_terminal_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			if (!initialised) {
				/* Check for file-monitor and create if requested */
				widget_file_monitor_try_create(var, act + 5);
			}
			widget_terminal_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_terminal_input_by_items(var);

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

		/* Connect signals */
#if HAVE_VTE
		g_signal_connect(G_OBJECT(var->Widget), "child-exited",
			G_CALLBACK(on_any_widget_child_exited_event), (gpointer)var->Attributes);
#endif

	}

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_terminal_removeselected(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_terminal_save(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): Save not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_terminal_input_by_command(variable *var, char *command)
{
#if HAVE_VTE
	FILE             *infile;
	GString          *text = g_string_sized_new(512);
	gchar             line[512];
#endif

	GDG_DEBUG("Entering.");

	GDG_DEBUG("command: '%s'", command);

#if HAVE_VTE
	/* Opening pipe for reading... */
	if ((infile = widget_opencommand(command))) {
		/* Read the file one line at a time */
		while (fgets(line, 512, infile)) {
			g_string_append(text, line);
		}

		vte_terminal_feed_child(VTE_TERMINAL(var->Widget), text->str, text->len);

		g_string_free(text, TRUE);
		/* Close the file */
		widget_closecommand(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			command);
	}
#endif

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_terminal_input_by_file(variable *var, char *filename)
{
#if HAVE_VTE
	FILE             *infile;
	GString          *text = g_string_sized_new(512);
	gchar             line[512];
#endif

	GDG_DEBUG("Entering.");

#if HAVE_VTE
	if ((infile = fopen(filename, "r"))) {
		/* Read the file one line at a time */
		while (fgets(line, 512, infile)) {
			g_string_append(text, line);
		}

		vte_terminal_feed_child(VTE_TERMINAL(var->Widget), text->str, text->len);

		g_string_free(text, TRUE);
		/* Close the file */
		fclose(infile);
	} else {
		fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n", __func__,
			filename);
	}
#endif

	GDG_DEBUG("Exiting.");
}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_terminal_input_by_items(variable *var)
{

	GDG_DEBUG("Entering.");

	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

	GDG_DEBUG("Exiting.");
}
