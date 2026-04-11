/*
 * builder_support.c: GtkBuilder UI file support for Gtkdialog.
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

#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <gtk/gtk.h>
#include "builder_support.h"
#include "widgets.h"
#include "actions.h"
#include "signals.h"

/*************************************************************************
 * Static declarations:                                                  *
 *                                                                       *
 *                                                                       *
 *************************************************************************/
typedef struct _gtkdialog_signal {
	gchar     *name;
	GCallback callback;
} gtkdialog_signal;

/* function prototypes */
gint widget_get_type_from_pointer(GtkWidget *widget);

/*
** Signal handler callbacks.
*/

static void
on_any_button_clicked(
		GtkButton *widget,
		gchar     *full_command)
{
	gchar *prefix, *command;

	g_return_if_fail(full_command != NULL);
#ifdef DEBUG
	g_message("%s(%p, '%s')", __func__, widget, full_command);
#endif
	command_get_prefix(full_command, &prefix, &command);
	execute_action(GTK_WIDGET(widget), command, prefix);
	g_free(command);
	g_free(prefix);
}


static void
on_any_entry_almost_any(GtkEntry *widget,
		gchar     *full_command)
{
	gchar *prefix, *command;

	g_return_if_fail(full_command != NULL);
#ifdef DEBUG
	g_message("%s(%p, '%s')", __func__, widget, full_command);
#endif
	command_get_prefix(full_command, &prefix, &command);
	execute_action(GTK_WIDGET(widget), command, prefix);
	g_free(command);
	g_free(prefix);
}


static void
on_any_entry_delete_from_cursor(
		GtkEntry *entry,
		GtkDeleteType *arg1,
		gint arg2,
		gpointer user_data)
{
	on_any_entry_almost_any(entry, user_data);
}

static void
on_any_entry_insert_at_cursor(
		GtkEntry *entry,
		gchar *arg1,
		gpointer user_data)
{
	on_any_entry_almost_any(entry, user_data);
}

static void
on_any_entry_move_cursor(
		GtkEntry *entry,
		GtkMovementStep *arg1,
		gint arg2,
		gboolean arg3,
		gpointer user_data)
{
	on_any_entry_almost_any(entry, user_data);
}

static void
on_any_entry_populate_popup(
		GtkEntry *entry,
		GtkMenu *arg1,
		gpointer user_data)
{
	on_any_entry_almost_any(entry, user_data);
}

static void
on_any_combobox_changed(
		GtkComboBox *widget,
		gchar     *full_command)
{
	gchar *prefix, *command;

	g_return_if_fail(full_command != NULL);
#ifdef DEBUG
	g_message("%s(%p, '%s')", __func__, widget, full_command);
#endif
	command_get_prefix(full_command, &prefix, &command);
	execute_action(GTK_WIDGET(widget), command, prefix);
	g_free(command);
	g_free(prefix);
}

static void
on_any_scale_value_changed(
		GtkScale *widget,
		gchar     *full_command)
{
	gchar *prefix, *command;

	g_return_if_fail(full_command != NULL);
#ifdef DEBUG
	g_message("%s(%p, '%s')", __func__, widget, full_command);
#endif
	command_get_prefix(full_command, &prefix, &command);
	execute_action(GTK_WIDGET(widget), command, prefix);
	g_free(command);
	g_free(prefix);
}

static void
on_any_widget_almost_any(
		GtkWidget *widget,
		gchar *full_command)
{
	gchar *prefix, *command;

	g_return_if_fail(full_command != NULL);
#ifdef DEBUG
	g_message("%s(%p, '%s')", __func__, widget, full_command);
#endif
	command_get_prefix(full_command, &prefix, &command);
	execute_action(widget, command, prefix);
	g_free(command);
	g_free(prefix);
}

static gboolean
on_any_widget_almost_any_gdk_event(
		 GtkWidget *widget,
		 GdkEvent *event,
		 gpointer user_data)
{
	on_any_widget_almost_any(widget, user_data);
	return FALSE;
}

