/*
 * actions.c:
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

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <gtk/gtk.h>

#ifndef G_OS_WIN32
#include <sys/types.h>
#include <sys/wait.h>
#include <regex.h>
#include <unistd.h>
#endif

#include "gtkdialog.h"
#include "widgets.h"
#include "actions.h"
#include "attributes.h"
#include "variables.h"
#include "tag_attributes.h"
#include "widget_sourceview.h"
#if HAVE_WEBKIT
#include <webkit2/webkit2.h>
#endif

extern gchar *option_include_file;

/***********************************************************************
 * Run a command using the user's SHELL instead of /bin/sh.            *
 * This preserves bash exported functions (export -f) which system()   *
 * loses because it always invokes /bin/sh.                            *
 ***********************************************************************/

static int run_shell_command(const char *command)
{
	const char *shell = getenv("SHELL");
	if (shell == NULL)
		shell = "/bin/sh";

	pid_t pid = fork();
	if (pid == -1)
		return -1;
	if (pid == 0) {
		execl(shell, shell, "-c", command, (char *)NULL);
		_exit(127);
	}
	int status;
	if (waitpid(pid, &status, 0) == -1)
		return -1;
	return status;
}

/* Local function prototypes */
void action_closewindow(GtkWidget *widget, char *string);
void action_launchwindow(GtkWidget *widget, char *string);
void action_exitprogram(GtkWidget *widget, char *string);
void action_refreshwidget(GtkWidget *widget, char *string);
void action_savewidget(GtkWidget *widget, char *string);
void action_fileselect(GtkWidget *widget, char *string);
void action_fileselection_made(GtkWidget *w, actioncommand *ac);
void action_fileselection_destroy(GtkWidget *w, actioncommand *ac);
void action_clearwidget(GtkWidget *widget, char *string);
void action_removeselected(GtkWidget *widget, char *string);
int action_append(GtkWidget *widget, char *string);
void action_enable(GtkWidget *widget, char *string);
void action_disable(GtkWidget *widget, char *string);
void action_show(GtkWidget *widget, char *string);
void action_hide(GtkWidget *widget, char *string);
void action_activate(GtkWidget *widget, char *string);
void action_grabfocus(GtkWidget *widget, char *string);
void action_presentwindow(GtkWidget *widget, char *string);
void action_set(GtkWidget *widget, char *string);
void action_shellcommand(GtkWidget *widget, char *string);

/***********************************************************************
 * Action closewindow                                                  *
 ***********************************************************************/
/* Thunor: This function will close an existing window that contains a
 * variable that matches string although ideally the application developer
 * would have supplied a unique name in the window widget's variable
 * directive.
 */

void action_closewindow(GtkWidget *widget, char *string)
{
	GtkWidget        *window;
	variable         *existing;

	g_assert(GTK_IS_WIDGET(widget));

#ifdef DEBUG
	fprintf(stderr, "%s(): Entering.\n", __func__);
#endif

	/**
	 * Patriot Oct 2009: zigbert has been dreaming for this to be fixed.
	 * Issue: closewindow command closes THE window its called from.
	 * Fixed: Workaround applied to point to the correct window.
	 **/

	existing = variables_get_by_name(string);

#ifdef DEBUG
	fprintf(stderr, "%s(): string=%s existing=%p\n",
		__func__, string, existing);
	fflush(stderr);
#endif

	if (existing != NULL && existing->Widget != NULL) {

#ifdef DEBUG
		fprintf(stderr, "%s(): Name=%s Type=%i\n",
			__func__, existing->Name, existing->Type);
		fflush(stderr);
#endif

		//Redundant: parent = gtk_widget_get_toplevel(existing->Widget);
		window = gtk_widget_get_ancestor(existing->Widget, GTK_TYPE_WINDOW);
		//Redundant: variables_drop_by_parent(NULL, parent);
		variables_drop_by_window_id(NULL, existing->window_id);
		gtk_widget_destroy(window);

#ifdef DEBUG
		fprintf(stderr, "%s(): variables_count_widgets()=%i\n", __func__,
			variables_count_widgets());
#endif

		/* If we are closing the last window then we can exit gtkdialog */
		if (variables_count_widgets() == 0) {

			if (option_output_format != OUTPUT_FORMAT_BASH)
				print_variables_with_exit("closewindow");
			else
				printf("EXIT=\"closewindow\"\n");

#ifdef DEBUG
			fprintf(stderr, "%s(): Calling gtkdialog_exit(EXIT_SUCCESS)\n", __func__);
#endif

			fflush(stdout);
			gtkdialog_exit(EXIT_SUCCESS);
			return;

		}
	}

#ifdef DEBUG
	fprintf(stderr, "%s(): Exiting.\n", __func__);
#endif
}

