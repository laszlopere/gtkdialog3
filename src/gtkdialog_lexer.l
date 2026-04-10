%{
/*
 * gtkdialog_lexer.l:
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

/*
**
** $Id: lexer.l,v 1.2 2004/11/20 20:01:25 root Exp root $
** $Log: lexer.l,v $
** Revision 1.2  2004/11/20 20:01:25  root
** - Log entries.
**
*/

#define YY_INPUT(buf,result,max_size) \
    { \
    int c = getnextchar(); \
    result = (c == EOF) ? YY_NULL : (buf[0] = c, 1); \
    }


#include <string.h>
#include <gtk/gtk.h>

#include "gtkdialog.h"
#include "attributes.h"
#include "gtkdialog_parser.h"

int getnextchar(void);
int gtkdialog_error(char *c);

extern int linenumber;
gchar *Token;
static int pending_close_token = 0;
static int current_close_token = 0;

/*
 * Strip backslash escapes from a string: \< becomes <, \\ becomes \, etc.
 * The caller must free the returned string with g_free().
 */
static gchar *strip_backslash_escapes(const gchar *s) {
	gchar *result = g_malloc(strlen(s) + 1);
	gchar *dst = result;
	while (*s) {
		if (*s == '\\' && s[1]) {
			s++;
		}
		*dst++ = *s++;
	}
	*dst = '\0';
	return result;
}

%}

	/**************************************************************
	 * Thunor: Uncomment this to debug.
	 **************************************************************
	* %option debug */

%option noinput

%x EMBEDDED
%x ST_TAG_ATTR ST_QUOTED_TAGATTR ST_SQUOTED_TAGATTR
%x ST_STRING ST_QUOTED_STRING ST_SQUOTED_STRING

%%

	#ifdef DEBUG
		g_message("%s(): Start", __func__);
	#endif

	/*
	 * Self-closing tag support: if a previous rule queued a
	 * closing token (from <widget/> or <widget attr="val"/>),
	 * return it now before scanning further input.
	 */
	if (pending_close_token) {
		int t = pending_close_token;
		pending_close_token = 0;
		Token = "self-closing tag end";
		return t;
	}

">"       				{ Token=">"; return(yytext[0]); 			}
<*>$[ \t\n]* 				{ Token="indent chars"; 				}

	/*
	 * Attributes.
	 */
<ST_TAG_ATTR>[-a-zA-Z0-9_]+ {
	#ifdef DEBUG 
	g_message(" -> TAG_ATTR_NAME: '%s'", yytext);
	#endif
	Token="tag attribute name";
	gtkdialog_lval.cval=strdup(yytext);
	return TAG_ATTR_NAME;
}


<ST_TAG_ATTR>= 				{
					  #ifdef DEBUG 
					  g_message(" -> spec char: '%s'", yytext);
					  #endif
					  Token="=";
					  return '=';
												}
<ST_TAG_ATTR>\/\> 			{
					  #ifdef DEBUG
					  g_message(" -> self-close: '%s'", yytext);
					  #endif
					  Token="/>";
					  pending_close_token = current_close_token;
					  BEGIN(0);
					  return '>';
												}

<ST_TAG_ATTR>\> 			{
					  #ifdef DEBUG
					  g_message(" -> spec char: '%s'", yytext);
					  #endif
					  Token=">";
					  BEGIN(0);
					  return '>';
												}

<ST_TAG_ATTR>\" 			{
					  Token = "double quote";
					  BEGIN(ST_QUOTED_TAGATTR);				}

<ST_QUOTED_TAGATTR>[^\\"]+		{
					  Token = "string";
					  yymore();						}

<ST_QUOTED_TAGATTR>("\\\"")		{
					  Token = "string";
					  yymore();						}

<ST_QUOTED_TAGATTR>\"			{
					  Token = yytext;
					  gtkdialog_lval.cval = g_strdup(yytext);
					  gtkdialog_lval.cval[strlen(gtkdialog_lval.cval) - 1] = '\0';
					  BEGIN(ST_TAG_ATTR);
					  return STRING;
					  							}

<ST_TAG_ATTR>\x27 			{
					  Token = "single quote";
					  BEGIN(ST_SQUOTED_TAGATTR);				}

<ST_SQUOTED_TAGATTR>[^\x27]+		{
					  Token = "string";
					  yymore();						}

