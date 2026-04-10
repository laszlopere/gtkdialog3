/*
 * widget_menuitem.c: 
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
#include "widget_menuitem.h"


#include "gdg_debug.h"
/* Local function prototypes, located at file bottom */
static void widget_menuitem_input_by_command(variable *var, char *command);
static void widget_menuitem_input_by_file(variable *var, char *filename);
static void widget_menuitem_input_by_items(variable *var);

/* Notes:
 * The following widgets are maintained here:
 * 
 * menu - a GtkMenu attached to a GtkMenuItem
 * menuitem  - a GtkMenuItem, GtkCheckMenuItem, GtkRadioMenuItem or GtkImageMenuItem
 * menuitemseparator - a GtkSeparatorMenuItem
 * 
 * Apart from GtkMenu which is the menu shell, the rest are all
 * descendants of GtkMenuItem and simply variations of the same thing.
 */

/***********************************************************************
 * Clear                                                               *
 ***********************************************************************/

void widget_menuitem_clear(variable *var)
{


	fprintf(stderr, "%s(): Clear not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Create                                                              *
 ***********************************************************************/

GtkWidget *widget_menu_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	GtkAccelGroup    *accel_group;
	GtkWidget        *menu;
	GtkWidget        *menuitems;
	GtkWidget        *widget;
	gint              n;
	stackelement      s;


	/* Create the menu shell */
	menu = gtk_menu_new();

	/* Thunor: Each menu needs an accelerator group which requires adding
	 * to the window, but because everything is being done in reverse i.e.
	 * the window is created last, the accel-groups have to be temporarily
	 * stored within a list for adding later when the window is created */
	accel_group = gtk_accel_group_new();
	gtk_menu_set_accel_group(GTK_MENU(menu), accel_group);
	accel_groups = g_list_append(accel_groups, accel_group);

	GDG_DEBUG("Appending accel_group=%p to GList", accel_group);

	/* Pop the widgets that the menu shell will contain and add them */
	s = pop();
	for (n = 0; n < s.nwidgets; ++n) {
		menuitems = s.widgets[n];
		gtk_menu_shell_append(GTK_MENU_SHELL(menu), menuitems);
	}

	attributeset_set_if_unset(Attr, ATTR_LABEL, "menu");

	/* Thunor: A menu widget is in fact a menuitem widget with a submenu
	 * so it'll be created just like any other menuitem widget. It's
	 * possible to create image, checkbox or radiobutton menu widgets but
	 * their usefulness is questionable. In fact creating a menu widget
	 * closes any open radiobutton group so that makes that pointless */
	widget = widget_menuitem_create(Attr, attr, WIDGET_MENU);
	gtk_menu_item_set_submenu(GTK_MENU_ITEM(widget), menu);

	/* This widget has one or more children which require registering */
	widget_visibility_list_add(menu, attr);


	return widget;
}

GtkWidget *widget_menuitem_create(
	AttributeSet *Attr, tag_attr *attr, gint Type)
{
	#define           TYPE_MENUITEM 0
	#define           TYPE_MENUITEM_IMAGE_STOCK 1
	#define           TYPE_MENUITEM_IMAGE_ICON 2
	#define           TYPE_MENUITEM_IMAGE_FILE 3
	#define           TYPE_MENUITEM_CHECK 4
	#define           TYPE_MENUITEM_RADIO 5
	#define           TYPE_MENUITEM_SEPARATOR 6
	GList            *element;
	GtkWidget        *widget;
	gchar             accel_path[64];
	gchar            *active = NULL;
	gchar            *icon_name, *image_name;
	gchar            *label, *stock_id;
	gchar            *value;
	gint              is_active;
	gint              menuitemtype = TYPE_MENUITEM;
	guint             accel_key = 0, accel_mods = 0, custom_accel = 0;


	/* We need to decode exactly what it is the user is trying to create
	 * and then make the right widget.
	 * 
	 * Originally as I couldn't use "stock", "icon" and "image" (image
	 * is a GTK+ property) I decided to make the meaningful names of
	 * "image-stock", "image-icon" and "image-file", but then I found that
	 * "stock[_id]" and "icon[_name]" were already being used within the
	 * tree widget (I missed that) so I'll document the latter but accept
	 * everything below (I'll have to now as they're likely being used) */
	if (Type == WIDGET_MENUITEMSEPARATOR) {
		menuitemtype = TYPE_MENUITEM_SEPARATOR;
	} else if (attr &&
		(stock_id = get_tag_attribute(attr, "label")) &&
		((value = get_tag_attribute(attr, "use-stock")) &&
		((strcasecmp(value, "true") == 0) ||
		(strcasecmp(value, "yes") == 0) || (atoi(value) == 1)))) {
		menuitemtype = TYPE_MENUITEM_IMAGE_STOCK;
	} else if (attr &&
		((stock_id = get_tag_attribute(attr, "stock")) ||
		(stock_id = get_tag_attribute(attr, "stock-id")) ||
		(stock_id = get_tag_attribute(attr, "image-stock")))) {	/* I don't want to keep this temp temp */
		menuitemtype = TYPE_MENUITEM_IMAGE_STOCK;
	} else if (attr &&
		((icon_name = get_tag_attribute(attr, "icon")) ||
		(icon_name = get_tag_attribute(attr, "icon-name")) ||
		(icon_name = get_tag_attribute(attr, "image-icon")))) {	/* I don't want to keep this temp temp */
		menuitemtype = TYPE_MENUITEM_IMAGE_ICON;
	} else if (attr &&
		((image_name = get_tag_attribute(attr, "image-name")) ||
		(image_name = get_tag_attribute(attr, "image-file")))) {	/* I don't want to keep this temp temp */
		menuitemtype = TYPE_MENUITEM_IMAGE_FILE;
	} else if (attr &&
		(active = get_tag_attribute(attr, "checkbox"))) {
		menuitemtype = TYPE_MENUITEM_CHECK;
	} else if (attr &&
		(active = get_tag_attribute(attr, "radiobutton"))) {
		menuitemtype = TYPE_MENUITEM_RADIO;
	} else {
		menuitemtype = TYPE_MENUITEM;
	}

	/* Read declared directives */
	/* Only separator menuitems don't support this */
	if (menuitemtype != TYPE_MENUITEM_SEPARATOR) {
		/* Set a default label */
		attributeset_set_if_unset(Attr, ATTR_LABEL, "menuitem");
		label = attributeset_get_first(&element, Attr, ATTR_LABEL);
	} else {
		if (attributeset_is_avail(Attr, ATTR_LABEL)) {
			fprintf(stderr, "%s(): <label> not implemented for this widget.\n",
				__func__);
		}
	}
	/* Only image menuitems from theme or file support this */
	if (attributeset_is_avail(Attr, ATTR_HEIGHT)) {
		if (menuitemtype != TYPE_MENUITEM_IMAGE_ICON &&
			menuitemtype != TYPE_MENUITEM_IMAGE_FILE) {
			fprintf(stderr, "%s(): <height> not implemented for this widget.\n",
				__func__);
		}
	}
	/* Only image menuitems from theme or file support this */
	if (attributeset_is_avail(Attr, ATTR_WIDTH)) {
		if (menuitemtype != TYPE_MENUITEM_IMAGE_ICON &&
			menuitemtype != TYPE_MENUITEM_IMAGE_FILE) {
			fprintf(stderr, "%s(): <width> not implemented for this widget.\n",
				__func__);
		}
	}

	/* Thunor: We can add an accelerator for this menuitem if both
	 * "accel-key" and "accel-mods" are valid custom tag attributes.
	 * Note that because these widgets are created and pushed when the
	 * end tags are detected, everything gets done in reverse! So here
	 * the menuitems are created with possibly an accelerator, then
	 * when the menu end tag is detected the menu and accelerator group
	 * are created and finally the menuitems are appended to the menu */

	/* Only separator menuitems don't support this */
	if (menuitemtype != TYPE_MENUITEM_SEPARATOR) {
		if (attr) {
			if ((value = get_tag_attribute(attr, "accel-key"))) {
				/* Read accel-key as a decimal integer or hex value */
				if (strncasecmp(value, "0x", 2) == 0) {
					sscanf(value, "%x", &accel_key);
				} else {
					sscanf(value, "%u", &accel_key);
				}
				if ((value = get_tag_attribute(attr, "accel-mods"))) {
					/* Read accel-mods as a decimal integer or hex value */
					if (strncasecmp(value, "0x", 2) == 0) {
						sscanf(value, "%x", &accel_mods);
					} else {
						sscanf(value, "%u", &accel_mods);
					}
					/* Create a random accel-path (yeah, this is fine) */
					sprintf(accel_path, "<%i>/%i", rand(), rand());
					custom_accel = TRUE;
					GDG_DEBUG("accel-key=%u", accel_key);
					GDG_DEBUG("accel-mods=%u", accel_mods);
					GDG_DEBUG("accel-path=%s", accel_path);
				}
			}
		}
	}

	/* Create the menuitem */
	switch (menuitemtype) {
		case TYPE_MENUITEM_SEPARATOR:
			widget = gtk_separator_menu_item_new();
			break;
		case TYPE_MENUITEM_IMAGE_STOCK: {
			/* Map GTK2 stock IDs to freedesktop named icons.
			 * Use the <label> if provided, otherwise derive from stock_id */
			const gchar *use_icon = NULL;
			const gchar *use_label = label;
			gchar *derived_label = NULL;
			GtkWidget *box, *image, *accel_lbl;

			/* Map common stock IDs to named icons */
			if (g_str_has_prefix(stock_id, "gtk-")) {
				use_icon = stock_id;
				/* If label is the default "menuitem", derive from stock_id
				 * e.g. "gtk-quit" -> "Quit", "gtk-save-as" -> "Save As" */
				if (strcmp(label, "menuitem") == 0) {
					gchar *p;
					derived_label = g_strdup(stock_id + 4);
					/* Capitalize first letter */
					if (derived_label[0])
						derived_label[0] = g_ascii_toupper(derived_label[0]);
					/* Replace hyphens with spaces and capitalize following letters */
					for (p = derived_label; *p; p++) {
						if (*p == '-') {
							*p = ' ';
							if (*(p + 1))
								*(p + 1) = g_ascii_toupper(*(p + 1));
						}
					}
					use_label = derived_label;
				}
			}
			widget = gtk_menu_item_new();
			box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
			if (use_icon) {
				image = gtk_image_new_from_icon_name(use_icon,
					GTK_ICON_SIZE_MENU);
				gtk_box_pack_start(GTK_BOX(box), image, FALSE, FALSE, 0);
			}
			accel_lbl = gtk_accel_label_new(use_label);
			gtk_label_set_use_underline(GTK_LABEL(accel_lbl), TRUE);
			gtk_label_set_xalign(GTK_LABEL(accel_lbl), 0.0);
			gtk_accel_label_set_accel_widget(GTK_ACCEL_LABEL(accel_lbl), widget);
			gtk_box_pack_start(GTK_BOX(box), accel_lbl, TRUE, TRUE, 0);
			gtk_container_add(GTK_CONTAINER(widget), box);
			gtk_widget_show_all(box);
			g_free(derived_label);
			break;
		}
		case TYPE_MENUITEM_IMAGE_ICON: {
			/* Create a menu item with a named theme icon */
			GtkWidget *box, *image, *accel_lbl;

			widget = gtk_menu_item_new();
			box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
			image = gtk_image_new_from_icon_name(icon_name,
				GTK_ICON_SIZE_MENU);
			gtk_box_pack_start(GTK_BOX(box), image, FALSE, FALSE, 0);
			accel_lbl = gtk_accel_label_new(label);
			gtk_label_set_use_underline(GTK_LABEL(accel_lbl), TRUE);
			gtk_label_set_xalign(GTK_LABEL(accel_lbl), 0.0);
			gtk_accel_label_set_accel_widget(GTK_ACCEL_LABEL(accel_lbl), widget);
			gtk_box_pack_start(GTK_BOX(box), accel_lbl, TRUE, TRUE, 0);
			gtk_container_add(GTK_CONTAINER(widget), box);
			gtk_widget_show_all(box);
			break;
		}
		case TYPE_MENUITEM_IMAGE_FILE: {
			/* Create a menu item with an icon from a file */
			GtkWidget *box, *image, *accel_lbl;

			widget = gtk_menu_item_new();
			box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
			image = gtk_image_new_from_file(image_name);
			gtk_box_pack_start(GTK_BOX(box), image, FALSE, FALSE, 0);
			accel_lbl = gtk_accel_label_new(label);
			gtk_label_set_use_underline(GTK_LABEL(accel_lbl), TRUE);
			gtk_label_set_xalign(GTK_LABEL(accel_lbl), 0.0);
			gtk_accel_label_set_accel_widget(GTK_ACCEL_LABEL(accel_lbl), widget);
			gtk_box_pack_start(GTK_BOX(box), accel_lbl, TRUE, TRUE, 0);
			gtk_container_add(GTK_CONTAINER(widget), box);
			gtk_widget_show_all(box);
			break;
		}
		case TYPE_MENUITEM_CHECK:
			/* Create the GtkCheckMenuItem */
			widget = gtk_check_menu_item_new_with_mnemonic(label);
			/* Get the active state */
			if ((strcasecmp(active, "true") == 0) ||
				(strcasecmp(active, "yes") == 0) || (atoi(active) == 1)) {
				is_active = 1;
			} else {
				is_active = 0;
			}
			/* Set the active state */
			gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(widget), is_active);
			break;
		case TYPE_MENUITEM_RADIO:
			/* Create the GtkRadioMenuItem */
			if (lastradiowidget == NULL) {
				widget = gtk_radio_menu_item_new_with_mnemonic(NULL, label);
				lastradiowidget = widget;
			} else {
				widget = gtk_radio_menu_item_new_with_mnemonic_from_widget(
					GTK_RADIO_MENU_ITEM(lastradiowidget), label);
			}
			/* Get the active state */
			if ((strcasecmp(active, "true") == 0) ||
				(strcasecmp(active, "yes") == 0) || (atoi(active) == 1)) {
				is_active = 1;
			} else {
				is_active = 0;
			}
			/* Set the active state (yeah, it uses the same base class function) */
			gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(widget), is_active);
			break;
		case TYPE_MENUITEM:
		default:
			/* Create the GtkMenuItem */
			widget = gtk_menu_item_new_with_mnemonic(label);
			break;
	}

	/* Are we setting an accelerator? */
	if (custom_accel) {
		/* Register and set the accelerator path on the menuitem */
		gtk_accel_map_add_entry(accel_path, accel_key, accel_mods);
		gtk_menu_item_set_accel_path(GTK_MENU_ITEM(widget), accel_path);
	}


	return widget;
}