/***********************************************************************
 * Action launchwindow                                                 *
 ***********************************************************************/
/* Thunor: This function will launch a new window, the source of which
 * should be contained within an existing exported shell variable.
 * 
 * The parameter to this function is the shell variable name which MUST
 * match any widget's variable within the program, although it would be
 * better practice to use a dedicated window widget's variable for this.
 * 
 * Currently the variable name matching requirement remains unenforced
 * and will require to remain so as there will be broken applications
 * out there using fixes and workarounds. The best that can be hoped for
 * is a warning message once the new window has been loaded. 
 */

void action_launchwindow(GtkWidget *widget, char *string)
{
	GtkWidget        *window;
	variable         *existing;

#ifdef DEBUG
	fprintf(stderr, "%s(): string=%s\n", __func__, string);
#endif

	/* Check if a variable already exists with the same name as that
	 * passed as the parameter to launch to establish if the window
	 * has already been launched (it's not foolproof but it works) */
	existing = variables_get_by_name(string);

	if (existing != NULL && existing->Widget != NULL) {

		/* The window has already been launched so just give it the focus */
#ifdef DEBUG
		fprintf(stderr, "%s(): existing=%p Name=%s\n", __func__,
			existing, existing->Name);
#endif

		window = gtk_widget_get_ancestor(existing->Widget, GTK_TYPE_WINDOW);
		gtk_window_present(GTK_WINDOW(window));

	} else {

		/* Parse the window definition if we haven't seen it before */
		if (!program_block_exists(string)) {
			get_program_from_variable(string);
			variables_export_all();
			gtkdialog_lexer_reset();
			gtkdialog_parse();
		}

		/* Build the window from the saved instruction block */
		build_window(string);

	}
}

/***********************************************************************
 * Action exit                                                         *
 ***********************************************************************/

void action_exitprogram(GtkWidget *widget, char *string)
{
	gchar *exit_value;

	if (string[0] == '=')
		exit_value = string;  /* raw "=value" form */
	else
		exit_value = string;

	if (option_output_format != OUTPUT_FORMAT_BASH) {
		print_variables_with_exit(exit_value);
	} else {
		print_variables(NULL);
		if (string[0] == '=')
			/* Thunor: An interesting undocumented feature temp temp */
			printf("EXIT%s", string);
		else
			printf("EXIT=\"%s\"\n", string);
	}

#ifdef DEBUG
	fprintf(stderr, "%s(): Calling gtkdialog_exit(EXIT_SUCCESS)\n", __func__);
#endif

	fflush(stdout);
	gtkdialog_exit(EXIT_SUCCESS);
}

/***********************************************************************
 * Action refresh                                                      *
 ***********************************************************************/

void action_refreshwidget(GtkWidget *widget, char *string)
{
	variables_refresh(string);
}

/***********************************************************************
 * Action save                                                         *
 ***********************************************************************/

void action_savewidget(GtkWidget *widget, char *string)
{
	variables_save(string);
}

/***********************************************************************
 * Action fileselect                                                   *
 ***********************************************************************/
/* This function will create and open a fileselection dialog and
 * connect it to the action_fileselection_made function to take
 * the selected file name */