<ST_SQUOTED_TAGATTR>\x27		{
					  Token = yytext;
					  gtkdialog_lval.cval = g_strdup(yytext);
					  gtkdialog_lval.cval[strlen(gtkdialog_lval.cval) - 1] = '\0';
					  BEGIN(ST_TAG_ATTR);
					  return STRING;
					  							}






	/*
	 * The elements of the embedded imperative language.
	 */
\<show\/\> { 
	Token="<show/>"; 
	return SHOW_WIDGETS;
}

\<command[ ]+assignment[ ]*=[ ]*\"  {
	Token="<command>";    
	BEGIN(EMBEDDED);
	return COMM;
}

\<if[ ]+condition[ ]*=[ ]*\"  {
	Token="<if>";    
	BEGIN(EMBEDDED);
	return IF;           
}

\<while[ ]+condition[ ]*=[ ]*\"  {
	Token="<while>";    
	BEGIN(EMBEDDED);
	return WHILE;
}

<EMBEDDED>[-+*/<>=:] {
	Token = "operator";
	return yytext[0];
}

<EMBEDDED>[a-zA-Z-]+ {
	Token = "variable";
	gtkdialog_lval.cval = g_strdup(yytext);
	return EMB_VARIABLE;
}

<EMBEDDED>[0-9,.]+ {
	Token = "number";
	gtkdialog_lval.cval = g_strdup(yytext);
	return EMB_NUMBER;
}

<EMBEDDED>\" { 
	BEGIN(0);
}

"</command>" { 
	Token="</if>"; 
	return ENDCOMM;
}

"</if>" { 
	Token="</if>"; 
	return ENDIF;
}

"</while>" { 
	Token="</while>"; 
	return EWHILE;
}


	/*
	 * The widget tags.
	 */
\<window\/\> {
	Token="<window/>";
	pending_close_token = EWINDOW;
	return(WINDOW);
}

\<window\> {
	Token="<window>";
	return(WINDOW);
}

\<window[ ]+ {
	Token="<window>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EWINDOW;
	return(PART_WINDOW);
}

\<\/window\> { 
	Token="</window>"; 
	return(EWINDOW);
}


\<notebook\/\> {
	Token="<notebook/>";
	pending_close_token = ENOTEBOOK;
	return(NOTEBOOK);
}

\<notebook\> {
	Token="<notebook>";
	return(NOTEBOOK);
}

\<notebook[ ]+ {
	Token="<notebook>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = ENOTEBOOK;
	return(PART_NOTEBOOK);
}

\<\/notebook\> { 
	Token="</notebook>"; 
	return(ENOTEBOOK);
}


\<vbox\/\> {
	Token="<vbox/>";
	pending_close_token = EVBOX;
	return(VBOX);
}

\<vbox\> {
	Token="<vbox>";
	return(VBOX);
}

\<vbox[ ]+ {
	Token="<vbox>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EVBOX;
	return(PART_VBOX);
}

\<\/vbox\> { 
	Token="</vbox>"; 
	return(EVBOX);
}


\<hbox\/\> {
	Token="<hbox/>";
	pending_close_token = EHBOX;
	return(HBOX);
}

\<hbox\> {
	Token="<hbox>";
	return(HBOX);
}

\<hbox[ ]+ {
	Token="<hbox>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EHBOX;
	return(PART_HBOX);
}

\<\/hbox\> { 
	Token="</hbox>"; 
	return(EHBOX);
}


\<frame\/\> {
	Token="<frame/>";
	pending_close_token = EFRAME;
	return(FRAME);
}

\<frame\> {
	Token="<frame>";
	return(FRAME);
}

\<frame[ ]+ {
	Token="<frame>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EFRAME;
	return(PART_FRAME);
}

\<\/frame\> {
	Token="</frame>";
	return(EFRAME);
}


\<text\/\> {
	Token="<text/>";
	pending_close_token = ETEXT;
	return(TEXT);
}

\<text\> {
	Token="<text>";
	return(TEXT);
}

\<text[ ]+ {
	Token="<text>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = ETEXT;
	return(PART_TEXT);
}

\<\/text\> { 
	Token="</text>"; 
	return(ETEXT);
}


\<pixmap\/\> {
	Token="<pixmap/>";
	pending_close_token = EPIXMAP;
	return(PIXMAP);
}