/*
** Signal handler connectors for each widget types we support.
*/
static gboolean
find_and_connect_handler(
		GtkWidget *widget,
		gtkdialog_signal *signals,
		const gchar *signal_name,
		const gchar *handler_name)
{
	gint n;

	for (n = 0; signals[n].name != NULL; ++n) {
		if (g_ascii_strcasecmp(signals[n].name, signal_name) == 0) {
			g_signal_connect(G_OBJECT(widget),
					signal_name,
					signals[n].callback,
					g_strdup(handler_name));
			return TRUE;
		}
	}

	return FALSE;
}


static gboolean
gtk_toggle_button_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	if (g_ascii_strcasecmp(signal_name, "toggled") == 0) {
		g_signal_connect(object,
				signal_name,
				G_CALLBACK(on_any_button_clicked),
				g_strdup(handler_name));
		return TRUE;
	}
	return FALSE;
}

static gboolean
gtk_button_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	gint n;
	gchar *signal_names[] = {
		"activate", "clicked", "enter", "leave", "pressed",
		"released", NULL
	};

	for (n = 0; signal_names[n] != NULL; ++n) {
		if (g_ascii_strcasecmp(signal_name, signal_names[n]) == 0) {
			g_signal_connect(object,
					signal_names[n],
					G_CALLBACK(on_any_button_clicked),
					g_strdup(handler_name));
			return TRUE;
		}
	}
	return FALSE;
}

static gboolean
gtk_entry_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	gtkdialog_signal entry_signals[] = {
		{ "activate",           (GCallback)on_any_entry_almost_any },
		{ "backspace",          (GCallback)on_any_entry_almost_any },
		{ "copy-clipboard",     (GCallback)on_any_entry_almost_any },
		{ "cut-clipboard",      (GCallback)on_any_entry_almost_any },
		{ "paste-clipboard",    (GCallback)on_any_entry_almost_any },
		{ "toggle-overwrite",   (GCallback)on_any_entry_almost_any },
		{ "delete-from-cursor", (GCallback)on_any_entry_delete_from_cursor },
		{ "insert-at-cursor",   (GCallback)on_any_entry_insert_at_cursor },
		{ "move-cursor",        (GCallback)on_any_entry_move_cursor },
		{ "populate-popup",     (GCallback)on_any_entry_populate_popup },
		{ NULL,                 (GCallback)NULL }
	};

	return find_and_connect_handler(GTK_WIDGET(object),
			entry_signals,
			signal_name,
			handler_name);
}

static gboolean
gtk_combobox_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	if (g_ascii_strcasecmp(signal_name, "changed") == 0) {
		g_signal_connect(object,
				signal_name,
				G_CALLBACK(on_any_combobox_changed),
				g_strdup(handler_name));
		return TRUE;
	}
	return FALSE;
}

static gboolean
gtk_scale_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	if ((g_ascii_strcasecmp(signal_name, "value_changed") == 0) ||
		(g_ascii_strcasecmp(signal_name, "value-changed") == 0)) {
		g_signal_connect(object,
				signal_name,
				G_CALLBACK(on_any_scale_value_changed),
				g_strdup(handler_name));
		return TRUE;
	}
	return FALSE;
}