#if GTK_CHECK_VERSION(2,4,0)
void action_fileselect(GtkWidget *widget, char *string)
{
	list_t                 *mime_types = NULL;
	list_t                 *patterns = NULL;
	variable               *var = NULL;
	GList                  *element;
	GtkFileChooserAction    action = GTK_FILE_CHOOSER_ACTION_OPEN;
	GtkFileFilter          *filter;
	GtkWidget              *chooser;
	gchar                  *filename = NULL;
	gchar                  *title = "Gtkdialog";
	gchar                  *value;
	gint                    count;
	gint                    response;

#ifdef DEBUG
	fprintf(stderr, "%s(): string='%s'\n", __func__, string);
#endif

	if ((var = variables_get_by_name(string))) {

		/* Set the title of the chooser dialog to the label directive
		 * of the target widget if available (this was the original
		 * behaviour that although used in the 16.00-fileselect example
		 * it is undocumented so possibly few people have realised this) */
		if (attributeset_is_avail(var->Attributes, ATTR_LABEL)) {
			title = attributeset_get_first(&element, var->Attributes, ATTR_LABEL);
#ifdef DEBUG
			fprintf(stderr, "%s(): title='%s' from label directive\n",
				__func__, title);
#endif
		}

		if (var->widget_tag_attr) {
			/* Set title if present */
			if ((value = get_tag_attribute(var->widget_tag_attr, "fs-title"))) {
				title = value;
#ifdef DEBUG
				fprintf(stderr, "%s(): title='%s' from tag attribute\n",
					__func__, title);
#endif
			}
			/* Set file chooser action if present */
			if ((value = get_tag_attribute(var->widget_tag_attr, "fs-action")) ||
				(value = get_tag_attribute(var->widget_tag_attr, "accept"))) {	/* Deprecated */				
				if ((strcasecmp(value, "file") == 0) ||
					(strcasecmp(value, "filename") == 0)) {			/* Deprecated */
					action = GTK_FILE_CHOOSER_ACTION_OPEN;
				} else if ((strcasecmp(value, "newfile") == 0) ||
					(strcasecmp(value, "savefilename") == 0)) {		/* Deprecated */
					action = GTK_FILE_CHOOSER_ACTION_SAVE;
				} else if ((strcasecmp(value, "folder") == 0) ||
					(strcasecmp(value, "directory") == 0)) {		/* Deprecated */
					action = GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER;
				} else if ((strcasecmp(value, "newfolder") == 0) ||
					(strcasecmp(value, "newdirectory") == 0)) {		/* Deprecated */
					action = GTK_FILE_CHOOSER_ACTION_CREATE_FOLDER;
				}
#ifdef DEBUG
				fprintf(stderr, "%s(): action=%i\n", __func__, action);
#endif
			}
		}

		/* Create the file chooser dialog */
		chooser = gtk_file_chooser_dialog_new(title, NULL, action,
			"_OK", GTK_RESPONSE_OK,
			"_Cancel", GTK_RESPONSE_CANCEL, NULL);

		/* Set current folder if present */
		if (var->widget_tag_attr &&
			((value = get_tag_attribute(var->widget_tag_attr, "fs-folder")))) {
			gtk_file_chooser_set_current_folder(GTK_FILE_CHOOSER(chooser), value);
#ifdef DEBUG
			fprintf(stderr, "%s(): current folder='%s'\n", __func__, value);
#endif
		}

		/* Add file filters */
		if (var->widget_tag_attr) {
			/* Filters of type pattern */
			if ((value = get_tag_attribute(var->widget_tag_attr, "fs-filters"))) {
				patterns = linecutter(g_strdup(value), '|');
				for (count = 0; count < patterns->n_lines; count++) {
					filter = gtk_file_filter_new();
					gtk_file_filter_set_name(filter, patterns->line[count]);
					gtk_file_filter_add_pattern(filter, patterns->line[count]);
					gtk_file_chooser_add_filter(GTK_FILE_CHOOSER(chooser), filter);
#ifdef DEBUG
					fprintf(stderr, "%s(): patterns->line[count]='%s'\n",
						__func__, patterns->line[count]);
#endif
				}
			}
			/* Filters of type mime */
			if ((value = get_tag_attribute(var->widget_tag_attr, "fs-filters-mime"))) {
				mime_types = linecutter(g_strdup(value), '|');
				for (count = 0; count < mime_types->n_lines; count++) {
					filter = gtk_file_filter_new();
					gtk_file_filter_set_name(filter, mime_types->line[count]);
					gtk_file_filter_add_mime_type(filter, mime_types->line[count]);
					gtk_file_chooser_add_filter(GTK_FILE_CHOOSER(chooser), filter);
#ifdef DEBUG
					fprintf(stderr, "%s(): mime_types->line[count]='%s'\n",
						__func__, mime_types->line[count]);
#endif
				}
			}
		}

		/* Add an "All files" "*" filter which will become the
		 * default if no user filters were added above */
		filter = gtk_file_filter_new();
		gtk_file_filter_set_name(filter, "All files");
		gtk_file_filter_add_pattern(filter, "*");
		gtk_file_chooser_add_filter(GTK_FILE_CHOOSER(chooser), filter);

		/* Run the file chooser dialog and get the response.
		 * Note that accept="newdirectory" (fs-action="newfolder")
		 * currently crashes the file chooser dialog if nothing is
		 * selected or created which is mentioned in the example */
		response = gtk_dialog_run(GTK_DIALOG(chooser));

#ifdef DEBUG
		fprintf(stderr, "%s(): response=%i\n", __func__, response);
#endif

		/* If the user pressed the OK button we set the target widget */
		switch (response) {
			case GTK_RESPONSE_CANCEL:
				/* Nothing to do */
				break;
			case GTK_RESPONSE_OK:
				filename = gtk_file_chooser_get_filename(
					GTK_FILE_CHOOSER(chooser));
#ifdef DEBUG
				fprintf(stderr, "%s(): filename=%s\n", __func__, filename);
#endif
				if (filename) {
					variables_set_value(string, filename);
					g_free(filename);
				}
				break;
		}

		/* Free linecutter memory */
		if (patterns) list_t_free(patterns);
		if (mime_types) list_t_free(mime_types);

		/* Destroy the file chooser dialog */
		gtk_widget_destroy(chooser);
	}

}