\<pixmap\> {
	Token="<pixmap>";
	return(PIXMAP);
}

\<\/pixmap\> {
	Token="</pixmap>";
	return(EPIXMAP);
}

\<pixmap[ ]+ {
	Token="<pixmap>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EPIXMAP;
	return(PART_PIXMAP);
}


\<entry\/\> {
	Token="<entry/>";
	pending_close_token = EENTRY;
	return(ENTRY);
}

\<entry\> {
	Token="<entry>";
	return(ENTRY);
}

\<\/entry\> {
	Token="</entry>";
	return(EENTRY);
}

\<entry[ ]+ {
	Token="<entry>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EENTRY;
	return(PART_ENTRY);
}


\<edit\/\> {
	Token="<edit/>";
	pending_close_token = EEDIT;
	return(EDIT);
}

\<edit\> {
	Token="<edit>";
	return(EDIT);
}

\<edit[ ]+ {
	Token="<entry>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EEDIT;
	return(PART_EDIT);
}

\<\/edit\> { 
	Token="</edit>"; 
	return(EEDIT);
}


\<tree\/\> {
	Token="<tree/>";
	pending_close_token = ETREE;
	return(TREE);
}

\<tree\> {
	Token="<tree>";
	return  TREE;
}

\<tree[ ]+ {
	Token="<tree>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = ETREE;
	return PART_TREE;
}

\<\/tree\> {
	Token="</tree>"; 
	return ETREE;
}


\<chooser\/\> {
	Token="<chooser/>";
	pending_close_token = ECHOOSER;
	return(CHOOSER);
}

\<chooser\> {
	Token="<chooser>";
	return(CHOOSER);
}

\<\/chooser\> {
	Token="</chooser>";
	return(ECHOOSER);
}

\<chooser[ ]+ {
	Token="<chooser>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = ECHOOSER;
	return PART_CHOOSER;
}


\<button\/\> {
	Token="<button/>";
	pending_close_token = EBUTTON;
	return(BUTTON);
}

\<button\> {
	Token="<button>";
	return(BUTTON);
}

\<\/button\> {
	Token="</button>";
	return(EBUTTON);
}

\<button[ ]+/([-a-zA-Z_]*=) {
	Token="<button>";
	BEGIN(ST_TAG_ATTR);
	current_close_token = EBUTTON;
	return PART_BUTTON;
}


\<buttonbox\/\>				{ Token="<buttonbox/>"; pending_close_token = EBUTTONBOX; return(BUTTONBOX); }
\<buttonbox\>				{ Token="<buttonbox>"; return(BUTTONBOX);		}
\<\/buttonbox\>				{ Token="</buttonbox>"; return(EBUTTONBOX);		}
\<buttonbox[ ]+				{ Token="<buttonbox>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EBUTTONBOX;
					  return(PART_BUTTONBOX);				}

\<checkbox\/\>				{ Token="<checkbox/>"; pending_close_token = ECHECKBOX; return(CHECKBOX); }
\<checkbox\>				{ Token="<checkbox>"; return(CHECKBOX);       		}
\<\/checkbox\>  			{ Token="</checkbox>"; return(ECHECKBOX);     		}
\<checkbox[ ]+  			{ Token="<checkbox>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ECHECKBOX;
					  return(PART_CHECKBOX);  				}

\<radiobutton\/\>			{ Token="<radiobutton/>"; pending_close_token = ERADIO; return(RADIO); }
\<radiobutton\>    			{ Token="<radiobutton>"; return(RADIO);      		}
\<\/radiobutton\>  			{ Token="</radiobutton>"; return(ERADIO);    		}
\<radiobutton[ ]+  			{ Token="<radiobutton>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ERADIO;
					  return(PART_RADIO);  					}

\<progressbar\/\>			{ Token="<progressbar/>"; pending_close_token = EPROGRESSBAR; return(PROGRESSBAR); }
\<progressbar\>    			{ Token="<progressbar>"; return(PROGRESSBAR);      	}
\<\/progressbar\>  			{ Token="</progressbar>"; return(EPROGRESSBAR);    	}
\<progressbar[ ]+  			{ Token="<progressbar>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EPROGRESSBAR;
					  return(PART_PROGRESSBAR);  				}