/***********************************************************************
 * Environment Variable All Construct                                  *
 ***********************************************************************/

gchar *widget_menuitem_envvar_all_construct(variable *var)
{
	gchar            *string = g_strdup("");


	/* This function should not be connected-up by default */

	GDG_DEBUG("Hello.");


	return string;
}

/***********************************************************************
 * Environment Variable Construct                                      *
 ***********************************************************************/

gchar *widget_menuitem_envvar_construct(GtkWidget *widget)
{
	gchar            *string;


	/* Only checkbox and radiobutton menuitems support this */
	if (GTK_IS_CHECK_MENU_ITEM(widget)) {
		if (gtk_check_menu_item_get_active(GTK_CHECK_MENU_ITEM(widget))) {
			string = g_strdup("true");
		} else {
			string = g_strdup("false");
		}
	} else {
		string = g_strdup("");
	}


	return string;
}

/***********************************************************************
 * Fileselect                                                          *
 ***********************************************************************/

void widget_menuitem_fileselect(
	variable *var, const char *name, const char *value)
{


	fprintf(stderr, "%s(): Fileselect not implemented for this widget.\n", __func__);

}

/***********************************************************************
 * Refresh                                                             *
 ***********************************************************************/

void widget_menuitem_refresh(variable *var)
{
	GList            *element;
	gchar            *act;
	gchar            *value, *image_name;
	gint              initialised = FALSE;


	/* Get initialised state of widget */
	if (g_object_get_data(G_OBJECT(var->Widget), "_initialised") != NULL)
		initialised = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(var->Widget), "_initialised"));

	/* tag_attr="value"... */
	/* GtkImageMenuItem is deprecated in GTK3. Image menuitems are now
	 * plain GtkMenuItems, so image refresh is no longer supported.
	 * We still create file monitors for the image-name/image-file
	 * tag attributes if present. */
	if (var->widget_tag_attr &&
		((image_name = get_tag_attribute(var->widget_tag_attr, "image-name")) ||
		(image_name = get_tag_attribute(var->widget_tag_attr, "image-file")))) {
		if (!initialised) {
			/* Check for file-monitor and create if requested */
			widget_file_monitor_try_create(var, image_name);
		}
	}

	/* The <input> tag... */
	act = attributeset_get_first(&element, var->Attributes, ATTR_INPUT);
	while (act) {
		if (input_is_shell_command(act))
			widget_menuitem_input_by_command(var, act + 8);
		/* input file stock = "File:", input file = "File:/path/to/file" */
		if (strncasecmp(act, "file:", 5) == 0 && strlen(act) > 5) {
			/* Only checkbox and radiobutton menuitems support this */
			if (GTK_IS_CHECK_MENU_ITEM(var->Widget)) {
				if (!initialised) {
					/* Check for file-monitor and create if requested */
					widget_file_monitor_try_create(var, act + 5);
				}
			}
			widget_menuitem_input_by_file(var, act + 5);
		}
		act = attributeset_get_next(&element, var->Attributes, ATTR_INPUT);
	}

	/* The <item> tags... */
	if (attributeset_is_avail(var->Attributes, ATTR_ITEM))
		widget_menuitem_input_by_items(var);

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
		/* The GTK "sensitive" property (if present) will be set later after
		 * widget realization, but this doesn't have any effect until after
		 * the menu has been opened by the user which results in accelerators
		 * being live up until that point. I don't know why that is -- it 
		 * looks as though GTK is initialising the menus on first opening as
		 * they render much quicker on subsequent openings -- but it can be
		 * dealt with by applying the property right here right now.
		 * Note that I'm applying this after any sensitive directive which
		 * would be the normal sequence of things.
		 * 
		 * [UPDATE]
		 * Menuitems are realized when the menu is opened which could be a
		 * problem since then tag attributes that are GTK properties will
		 * sit there waiting to be applied at some later time. Something is
		 * going to have to be done about the on_any_widget_realized method
		 * of setting tag attributes because it will be affecting other widgets
		 * such as the notebook including all of the widgets within that!
		 * When that's dealt with I can remove the following code temp temp */
		if (var->widget_tag_attr &&
			(value = get_tag_attribute(var->widget_tag_attr, "sensitive")) &&
			((strcasecmp(value, "false") == 0) ||
			(strcasecmp(value, "no") == 0) || (atoi(value) == 0))) {
			gtk_widget_set_sensitive(var->Widget, FALSE);
		}

		/* Connect signals */
		/* Only checkbox and radiobutton menuitems support this */
		if (GTK_IS_CHECK_MENU_ITEM(var->Widget)) {
			g_signal_connect(G_OBJECT(var->Widget), "toggled",
				G_CALLBACK(on_any_widget_toggled_event), (gpointer)var->Attributes);
		}
		/* Only separator menuitems don't support this */
		if (!GTK_IS_SEPARATOR_MENU_ITEM(var->Widget)) {
			g_signal_connect(G_OBJECT(var->Widget), "activate",
				G_CALLBACK(on_any_widget_activate_event), (gpointer)var->Attributes);
		}

	}

}