#else

void action_fileselect(GtkWidget *widget, char *string)
{
	actioncommand *ac;
	/*
	 ** We create a new actioncommand.
	 */
	ac = g_malloc(sizeof(actioncommand));
	ac->source_widget = gtk_file_selection_new("gtkwindow");
	ac->destination_name = string;
	gtk_widget_show(ac->source_widget);

	/*
	 ** We connect the OK button in fileselection dialog
	 */
	g_signal_connect(G_OBJECT
			 (GTK_FILE_SELECTION(ac->source_widget)->
			  ok_button), "clicked",
			 G_CALLBACK(action_fileselection_made),
			 (gpointer) ac);
	/*
	 ** We connect the Cancel button in fileselection dialog
	 */
	g_signal_connect(G_OBJECT
			 (GTK_FILE_SELECTION(ac->source_widget)->
			  cancel_button), "clicked",
			 G_CALLBACK(action_fileselection_destroy),
			 (gpointer) ac);
}
#endif

/***********************************************************************
 *                                                                     *
 ***********************************************************************/
/* This function is called when the user presses the OK button in
 * a fileselection dialog */

/* GtkFileSelection was removed in GTK3 - these functions are unused
 * when GTK_CHECK_VERSION(2,4,0) is true (which it always is in GTK3) */
void action_fileselection_made(GtkWidget *w, actioncommand * ac)
{
	gtk_widget_destroy(ac->source_widget);
	free(ac);
}

void action_fileselection_destroy(GtkWidget *w, actioncommand *ac)
{
	gtk_widget_destroy(ac->source_widget);
	free(ac);
}

/***********************************************************************
 * Action clear                                                        *
 ***********************************************************************/
/* This action removes all elements from a widget */

void action_clearwidget(GtkWidget *widget, char *string)
{
	variables_clear(string);
}

/***********************************************************************
 * Action removeselected                                               *
 ***********************************************************************/
/* This action removes a selected element from a widget */

void action_removeselected(GtkWidget *widget, char *string)
{
	remove_selected_variable(string);
}

/***********************************************************************
 * Action cut/copy/paste/selectall                                     *
 ***********************************************************************/

void action_cut(GtkWidget *widget, char *string)
{
	variables_cut(string);
}

void action_copy(GtkWidget *widget, char *string)
{
	variables_copy(string);
}

void action_paste(GtkWidget *widget, char *string)
{
	variables_paste(string);
}

void action_selectall(GtkWidget *widget, char *string)
{
	variables_selectall(string);
}

/***********************************************************************
 *                                                                     *
 ***********************************************************************/