\<radio\/\>				{ Token="<radio/>"; pending_close_token = ERADIO; return(RADIO); }
\<radio\>    				{ Token="<radio>"; return(RADIO);  			}
\<\/radio\>  				{ Token="</radio>"; return(ERADIO);  			}

\<gvim\/\>				{ Token="<gvim/>"; pending_close_token = EGVIM; return(GVIM); }
\<gvim\>     				{ Token="<gvim>"; return(GVIM);  			}
\<\/gvim\>   				{ Token="</gvim>"; return(EGVIM);  			}

\<combobox\/\>				{ Token="<combobox/>"; pending_close_token = ECOMBOBOX; return(COMBOBOX); }
\<combobox\>    			{ Token="<combobox>"; return(COMBOBOX);		}
\<combobox[ ]+  			{ Token="<combobox>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ECOMBOBOX;
					  return(PART_COMBOBOX); 					}
\<\/combobox\>  			{ Token="</combobox>"; return(ECOMBOBOX);	}

\<list\/\>				{ Token="<list/>"; pending_close_token = ELIST; return(LIST); }
\<list\>    				{ Token="<list>";  return(LIST);  			}
\<list[ ]+      			{ Token="<list>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ELIST;
					  return(PART_LIST); 					}
\<\/list\>  				{ Token="</list>"; return(ELIST);  			}

\<table\/\>				{ Token="<table/>"; pending_close_token = ETABLE; return(TABLE); }
\<table\>    				{ Token="<table>"; return(TABLE); }
\<table[ ]+    				{ Token="<table>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ETABLE;
					  return(PART_TABLE); }
\<\/table\>  				{ Token="</table>"; return(ETABLE); }

\<menubar\/\>				{ Token="<menubar/>"; pending_close_token = EMENUBAR; return(MENUBAR); }
\<menubar\>    				{ Token="<menubar>"; return(MENUBAR); }
\<menubar[ ]+    			{ Token="<menubar>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EMENUBAR;
					  return(PART_MENUBAR); }
\<\/menubar\>  				{ Token="</menubar>"; return(EMENUBAR); }

\<menu\/\>				{ Token="<menu/>"; pending_close_token = EMENU; return(MENU); }
\<menu\>    				{ Token="<menu>"; return(MENU); }
\<menu[ ]+    				{ Token="<menu>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EMENU;
					  return(PART_MENU); }
\<\/menu\>  				{ Token="</menu>"; return(EMENU); }

\<menuitem\/\>				{ Token="<menuitem/>"; pending_close_token = EMENUITEM; return(MENUITEM); }
\<menuitem\>    			{ Token="<menuitem>"; return(MENUITEM); }
\<menuitem[ ]+  			{ Token="<menuitem>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EMENUITEM;
					  return(PART_MENUITEM); }
\<\/menuitem\>  			{ Token="</menuitem>"; return(EMENUITEM); }

\<menuitemseparator\/\>		{ Token="<menuitemseparator/>"; pending_close_token = EMENUITEMSEPARATOR; return(MENUITEMSEPARATOR); }
\<menuitemseparator\>    	{ Token="<menuitemseparator>"; return(MENUITEMSEPARATOR); }
\<\/menuitemseparator\>		{ Token="</menuitemseparator>"; return(EMENUITEMSEPARATOR); }

\<separator\/\>			{ Token="<menuitemseparator/>"; pending_close_token = EMENUITEMSEPARATOR; return(MENUITEMSEPARATOR); }
\<separator\>    			{ Token="<menuitemseparator>"; return(MENUITEMSEPARATOR); }
\<\/separator\>				{ Token="</menuitemseparator>"; return(EMENUITEMSEPARATOR); }

	/**************************************************************
	 * Thunor: Newly supported widgets.
	 **************************************************************/
\<hseparator\/\>			{ Token="<hseparator/>"; pending_close_token = EHSEPARATOR; return(HSEPARATOR); }
\<hseparator\>    			{ Token="<hseparator>"; return(HSEPARATOR); }
\<hseparator[ ]+  			{ Token="<hseparator>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EHSEPARATOR;
					  return(PART_HSEPARATOR); }
\<\/hseparator\>			{ Token="</hseparator>"; return(EHSEPARATOR); }