static gboolean
gtk_widget_signal_handler_connector(
		const gchar *handler_name,
		GObject *object,
		const gchar *signal_name,
		GObject *connect_object,
		GConnectFlags flags,
		gpointer user_data)
{
	variable *var;
	gtkdialog_signal widget_signals[] = {
		{ "accel-closures-changed",    (GCallback)on_any_widget_almost_any },
		{ "composited-changed",        (GCallback)on_any_widget_almost_any },
		{ "grab-focus",                (GCallback)on_any_widget_almost_any },
		{ "hide",                      (GCallback)on_any_widget_almost_any },
		{ "map",                       (GCallback)on_any_widget_almost_any },
		{ "popup-menu",                (GCallback)on_any_widget_almost_any },
		{ "show",                      (GCallback)on_any_widget_almost_any },
		{ "unmap",                     (GCallback)on_any_widget_almost_any },
		{ "unrealize",                 (GCallback)on_any_widget_almost_any },
		{ "button-press-event",        (GCallback)on_any_widget_almost_any_gdk_event },
		{ "configure-event",           (GCallback)on_any_widget_almost_any_gdk_event },
		{ "delete-event",              (GCallback)on_any_widget_almost_any_gdk_event },
		{ "destroy-event",             (GCallback)on_any_widget_almost_any_gdk_event },
		{ "enter-notify-event",        (GCallback)on_any_widget_almost_any_gdk_event },
		{ "event",                     (GCallback)on_any_widget_almost_any_gdk_event },
		{ "event-after",               (GCallback)on_any_widget_almost_any_gdk_event },
		{ "focus-in-event",            (GCallback)on_any_widget_almost_any_gdk_event },
		{ "focus-out-event",           (GCallback)on_any_widget_almost_any_gdk_event },
		{ "grab-broken-event",         (GCallback)on_any_widget_almost_any_gdk_event },
		{ "key-press-event",           (GCallback)on_any_widget_almost_any_gdk_event },
		{ "key-release-event",         (GCallback)on_any_widget_almost_any_gdk_event },
		{ "leave-notify-event",        (GCallback)on_any_widget_almost_any_gdk_event },
		{ "map-event",                 (GCallback)on_any_widget_almost_any_gdk_event },
		{ "motion-notify-event",       (GCallback)on_any_widget_almost_any_gdk_event },
		{ "property-notify-event",     (GCallback)on_any_widget_almost_any_gdk_event },
		{ "scroll-event",              (GCallback)on_any_widget_almost_any_gdk_event },
		{ "selection-clear-event",     (GCallback)on_any_widget_almost_any_gdk_event },
		{ "selection-notify-event",    (GCallback)on_any_widget_almost_any_gdk_event },
		{ "selection-request-event",   (GCallback)on_any_widget_almost_any_gdk_event },
		{ "unmap-event",               (GCallback)on_any_widget_almost_any_gdk_event },
		{ "visibility-notify-event",   (GCallback)on_any_widget_almost_any_gdk_event },
		{ NULL,                        (GCallback)NULL }
	};
	/*
	 * The best thing to do is to register this callback as the input
	 * attribute of the given variable. We can't connect the signal to a
	 * signal handler, for it is already created.
	 */
	if (g_ascii_strcasecmp(signal_name, "realize") == 0) {
		var = find_variable_by_widget(GTK_WIDGET(object));
		g_return_val_if_fail(var != NULL, FALSE);
		attributeset_insert(var->Attributes, ATTR_INPUT, handler_name);
		return TRUE;
	}

	return find_and_connect_handler(GTK_WIDGET(object),
			widget_signals,
			signal_name,
			handler_name);
}


/*
** Main signal handler connector called by gtk_builder_connect_signals_full().
*/
static void
signal_handler_connector(
		GtkBuilder  *builder,
		GObject     *object,
		const gchar *signal_name,
		const gchar *handler_name,
		GObject     *connect_object,
		GConnectFlags flags,
		gpointer     user_data)
{
#ifdef DEBUG
	g_message("%s(): start", __func__);
	g_message("      signal_name: '%s'", signal_name);
	g_message("     handler_name: '%s'", handler_name);
#endif
	if (GTK_IS_ENTRY(object))
		if (gtk_entry_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_TOGGLE_BUTTON(object))
		if (gtk_toggle_button_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_BUTTON(object))
		if (gtk_button_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_TOOL_BUTTON(object))
		if (gtk_button_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_COMBO_BOX(object))
		if (gtk_combobox_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_SCALE(object))
		if (gtk_scale_signal_handler_connector(handler_name,
					object,
					signal_name,
					connect_object,
					flags,
					user_data))
			return;

	if (GTK_IS_WIDGET(object))
		if (gtk_widget_signal_handler_connector(handler_name,
				object,
				signal_name,
				connect_object,
				flags,
				user_data))
			return;

	g_warning("%s(): Unhandled signal: '%s'", __func__, signal_name);

}


