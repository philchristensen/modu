modu seeks to carve out a niche among the increasingly crowded arena of Python web application frameworks. It encourages a number of conventions intended to keep large-scale web projects organized and maintainable, while providing a number of optional services that can be used or ignored by the programmer.

modu by itself isn't a blogging tool, or a wiki, but instead a platform for building such things. It is particularly well-suited for the world of custom web application development, as it assumes the less mundane aspects of website construction (site design, URL organization, content) will be recreated for each project.

Work is progressing on the design and implementation of a robust content API based on the Drupal Node API, but this will exist as a separate project, above the modu layer.

Features
========

### Storables

The Storable API provides a simple and lightweight database interaction layer. It's based around the idea that to build a high-performance, scalable web application, developers simply must know and understand SQL, and doesn't attempt to hide this from the user. The API includes a number of generator functions for building more common queries, and a default model class that can be used as-is, or subclassed to provide advanced features.

Current DB support is limited to MySQL 5, but there are proof-of-concept drivers for both the Pygresql and the Pyscopg2 DB-API drivers.

### Forms

modu forms are heavily inspired by the Drupal Form API, and are fully themeable and customizable. Borrowed from PHP is the concept of "nestable" form fields, which are extremely useful in allowing individual form elements to return multiple complex values.

### Editables

Create powerful customizable admin interfaces. The Editable API provides CMS features either through an alternate administrative interface, or embedded in your public-facing web application. Human-readable configuration objects make modifying and creating new interfaces extremely easy for beginning developers, while providing many powerful features for advanced users.

### Pluggable Template System

By default, modu provides a template abstraction layer, allowing use of different content generation mechanisms, even within the same web application. A great deal of work has gone into providing support for the Cheetah Template engine, but proof-of-concept engines exist supporting CherryTemplate and ZPTPages.

### WSGI Support

modu implements the WSGI protocol, and may be installed inside any WSGI-compatible web container. modu can also act as middleware, and embed WSGI applications as resources in the modu URL tree, while optionally customizing the perceived environment. Examples include the trac integration used on the primary modu website.

### User/Role/Session Support

DB-resident sessions provide fully customizable user-tracking features including built-in support for role-based permissions.

### Flexible Deployment Options

modu currently provides several deployment options, depending on the needs of your project. For development and small to medium-sized sites, the built-in  Twisted Python-based web server can provide for most of your needs.

modu has been running on Apache 2.2 with mod_wsgi in high-availability commercial deployments with much success. Although it has not yet been tested on many other configurations, the flexibility of the modu application layer makes support of other container technologies (such as FaastCGI or SCGI) entirely feasible, given user demand.

### JQuery Support

modu uses the Google AJAX Libraries API to fetch the most recent version of the  JQuery JavaScript library.

### FCKEditor Support

Editable interfaces can include any number of embedded  FCKEditor-powered text areas. Support for other WYSIWYG editors is forthcoming.