/***********************************************************************
 * Removeselected                                                      *
 ***********************************************************************/

void widget_menuitem_removeselected(variable *var)
{


	fprintf(stderr, "%s(): Removeselected not implemented for this widget.\n",
		__func__);

}

/***********************************************************************
 * Save                                                                *
 ***********************************************************************/

void widget_menuitem_save(variable *var)
{
	FILE             *outfile;
	GList            *element;
	gchar            *act;
	gchar            *filename = NULL;
	gint              is_active;


	/* Only checkbox and radiobutton menuitems support this */
	if (GTK_IS_CHECK_MENU_ITEM(var->Widget)) {

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

				is_active = gtk_check_menu_item_get_active(
					GTK_CHECK_MENU_ITEM(var->Widget));
				if (is_active) fprintf(outfile, "%s", "true");
				else fprintf(outfile, "%s", "false");

				fclose(outfile);
			} else {
				fprintf(stderr, "%s(): Couldn't open '%s' for writing.\n",
					__func__, filename);
			}
		} else {
			fprintf(stderr, "%s(): No <output file> directive found.\n",
				__func__);
		}

	} else {
		fprintf(stderr, "%s(): Save not implemented for this widget.\n",
			__func__);
	}

}

/***********************************************************************
 * Input by Command                                                    *
 ***********************************************************************/