static void
register_widgets(GtkBuilder *builder)
{
	GSList       *object_list, *li;
	GtkWidget    *widget;
	AttributeSet *Attr;
	gint          type;
	const gchar  *name;

	object_list = gtk_builder_get_objects(builder);
	for (li = object_list; li != NULL; li = li->next) {
		if (!GTK_IS_WIDGET(li->data))
			continue;
		widget = GTK_WIDGET(li->data);
		/*
		 * GtkBuilder stores the id in the buildable name, not the
		 * widget name.  Copy it so the rest of gtkdialog (which uses
		 * gtk_widget_get_name) sees the builder id.
		 */
		name = gtk_buildable_get_name(GTK_BUILDABLE(widget));
		if (name != NULL)
			gtk_widget_set_name(widget, name);
		Attr = attributeset_new();
		attributeset_set_if_unset(Attr, ATTR_VARIABLE, name);
		type = widget_get_type_from_pointer(widget);
		variables_new_with_widget(Attr, NULL, widget, type);
#ifdef DEBUG
		g_message("%s(): widget name: %s, type: %d",
				__func__, name, type);
#endif
	}
	g_slist_free(object_list);
}

static void
refresh_widgets(GtkBuilder *builder)
{
	GSList       *object_list, *li;
	const gchar  *name;

	object_list = gtk_builder_get_objects(builder);
	for (li = object_list; li != NULL; li = li->next) {
		if (!GTK_IS_WIDGET(li->data))
			continue;
		name = gtk_buildable_get_name(GTK_BUILDABLE(li->data));
		variables_refresh(name);
	}

	g_slist_free(object_list);
}

/*
 * Map a GtkWidget pointer to the internal gtkdialog widget type.
 *
 * These MUST be in an order that returns widgets lower down the
 * hierarchy before those higher up.
 */
