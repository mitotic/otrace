""" Base tracing class
    Adapted from echo.py written by Thomas Guest <tag@wordaligned.org>
    http://wordaligned.org/articles/echo
"""

import functools
import inspect

def get_naked_function(method):
    """ Return function object associated with a method."""
    if inspect.isfunction(method):
        return method
    return getattr(method, "__func__", None)

def ismethod_or_function(method):
    return inspect.isfunction(get_naked_function(method))

def get_method_type(klass, method):
    """Return 'instancemethod'/'classmethod'/'staticmethod' """
    # Get class attribute directly
    attr_value = klass.__dict__[method.__name__]
    if inspect.isfunction(attr_value):
        # Undecorated function => instance method
        return "instancemethod"
    # Decorated function; return type
    return type(attr_value).__name__

class TraceInfo(object):
    pass

class BaseTrace(object):
    """Base object tracing class.
    All methods are class methods
    Class cannot be instantiated.
    """
    class_trace_attr = "_otrace_class_trace"
    orig_function_attr = "_otrace_orig_function"
    trace_active = False

    @classmethod
    def trace_function(cls, fn, classname="", modulename="", methodtype="", unwrap=False):
        """  Returns a decorated version of the input function which traces calls
        made to it by logging the function's name and the arguments it was
        called with.
        classname is the name of the class for instance/class/static methods.
        methodtype = "" (function) or "instancemethod" or "classmethod" or "staticmethod"
        """
        if hasattr(fn, cls.orig_function_attr):
            if unwrap:
                # Unwrap function (return original function)
                orig_fn = getattr(fn, cls.orig_function_attr)
                delattr(fn, cls.orig_function_attr)
                return orig_fn
            else:
                # Function already wrapped; do nothing
                return fn
        elif unwrap:
            # Function not wrapped; do nothing
            return fn

        info = TraceInfo()
        info.modulename = modulename
        info.classname = classname
        info.methodtype = methodtype
        info.fn = fn

        code = fn.func_code
        argcount = code.co_argcount
        info.argnames = code.co_varnames[:argcount]

        fn_defaults = fn.func_defaults or list()
        info.argdefs = dict(zip(info.argnames[-len(fn_defaults):], fn_defaults))

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            if not cls.trace_active:
                return fn(*args, **kwargs)
            return cls.trace_function_call(info, *args, **kwargs)
        # Save original function
        setattr(wrapped, cls.orig_function_attr, fn)
        return wrapped

    @classmethod
    def trace_method(cls, klass, method, modulename="", unwrap=False):
        """ Change a method of a class so that calls to it are traced.
        """
        methodtype = get_method_type(klass, method)

        mname = method.__name__
        if mname.startswith("__") and not mname.endswith("__"):
            # Private class name; unmangle
            mname = "_%s%s" % (klass.__name__, mname)
    
        never_trace = "__str__", "__repr__", # Avoid recursion in printing method calls
        if mname not in never_trace:
            new_fn = cls.trace_function(get_naked_function(method), klass.__name__, modulename=modulename,
                                        methodtype=methodtype, unwrap=unwrap)
            if methodtype == "classmethod":
                new_fn = classmethod(new_fn)
            elif methodtype == "staticmethod":
                new_fn = staticmethod(new_fn)

            setattr(klass, mname, new_fn)

        return getattr(klass, mname)
    
    @classmethod
    def trace_class(cls, klass, exclude=[], include=[], modulename="", unwrap=False):
        """ Trace calls to class methods
        """
        if unwrap:
            if hasattr(klass, cls.class_trace_attr):
                delattr(klass, cls.class_trace_attr)
        else:
            setattr(klass, cls.class_trace_attr, True)

        for _, method in inspect.getmembers(klass, ismethod_or_function):
            if ((not include or method.__name__ in include) and
                (not exclude or method.__name__ not in exclude) and
                method.__name__ in klass.__dict__):
                cls.trace_method(klass, method, modulename=modulename, unwrap=unwrap)
    
    @classmethod
    def trace_modfunc(cls, mod, fn, unwrap=False):
        """ Trace calls to function in module
        """
        setattr(mod, fn.__name__, cls.trace_function(fn, modulename=mod.__name__, unwrap=unwrap))

    @classmethod
    def trace_module(cls, mod, exclude=[], include=[], unwrap=False):
        """ Trace calls to functions and methods in a module.
        Returns list of names traced.
        """
        traced_list = []
        for fname, fn in inspect.getmembers(mod, inspect.isfunction):
            if ((not include or fn.__name__ in include) and
                (not exclude or fn.__name__ not in exclude)):
                cls.trace_modfunc(mod, fn, unwrap=unwrap)
                traced_list.append(fn.__name__)

        for _, klass in inspect.getmembers(mod, inspect.isclass):
            if ((not include or klass.__name__ in include) and
                (not exclude or klass.__name__ not in exclude)):
                cls.trace_class(klass, modulename=mod.__name__, unwrap=unwrap)
                traced_list.append(klass.__name__)
        return traced_list

    @classmethod
    def trace_function_call(cls, info, *args, **kwargs):
        raise Exception("NOT IMPLEMENTED")
   