int action_append(GtkWidget *widget, char *string)
{
#ifndef G_OS_WIN32
	regex_t twoparams;
	regmatch_t matched[3];
	char *regular = "[ ]*([A-Za-z_]+),[ ]*([A-Za-z_]+)";
	char *from, *to;
	int length_from, length_to;
	
	g_assert(string != NULL);
	
	if (regcomp(&twoparams, regular, REG_EXTENDED) != 0)
		g_error("%s(): Internal error: %m", __func__);

	if (regexec(&twoparams, string, 3, matched, 0) != 0) {
		yywarning("Insert action needs two parameters.");
		return FALSE;
	}
	
	length_from = matched[1].rm_eo - matched[1].rm_so;
	from = g_malloc(length_from + 1);

	length_to = matched[2].rm_eo - matched[2].rm_so;
	to = g_malloc(length_to + 1);

	strncpy(from, string, length_from);
	from[length_from] = '\0';

	strncpy(to, string + matched[2].rm_so, length_to);
	to[length_to] = '\0';

	return append_fromto_variable(from, to);
#else
	g_warning("%s(): Unimplemented.", __func__);
#endif
}

/***********************************************************************
 * Action enable                                                       *
 ***********************************************************************/

void action_enable(GtkWidget *widget, char *string)
{
	variables_enable(string);
}

/***********************************************************************
 * Action disable                                                      *
 ***********************************************************************/

void action_disable(GtkWidget *widget, char *string)
{
	variables_disable(string);
}

/***********************************************************************
 * Action show                                                         *
 ***********************************************************************/

void action_show(GtkWidget *widget, char *string)
{
	variables_show(string);
}

/***********************************************************************
 * Action hide                                                         *
 ***********************************************************************/

void action_hide(GtkWidget *widget, char *string)
{
	variables_hide(string);
}

/***********************************************************************
 * Action activate                                                     *
 ***********************************************************************/

void action_activate(GtkWidget *widget, char *string)
{
	variables_activate(string);
}

/***********************************************************************
 * Action grabfocus                                                    *
 ***********************************************************************/

void action_grabfocus(GtkWidget *widget, char *string)
{
	variables_grabfocus(string);
}

/***********************************************************************
 * Action presentwindow                                                *
 ***********************************************************************/

void action_presentwindow(GtkWidget *widget, char *string)
{
	variables_presentwindow(string);
}

/***********************************************************************
 * Action command                                                      *
 ***********************************************************************/
/* This fuction will export variables and run a shell command */

void action_shellcommand(GtkWidget *widget, char *string)
{
	char *command;

	variables_export_all();

	if (option_include_file == NULL) {

		run_shell_command(string);

	} else {

		/* Debian 01_bashism patch: use dot rather than source.
		command = g_strdup_printf("source %s; %s", */
		command = g_strdup_printf(". %s; %s",
				option_include_file, string);
		run_shell_command(command);
		g_free(command);

	}

}

/***********************************************************************
 * Action set                                                          *
 ***********************************************************************/
/* Parses "widget.property=value" and sets the property on the widget
 * looked up by variable name.  Custom (non-GTK) properties are handled
 * first for specific widget types; everything else falls through to
 * try_set_property which uses GObject's property system. */

void action_set(GtkWidget *widget, char *string)
{
	variable         *var;
	namevalue         nv;
	char             *dot;
	char             *eq;
	char             *widget_name;

	/* Find the first dot (widget.property separator) */
	dot = strchr(string, '.');
	if (dot == NULL) {
		fprintf(stderr, "%s(): Missing '.' in set argument: %s\n",
			__func__, string);
		return;
	}

	/* Find the first '=' after the dot (property=value separator) */
	eq = strchr(dot + 1, '=');
	if (eq == NULL) {
		fprintf(stderr, "%s(): Missing '=' in set argument: %s\n",
			__func__, string);
		return;
	}

	/* Extract widget name, property name, and value */
	widget_name = g_strndup(string, dot - string);
	nv.name = g_strndup(dot + 1, eq - dot - 1);
	nv.value = eq + 1;

	var = variables_get_by_name(widget_name);
	if (var == NULL || var->Widget == NULL) {
		fprintf(stderr, "%s(): Widget '%s' not found.\n",
			__func__, widget_name);
		g_free(widget_name);
		g_free(nv.name);
		return;
	}

	/* Handle custom properties for specific widget types */
#if HAVE_WEBKIT
	if (WEBKIT_IS_WEB_VIEW(var->Widget) &&
	    strcasecmp(nv.name, "uri") == 0) {
		webkit_web_view_load_uri(WEBKIT_WEB_VIEW(var->Widget), nv.value);
		g_free(widget_name);
		g_free(nv.name);
		return;
	}
#endif
	if (var->Type == WIDGET_SOURCEVIEW) {
		if (strcasecmp(nv.name, "file") == 0) {
			widget_sourceview_load_file(var, nv.value);
			g_free(widget_name);
			g_free(nv.name);
			return;
		}
		if (strcasecmp(nv.name, "language") == 0) {
			widget_sourceview_set_language(var, nv.value);
			g_free(widget_name);
			g_free(nv.name);
			return;
		}
	}

	/* Fall through to GObject property system */
	try_set_property(var->Widget, &nv);

	g_free(widget_name);
	g_free(nv.name);
}