\<vseparator\/\>			{ Token="<vseparator/>"; pending_close_token = EVSEPARATOR; return(VSEPARATOR); }
\<vseparator\>    			{ Token="<vseparator>"; return(VSEPARATOR); }
\<vseparator[ ]+  			{ Token="<vseparator>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EVSEPARATOR;
					  return(PART_VSEPARATOR); }
\<\/vseparator\>			{ Token="</vseparator>"; return(EVSEPARATOR); }

\<comboboxtext\/\>			{ Token="<comboboxtext/>"; pending_close_token = ECOMBOBOXTEXT; return(COMBOBOXTEXT); }
\<comboboxtext\>   			{ Token="<comboboxtext>"; return(COMBOBOXTEXT); }
\<comboboxtext[ ]+  		{ Token="<comboboxtext>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ECOMBOBOXTEXT;
					  return(PART_COMBOBOXTEXT); }
\<\/comboboxtext\>  		{ Token="</comboboxtext>"; return(ECOMBOBOXTEXT); }

\<comboboxentry\/\>		{ Token="<comboboxentry/>"; pending_close_token = ECOMBOBOXENTRY; return(COMBOBOXENTRY); }
\<comboboxentry\>   		{ Token="<comboboxentry>"; return(COMBOBOXENTRY); }
\<comboboxentry[ ]+  		{ Token="<comboboxentry>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ECOMBOBOXENTRY;
					  return(PART_COMBOBOXENTRY); }
\<\/comboboxentry\>  		{ Token="</comboboxentry>"; return(ECOMBOBOXENTRY); }

\<hscale\/\>				{ Token="<hscale/>"; pending_close_token = EHSCALE; return(HSCALE); }
\<hscale\>					{ Token="<hscale>"; return(HSCALE); }
\<hscale[ ]+				{ Token="<hscale>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EHSCALE;
					  return(PART_HSCALE); }
\<\/hscale\>				{ Token="</hscale>"; return(EHSCALE); }

\<vscale\/\>				{ Token="<vscale/>"; pending_close_token = EVSCALE; return(VSCALE); }
\<vscale\>					{ Token="<vscale>"; return(VSCALE); }
\<vscale[ ]+				{ Token="<vscale>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EVSCALE;
					  return(PART_VSCALE); }
\<\/vscale\>				{ Token="</vscale>"; return(EVSCALE); }

\<spinbutton\/\>			{ Token="<spinbutton/>"; pending_close_token = ESPINBUTTON; return(SPINBUTTON); }
\<spinbutton\>				{ Token="<spinbutton>"; return(SPINBUTTON); }
\<spinbutton[ ]+			{ Token="<spinbutton>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ESPINBUTTON;
					  return(PART_SPINBUTTON); }
\<\/spinbutton\>			{ Token="</spinbutton>"; return(ESPINBUTTON); }

\<timer\/\>				{ Token="<timer/>"; pending_close_token = ETIMER; return(TIMER); }
\<timer\>					{ Token="<timer>"; return(TIMER); }
\<timer[ ]+					{ Token="<timer>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ETIMER;
					  return(PART_TIMER); }
\<\/timer\>					{ Token="</timer>"; return(ETIMER); }

\<togglebutton\/\>			{ Token="<togglebutton/>"; pending_close_token = ETOGGLEBUTTON; return(TOGGLEBUTTON); }
\<togglebutton\>			{ Token="<togglebutton>"; return(TOGGLEBUTTON); }
\<togglebutton[ ]+			{ Token="<togglebutton>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ETOGGLEBUTTON;
					  return(PART_TOGGLEBUTTON); }
\<\/togglebutton\>			{ Token="</togglebutton>"; return(ETOGGLEBUTTON); }

\<statusbar\/\>			{ Token="<statusbar/>"; pending_close_token = ESTATUSBAR; return(STATUSBAR); }
\<statusbar\>				{ Token="<statusbar>"; return(STATUSBAR); }
\<statusbar[ ]+				{ Token="<statusbar>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ESTATUSBAR;
					  return(PART_STATUSBAR); }
\<\/statusbar\>				{ Token="</statusbar>"; return(ESTATUSBAR); }

\<colorbutton\/\>			{ Token="<colorbutton/>"; pending_close_token = ECOLORBUTTON; return(COLORBUTTON); }
\<colorbutton\>				{ Token="<colorbutton>"; return(COLORBUTTON); }
\<colorbutton[ ]+			{ Token="<colorbutton>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ECOLORBUTTON;
					  return(PART_COLORBUTTON); }
