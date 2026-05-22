/*
 * widget_webview.c:
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
#include "widget_webview.h"
#include "attributes.h"
#include "automaton.h"
#include "widgets.h"
#include "signals.h"
#include "tag_attributes.h"
#include "gdg_debug.h"
#if HAVE_WEBKIT
#include <webkit2/webkit2.h>
#endif

#define WEBKIT_WARNING "The webview (WebKitWebView) widget requires \
a version of gtkdialog built with libwebkit2gtk."

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_webview_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkWidget        *widget;
#if HAVE_WEBKIT
	GList            *element;
	gchar            *value;
#endif


#if HAVE_WEBKIT
	widget = webkit_web_view_new();

	/* WebKitWebView has no intrinsic size — set a minimum and
	 * request expansion so it fills its parent container */
	gtk_widget_set_size_request(widget, 200, 200);
	gtk_widget_set_hexpand(widget, TRUE);
	gtk_widget_set_vexpand(widget, TRUE);

	/* Load default URL if specified */
	if (attributeset_is_avail(Attr, ATTR_DEFAULT)) {
		value = attributeset_get_first(&element, Attr, ATTR_DEFAULT);
		if (value && value[0]) {
			webkit_web_view_load_uri(WEBKIT_WEB_VIEW(widget), value);
		}
	}

	/* Apply tag attributes as GObject properties */
	if (attr)
		widget_set_tag_attributes(widget, attr);
#else
	widget = gtk_label_new(WEBKIT_WARNING);
#endif

	return widget;
}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_webview_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gchar             line[512];
	FILE             *infile;


#if HAVE_WEBKIT
	/* The <input> tag: execute command and load its output as HTML */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act)) {
			if ((infile = widget_opencommand(act + 8))) {
				GString *html = g_string_sized_new(4096);
				while (fgets(line, 512, infile)) {
					g_string_append(html, line);
				}
				webkit_web_view_load_html(
					WEBKIT_WEB_VIEW(var->Widget), html->str, NULL);
				g_string_free(html, TRUE);
				widget_closecommand(infile);
			}
		} else if (strncasecmp(act, "file:", 5) == 0) {
			/* <input file>path</input> — read file content:
			 * if it starts with http:// or https://, navigate to URL;
			 * otherwise load content as HTML */
			gchar *path = act + 5;
			while (*path == ' ') path++;
			if ((infile = fopen(path, "r"))) {
				GString *content = g_string_sized_new(4096);
				while (fgets(line, 512, infile)) {
					g_string_append(content, line);
				}
				fclose(infile);
				g_strstrip(content->str);
				if (strncasecmp(content->str, "http://", 7) == 0 ||
				    strncasecmp(content->str, "https://", 8) == 0) {
					webkit_web_view_load_uri(
						WEBKIT_WEB_VIEW(var->Widget), content->str);
				} else if (content->str[0] == '/') {
					/* Absolute file path — convert to file:// URI */
					gchar *uri = g_filename_to_uri(content->str, NULL, NULL);
					if (uri) {
						webkit_web_view_load_uri(
							WEBKIT_WEB_VIEW(var->Widget), uri);
						g_free(uri);
					}
				} else if (content->len > 0) {
					webkit_web_view_load_html(
						WEBKIT_WEB_VIEW(var->Widget), content->str, NULL);
				}
				g_string_free(content, TRUE);
			}
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}
#endif

}

/***********************************************************************
 * Environment variable construct                                      *
 ***********************************************************************/

gchar *widget_webview_envvar_construct(GtkWidget *widget)
{
#if HAVE_WEBKIT
	const gchar *uri = webkit_web_view_get_uri(WEBKIT_WEB_VIEW(widget));
	return g_strdup(uri ? uri : "");
#else
	return g_strdup("");
#endif
}
