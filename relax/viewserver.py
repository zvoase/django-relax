# -*- coding: utf-8 -*-

from os import linesep as NEWLINE
import SocketServer
import sys
try:
    import threading
except ImportError:
    import dummy_threading as threading

import couchdb

from relax import json, settings, utils


def get_function(function_name):
    """
    Given a Python function name, return the function it refers to.
    """
    module, basename = str(function_name).rsplit('.', 1)
    try:
        return getattr(__import__(module, fromlist=[basename]), basename)
    except (ImportError, AttributeError):
        raise FunctionNotFound(function_name)

def one_lineify(json_data):
    """Prevent JSON data from taking up multiple lines."""
    # simplejson replaces all newlines inside the data with '\\n' (i.e.
    # backslash then n, instead of newline character), so we can safely assume
    # that all newlines are in-between strings.
    return json_data.replace('\n', ' ').replace('\r', ' ')

def js_error(exc):
    """Transform a Python exception into a CouchDB JSON error."""
    # This is the format in which CouchDB interprets errors.
    return json.dumps({
        'error': type(exc).__name__,
        'reason': str(exc)})


class CommandNotFound(Exception):
    
    def __init__(self, command):
        Exception.__init__(self, 'Command %r not found.' % (command,))


class FunctionNotFound(Exception):
    
    def __init__(self, function_name):
        Exception.__init__(self, 'Function %r not found.' % (function_name,))


class ViewServerRequestHandler(SocketServer.StreamRequestHandler):
    
    functions = {}
    function_counter = 0
    
    def handle_reset(self):
        """Reset the current function list."""
        self.functions.clear()
        self.function_counter = 0
    
    def handle_add_fun(self, function_name):
        """Add a function to the function list, in order."""
        function_name = function_name.strip()
        try:
            function = get_function(function_name)
        except Exception, exc:
            self.wfile.write(js_error(exc) + NEWLINE)
            return
        # This tests to see if the function has been decorated with the view
        # server synchronisation decorator (``decorate_view``).
        if not getattr(function, 'view_decorated', None):
            self.functions[function_name] = (self.function_counter, function)
        # The decorator gets called with the logger function.
        else:
            self.functions[function_name] = (self.function_counter,
                function(self.log))
        self.function_counter += 1
        return True
    
    @utils.generator_to_list
    def handle_map_doc(self, document):
        """Return the mapping of a document according to the function list."""
        # This uses the stored set of functions, sorted by order of addition.
        for function in sorted(self.functions.values(), key=lambda x: x[0]):
            try:
                # It has to be run through ``list``, because it may be a
                # generator function.
                yield [list(function(document))]
            except Exception, exc:
                # Otherwise, return an empty list and log the event.
                yield []
                self.log(repr(exc))
    
    def handle_reduce(self, reduce_function_names, mapped_docs):
        """Reduce several mapped documents by several reduction functions."""
        reduce_functions = []
        # This gets a large list of reduction functions, given their names.
        for reduce_function_name in reduce_function_names:
            try:
                reduce_function = get_function(reduce_function_name)
                if getattr(reduce_function, 'view_decorated', None):
                    reduce_function = reduce_function(self.log)
                reduce_functions.append(reduce_function)
            except Exception, exc:
                self.log(repr(exc))
                reduce_functions.append(lambda *args, **kwargs: None)
        # Transform lots of (key, value) pairs into one (keys, values) pair.
        keys, values = zip(
            (key, value) for ((key, doc_id), value) in mapped_docs)
        # This gets the list of results from the reduction functions.
        results = []
        for reduce_function in reduce_functions:
            try:
                results.append(reduce_function(keys, values, rereduce=False))
            except Exception, exc:
                self.log(repr(exc))
                results.append(None)
        return [True, results]
    
    def handle_rereduce(self, reduce_function_names, values):
        """Re-reduce a set of values, with a list of rereduction functions."""
        # This gets a large list of reduction functions, given their names.
        reduce_functions = []
        for reduce_function_name in reduce_function_names:
            try:
                reduce_function = get_function(reduce_function_name)
                if getattr(reduce_function, 'view_decorated', None):
                    reduce_function = reduce_function(self.log)
                reduce_functions.append(reduce_function)
            except Exception, exc:
                self.log(repr(exc))
                reduce_functions.append(lambda *args, **kwargs: None)
        # This gets the list of results from those functions.
        results = []
        for reduce_function in reduce_functions:
            try:
                results.append(reduce_function(None, values, rereduce=True))
            except Exception, exc:
                self.log(repr(exc))
                results.append(None)
        return [True, results]
    
    def handle_validate(self, function_name, new_doc, old_doc, user_ctx):
        """Validate...this function is undocumented, but still in CouchDB."""
        try:
            function = get_function(function_name)
        except Exception, exc:
            self.log(repr(exc))
            return False
        try:
            return function(new_doc, old_doc, user_ctx)
        except Exception, exc:
            self.log(repr(exc))
            return repr(exc)
    
    def handle(self):
        """The main function called to handle a request."""
        while True:
            try:
                line = self.rfile.readline()
                try:
                    # All input data are lines of JSON like the following:
                    #   ["<cmd_name>" "<cmd_arg1>" "<cmd_arg2>" ...]
                    # So I handle this by dispatching to various methods.
                    cmd = json.loads(line)
                except Exception, exc:
                    # Sometimes errors come up. Once again, I can't predict
                    # anything, but can at least tell CouchDB about the error.
                    self.wfile.write(repr(exc) + NEWLINE)
                    continue
                else:
                    # Automagically get the command handler.
                    handler = getattr(self, 'handle_' + cmd[0], None)
                    if not handler:
                        # We are ready to not find commands. It probably won't
                        # happen, but fortune favours the prepared.
                        self.wfile.write(
                            repr(CommandNotFound(cmd[0])) + NEWLINE)
                        continue
                    return_value = handler(*cmd[1:])
                    if not return_value:
                        continue
                    # We write the output back to CouchDB.
                    self.wfile.write(
                        one_lineify(json.dumps(return_value)) + NEWLINE)
            except Exception, exc:
                self.wfile.write(repr(exc) + NEWLINE)
                continue
    
    def log(self, string):
        """Log an event on the CouchDB server."""
        self.wfile.write(json.dumps({'log': string}) + NEWLINE)


class ViewServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass # I don't think this actually requires any code. I may be wrong.


def main(host=settings._('VIEW_SERVER_HOST')):
    host, port = host.split(':') # Should be in format 127.0.0.1:5936
    port = int(port)
    server = ViewServer((host, port), ViewServerRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    print 'View server running at %s on port %s' % (host, port)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)