\<\/colorbutton\>			{ Token="</colorbutton>"; return(ECOLORBUTTON); }

\<fontbutton\/\>			{ Token="<fontbutton/>"; pending_close_token = EFONTBUTTON; return(FONTBUTTON); }
\<fontbutton\>				{ Token="<fontbutton>"; return(FONTBUTTON); }
\<fontbutton[ ]+			{ Token="<fontbutton>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EFONTBUTTON;
					  return(PART_FONTBUTTON); }
\<\/fontbutton\>			{ Token="</fontbutton>"; return(EFONTBUTTON); }

\<terminal\/\>				{ Token="<terminal/>"; pending_close_token = ETERMINAL; return(TERMINAL); }
\<terminal\>				{ Token="<terminal>"; return(TERMINAL); }
\<terminal[ ]+				{ Token="<terminal>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ETERMINAL;
					  return(PART_TERMINAL); }
\<\/terminal\>				{ Token="</terminal>"; return(ETERMINAL); }

\<webview\/\>				{ Token="<webview/>"; pending_close_token = EWEBVIEW; return(WEBVIEW); }
\<webview\>				{ Token="<webview>"; return(WEBVIEW); }
\<webview[ ]+				{ Token="<webview>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EWEBVIEW;
					  return(PART_WEBVIEW); }
\<\/webview\>				{ Token="</webview>"; return(EWEBVIEW); }

\<sourceview\/\>			{ Token="<sourceview/>"; pending_close_token = ESOURCEVIEW; return(SOURCEVIEW); }
\<sourceview\>				{ Token="<sourceview>"; return(SOURCEVIEW); }
\<sourceview[ ]+			{ Token="<sourceview>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ESOURCEVIEW;
					  return(PART_SOURCEVIEW); }
\<\/sourceview\>			{ Token="</sourceview>"; return(ESOURCEVIEW); }

\<eventbox\/\>				{ Token="<eventbox/>"; pending_close_token = EEVENTBOX; return(EVENTBOX); }
\<eventbox\>				{ Token="<eventbox>"; return(EVENTBOX); }
\<eventbox[ ]+				{ Token="<eventbox>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EEVENTBOX;
					  return(PART_EVENTBOX); }
\<\/eventbox\>				{ Token="</eventbox>"; return(EEVENTBOX); }

\<expander\/\>				{ Token="<expander/>"; pending_close_token = EEXPANDER; return(EXPANDER); }
\<expander\>				{ Token="<expander>"; return(EXPANDER); }
\<expander[ ]+				{ Token="<expander>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EEXPANDER;
					  return(PART_EXPANDER); }
\<\/expander\>				{ Token="</expander>"; return(EEXPANDER); }

\<switch\/\>				{ Token="<switch/>"; pending_close_token = ESWITCH; return(SWITCH); }
\<switch\>				{ Token="<switch>"; return(SWITCH); }
\<switch[ ]+				{ Token="<switch>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = ESWITCH;
					  return(PART_SWITCH); }
\<\/switch\>				{ Token="</switch>"; return(ESWITCH); }



\<label\>    				{ Token="<label>"; return(LABEL);    			}
\<\/label\>  				{ Token="</label>"; return(ELABEL);  			}

\<item\>     				{ Token="<item>"; return(ITEM);      			}
\<\/item\>   				{ Token="</item>"; return(EITEM);    			}
\<item[ ]+   				{ Token="<item>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EITEM;
					  return(PART_ITEM); 					}

\<default\>      			{ Token="<default>"; return(DEFAULT);  			}
\<\/default\>    			{ Token="</default>"; return(EDEFAULT);  		}

\<visible\>      			{ Token="<sensitive>"; return(SENSITIVE);  		}
\<\/visible\>    			{ Token="</sensitive>"; return(ESENSITIVE);  	}

\<sensitive\>      			{ Token="<sensitive>"; return(SENSITIVE);  		}
\<\/sensitive\>    			{ Token="</sensitive>"; return(ESENSITIVE);  	}

\<height\>       			{ Token="<height>"; return(HEIGHT);  			}
\<\/height\>     			{ Token="</height>"; return(EHEIGHT);  			}

\<width\>        			{ Token="<width>"; return(WIDTH);   			}
\<\/width\>      			{ Token="</width>"; return(EWIDTH);   			}