/***********************************************************************
 * Execute Action                                                      *
 ***********************************************************************/
/* On exit: returns 0 if action function is unknown
 *                  1 if action function is valid
 *                  2 if break function detected */

int execute_action(GtkWidget *widget, const char *command, const char *type)
{
	gchar            *command_prefix;
	gchar            *command_string;
	gint              retval = 1;
	CommandType       t;

	/* Thunor: I've re-engineered my signal blocking mechanism.
	 * All signal callbacks end up here, so if the global flag is
	 * true then the action functions simply don't get executed */
	if (!function_signals_block) {

		if (type == NULL || g_utf8_strlen(type, -1) == 0) {
			command_get_prefix(command, &command_prefix, &command_string);
		} else {
			command_prefix = g_strdup(type);
			command_string = g_strdup(command);
		}

#ifdef DEBUG
		fprintf(stderr, "%s(): command: '%s' type: '%s'.\n", __func__,
			command_string, command_prefix);
#endif

		t = command_prefix_get_type(command_prefix);
		switch (t) {
			case CommandShellCommand:
				action_shellcommand(widget, command_string);
				break;

			case CommandExit:
				action_exitprogram(widget, command_string);
				break;

			case CommandCloseWindow:
				action_closewindow(widget, command_string);
				break;

			case CommandLaunch:
				action_launchwindow(widget, command_string);
				break;

			case CommandEnable:
				action_enable(widget, command_string);
				break;

			case CommandDisable:
				action_disable(widget, command_string);
				break;

			case CommandShow:
				action_show(widget, command_string);
				break;

			case CommandHide:
				action_hide(widget, command_string);
				break;

			case CommandActivate:
				action_activate(widget, command_string);
				break;

			case CommandGrabFocus:
				action_grabfocus(widget, command_string);
				break;

			case CommandPresentWindow:
				action_presentwindow(widget, command_string);
				break;

			case CommandRefresh:
				variables_export_all();
				action_refreshwidget(widget, command_string);
				break;

			case CommandSave:
				action_savewidget(widget, command_string);
				break;

			case CommandFileSelect:
				action_fileselect(widget, command_string);
				break;

			case CommandClear:
				action_clearwidget(widget, command_string);
				break;

			case CommandRemoveSelected:
				action_removeselected(widget, command_string);
				break;

			case CommandBreak:
				retval = 2;
				break;

			/* Thunor: It looks like work on insert and append was started
			 * but there's not much code so I wouldn't expect it to work
			 * (I haven't tried it since it's not documented). Note that
			 * both are calling action_append() which is strange */
			case CommandInsert:
				action_append(widget, command_string);
				break;

			case CommandAppend:
				action_append(widget, command_string);
				break;

			case CommandCut:
				action_cut(widget, command_string);
				break;

			case CommandCopy:
				action_copy(widget, command_string);
				break;

			case CommandPaste:
				action_paste(widget, command_string);
				break;

			case CommandSelectAll:
				action_selectall(widget, command_string);
				break;

			case CommandSet:
				action_set(widget, command_string);
				break;

			default:
				g_error("%s(): Unknown action type", __func__);
				retval = 0;
				break;
		}
			
		g_free(command_prefix);
		g_free(command_string);
	}

	return retval;
}
