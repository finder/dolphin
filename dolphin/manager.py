from django.http import HttpRequest, Http404, HttpResponseRedirect


class FlagManager(object):
    """
    This is an abstraction on the backend to allow multiple backends. It's loaded as dolphin.flipper
    """
    def __init__(self, backend):
        self.backend = backend
        self.registered_checks = {}

    def is_active(self, key, *args, **kwargs):
        """Tests if the flag is active"""
        ret = self.backend.is_active(key, *args, **kwargs)
        if not ret: return False
        if key in self.registered_checks:
            for check in self.registered_checks[key]:
                kwargs['backend'] = self.backend
                if not check(key, **kwargs):
                    return False
        return True

    def delete(self, key, *args, **kwargs):
        """Deletes the FeatureFlag"""
        return self.backend.delete(key, *args, **kwargs)

    def all_flags(self, *args, **kwargs):
        return self.backend.all_flags(*args, **kwargs)

    def active_flags(self, *args, **kwargs):
        """Returns a list of active flags (not including overrides)"""
        return self.backend.active_flags(*args, **kwargs)

    def switch_is_active(self, key, **kwargs):
        """A decorator that redirects if redirect is provided,
        returns alt if it's provided, or raises Http404 otherwise"""
        redirect = kwargs.get('redirect', None)
        alt = kwargs.get('alt', None)

        def wrap(f):
            def newf(*args, **kwargs):
                if args and isinstance(args[0], HttpRequest):
                    request = args[0]
                else:
                    request = None

                if self.is_active(key, request=request):
                    return f(*args, **kwargs)
                else:
                    if redirect:
                        return HttpResponseRedirect(redirect)
                    if alt:
                        return alt(*args, **kwargs)
                    raise Http404('Switch %s is not active.'%key)
            return newf
        return wrap

    def ifactive(self, key, active_var, else_var, **kwargs):
        if self.is_active(key, **kwargs):
            return active_var
        else:
            return else_var

    def register_check(self, key, flag):
        """
        Allows you to register custom flags. The flag should be a function that returns True or False
        given the key and **kwargs
        """
        self.registered_checks.setdefault(key, []).append(flag)