\<input\>        			{ Token="<input>"; return(INPUT);   			}
\<\/input\>      			{ Token="</input>"; return(EINPUT);   			}
\<\input\ [ ]*   			{ Token="<input>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EINPUT;
					  return(PART_INPUT);   				}

\<output\>        			{ Token="<output>"; return(OUTPUT);   			}
\<\/output\>      			{ Token="</output>"; return(EOUTPUT);   		}
\<\output\ [ ]*   			{ Token="<output>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EOUTPUT;
					  return(PART_OUTPUT);   			}

\<variable\>     			{ Token="<variable>"; return(VARIABLE);  		}
\<variable[ ]+   			{ Token="<variable>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EVARIABLE;
					  return(PART_VARIABLE); 				}
\<\/variable\>   			{ Token="</variable>"; return(EVARIABLE);  		}

	/*
	** The definition of action tags.
	*/

\<action\>     				{ Token="<action>"; return(ACTION);  			}
\<action[ ]+   				{ Token="<action>";
					  BEGIN(ST_TAG_ATTR);
					  current_close_token = EACTION;
					  return(PART_ACTION); 					}
\<\/action\>     			{ Token="</action>"; return(EACTION);  			}






\<\/[^> ]*\> { 
	Token=g_strdup(yytext); 
	gtkdialog_error("Unknown end tag.");  
}

\<[^> ]*\> { 
	Token=g_strdup(yytext); 
	gtkdialog_error("Unknown tag.");      
}
					
					/*
					 * The quoted string. It can contain anything, except
					 * unescaped double quote.
					 */
\"	  				{
					  Token = "double quote";
					  BEGIN(ST_QUOTED_STRING);				}
					  
<ST_QUOTED_STRING>[^\\"]+		{
					  yymore();						}

<ST_QUOTED_STRING>"\\\""		{
					  yymore();						}
					  
<ST_QUOTED_STRING>\"			{
					  Token = yytext;
					  gtkdialog_lval.cval = g_strdup(yytext);
					  gtkdialog_lval.cval[strlen(gtkdialog_lval.cval) - 1] = '\0';
					  BEGIN(0);
					  return STRING;
					  							}

					/*
					 * The single-quoted string. It can contain anything
					 * except a single quote (no escape sequences).
					 */
\x27	  				{
					  Token = "single quote";
					  BEGIN(ST_SQUOTED_STRING);				}

<ST_SQUOTED_STRING>[^\x27]+		{
					  yymore();						}

<ST_SQUOTED_STRING>\x27			{
					  Token = yytext;
					  gtkdialog_lval.cval = g_strdup(yytext);
					  gtkdialog_lval.cval[strlen(gtkdialog_lval.cval) - 1] = '\0';
					  BEGIN(0);
					  return STRING;
					  							}

					/*
					 * An unquoted string can contain anything except
					 * unescaped '<'.
					 */
\\<					{
					  Token = "string";
					  BEGIN(ST_STRING);
					  yymore();
												}
[^ \n\t\>\<\"\x27][^\n\<\\]*  		{
					  Token = "string";
					  BEGIN(ST_STRING);
					  yymore();
												}
<ST_STRING>[^\n\<\\]+  			{
					  Token = "string";
					  yymore();
												}


<ST_STRING>"\\<"			{
					  yymore();
												}

<ST_STRING>\\.				{
					  yymore();
												}

<ST_STRING>\n				{
					  ++linenumber;
					  yymore();
												}

<ST_STRING>"<"				{
					  gchar *tmp = g_strdup(yytext);
					  tmp[strlen(tmp) - 1] = '\0';
					  gtkdialog_lval.cval = strip_backslash_escapes(tmp);
					  g_free(tmp);
					  unput('<');
					  BEGIN(0);
					  return STRING;
					  							}

												

<*>\n 					{
					  ++linenumber;
												}
<*>[\t ] 					{
					  /* */
												}

<*>.                                       {
					  /* we do nothing, this is a dropped char. */
												}
%%

/*
** Reset the lexer state so it can be used for a new parse.
** Must be called before gtkdialog_parse() when re-parsing
** (e.g., when launching a new window).
*/
void gtkdialog_lexer_reset(void)
{
	YY_FLUSH_BUFFER;
	BEGIN(INITIAL);
	linenumber = 1;
}