static void widget_menuitem_input_by_command(variable *var, char *command)
{
	FILE             *infile;
	gchar             line[512];
	gint              count, is_active;


	/* Only checkbox and radiobutton menuitems support this */
	if (GTK_IS_CHECK_MENU_ITEM(var->Widget)) {

		/* Opening pipe for reading... */
		if ((infile = widget_opencommand(command))) {
			/* Just one line */
			if ((fgets(line, 512, infile))) {
				/* Enforce end of string in case of max chars read */
				line[512 - 1] = 0;
				/* Remove the trailing [CR]LFs */
				for (count = strlen(line) - 1; count >= 0; count--)
					if (line[count] == 13 || line[count] == 10) line[count] = 0;

				if ((strcasecmp(line, "true") == 0) ||
					(strcasecmp(line, "yes") == 0) || (atoi(line) == 1)) {
					is_active = 1;
				} else {
					is_active = 0;
				}
				gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(
					var->Widget), is_active);

			}
			/* Close the file */
			widget_closecommand(infile);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n",
				__func__, command);
		}

	} else {
		fprintf(stderr, "%s(): <input> not implemented for this widget.\n",
			__func__);
	}

}

/***********************************************************************
 * Input by File                                                       *
 ***********************************************************************/

static void widget_menuitem_input_by_file(variable *var, char *filename)
{
	FILE             *infile;
	gchar             line[512];
	gint              count, is_active;


	/* Only checkbox and radiobutton menuitems support this */
	if (GTK_IS_CHECK_MENU_ITEM(var->Widget)) {

		if ((infile = fopen(filename, "r"))) {
			/* Just one line */
			if ((fgets(line, 512, infile))) {
				/* Enforce end of string in case of max chars read */
				line[512 - 1] = 0;
				/* Remove the trailing [CR]LFs */
				for (count = strlen(line) - 1; count >= 0; count--)
					if (line[count] == 13 || line[count] == 10) line[count] = 0;

				if ((strcasecmp(line, "true") == 0) ||
					(strcasecmp(line, "yes") == 0) || (atoi(line) == 1)) {
					is_active = 1;
				} else {
					is_active = 0;
				}
				gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(
					var->Widget), is_active);

			}
			/* Close the file */
			fclose(infile);
		} else {
			fprintf(stderr, "%s(): Couldn't open '%s' for reading.\n",
				__func__, filename);
		}

	} else {
		fprintf(stderr, "%s(): <input file> not implemented for this widget.\n",
			__func__);
	}

}

/***********************************************************************
 * Input by Items                                                      *
 ***********************************************************************/

static void widget_menuitem_input_by_items(variable *var)
{


	fprintf(stderr, "%s(): <item> not implemented for this widget.\n", __func__);

}