gint widget_get_type_from_pointer(GtkWidget *widget)
{
	gint retval = 0;

/* GtkRadioButton */
	if (GTK_IS_RADIO_BUTTON(widget))
		retval = WIDGET_RADIOBUTTON;
/* GtkCheckButton */
	else if (GTK_IS_CHECK_BUTTON(widget))
		retval = WIDGET_CHECKBOX;
/* GtkColorButton */
	else if (GTK_IS_COLOR_BUTTON(widget))
		retval = WIDGET_COLORBUTTON;
/* GtkToggleButton */
	else if (GTK_IS_TOGGLE_BUTTON(widget))
		retval = WIDGET_TOGGLEBUTTON;
/* GtkFontButton */
	else if (GTK_IS_FONT_BUTTON(widget))
		retval = WIDGET_FONTBUTTON;
/* GtkButton */
	else if (GTK_IS_BUTTON(widget))
		retval = WIDGET_BUTTON;
/* GtkComboBox with entry */
	else if (GTK_IS_COMBO_BOX(widget) && gtk_combo_box_get_has_entry(GTK_COMBO_BOX(widget)))
		retval = WIDGET_COMBOBOXENTRY;
/* GtkComboBox (also matches GtkComboBoxText) */
	else if (GTK_IS_COMBO_BOX(widget))
		retval = WIDGET_COMBOBOXTEXT;
/* GtkEventBox */
	else if (GTK_IS_EVENT_BOX(widget))
		retval = WIDGET_EVENTBOX;
/* GtkExpander */
	else if (GTK_IS_EXPANDER(widget))
		retval = WIDGET_EXPANDER;
/* GtkFrame */
	else if (GTK_IS_FRAME(widget))
		retval = WIDGET_FRAME;
/* GtkSeparatorMenuItem */
	else if (GTK_IS_SEPARATOR_MENU_ITEM(widget))
		retval = WIDGET_MENUITEMSEPARATOR;
/* GtkMenuItem */
	else if (GTK_IS_MENU_ITEM(widget))
		retval = WIDGET_MENUITEM;
/* GtkScrolledWindow */
	else if (GTK_IS_SCROLLED_WINDOW(widget))
		retval = WIDGET_SCROLLEDW;
/* GtkWindow */
	else if (GTK_IS_WINDOW(widget))
		retval = WIDGET_WINDOW;
/* GtkStatusbar */
	else if (GTK_IS_STATUSBAR(widget))
		retval = WIDGET_STATUSBAR;
/* GtkBox: check orientation to distinguish hbox/vbox */
	else if (GTK_IS_BOX(widget)) {
		if (GTK_IS_FILE_CHOOSER_WIDGET(widget))
			retval = WIDGET_CHOOSER;
		else if (gtk_orientable_get_orientation(GTK_ORIENTABLE(widget)) == GTK_ORIENTATION_HORIZONTAL)
			retval = WIDGET_HBOX;
		else
			retval = WIDGET_VBOX;
	}
/* GtkMenuBar */
	else if (GTK_IS_MENU_BAR(widget))
		retval = WIDGET_MENUBAR;
/* GtkMenu */
	else if (GTK_IS_MENU(widget))
		retval = WIDGET_MENU;
/* GtkNotebook */
	else if (GTK_IS_NOTEBOOK(widget))
		retval = WIDGET_NOTEBOOK;
/* GtkTextView */
	else if (GTK_IS_TEXT_VIEW(widget))
		retval = WIDGET_EDIT;
/* GtkTreeView */
	else if (GTK_IS_TREE_VIEW(widget))
		retval = WIDGET_TREE;
/* GtkSpinButton */
	else if (GTK_IS_SPIN_BUTTON(widget))
		retval = WIDGET_SPINBUTTON;
/* GtkEntry */
	else if (GTK_IS_ENTRY(widget))
		retval = WIDGET_ENTRY;
/* GtkImage */
	else if (GTK_IS_IMAGE(widget))
		retval = WIDGET_PIXMAP;
/* GtkLabel */
	else if (GTK_IS_LABEL(widget))
		retval = WIDGET_TEXT;
/* GtkProgressBar */
	else if (GTK_IS_PROGRESS_BAR(widget))
		retval = WIDGET_PROGRESSBAR;
/* GtkScale: check orientation to distinguish hscale/vscale */
	else if (GTK_IS_SCALE(widget)) {
		if (gtk_orientable_get_orientation(GTK_ORIENTABLE(widget)) == GTK_ORIENTATION_HORIZONTAL)
			retval = WIDGET_HSCALE;
		else
			retval = WIDGET_VSCALE;
	}
/* GtkSeparator: check orientation */
	else if (GTK_IS_SEPARATOR(widget)) {
		if (gtk_orientable_get_orientation(GTK_ORIENTABLE(widget)) == GTK_ORIENTATION_HORIZONTAL)
			retval = WIDGET_HSEPARATOR;
		else
			retval = WIDGET_VSEPARATOR;
	}
/* GtkWidget hasn't been accounted for */
	else
		retval = 0;

	return retval;
}

/*************************************************************************
 * Public functions:                                                     *
 *                                                                       *
 *                                                                       *
 *************************************************************************/
void
run_program_by_builder(
		const gchar *filename,
		const gchar *window_name)
{
	GtkBuilder *builder;
	GtkWidget  *main_window;
	GError     *error = NULL;

	builder = gtk_builder_new();
	if (!gtk_builder_add_from_file(builder, filename, &error))
		g_error("Failed to load UI file '%s': %s", filename,
				error->message);

	if (window_name != NULL)
		main_window = GTK_WIDGET(gtk_builder_get_object(builder, window_name));
	else
		main_window = GTK_WIDGET(gtk_builder_get_object(builder, "MAIN_WINDOW"));

	if (main_window == NULL)
		g_error("Can not find widget '%s' in file '%s'",
				window_name ? window_name : "MAIN_WINDOW",
				filename);
	/*
	 * Register all widgets from the UI file.
	 */
	register_widgets(builder);
	/*
	 * Connecting the signals.
	 */
	gtk_builder_connect_signals_full(builder,
			(GtkBuilderConnectFunc) signal_handler_connector,
			NULL);
	g_signal_connect(G_OBJECT(main_window), "delete-event",
			G_CALLBACK(window_delete_event_handler), NULL);

	refresh_widgets(builder);

	gtk_widget_show(main_window);
	gtk_main();

	g_object_unref(builder);
}
