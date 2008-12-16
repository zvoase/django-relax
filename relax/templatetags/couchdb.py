# -*- coding: utf-8 -*-

import re

from django import template
from django.template.defaultfilters import stringfilter

from relax import json, settings


register = template.Library()

class SettingNode(template.Node):
    
    def __init__(self, setting_name, var_name=None, default_value=None):
        # The variable name will be stored no matter what.
        self.var_name = var_name
        # If there is a default value, it will be added to the args for the
        # relax.settings._ function; otherwise it will just be the setting
        # name.
        self.setting_args = ((setting_name, default_value) if default_value
            else (setting_name,))
    
    def render(self, context):
        # We pre-stored these arguments in __init__, remember?
        value = settings._(*self.setting_args)
        # If a variable name was provided, use it.
        if self.var_name:
            context[self.var_name] = value
            return ''
        # Otherwise, render the setting as a string in the template.
        else:
            return str(value)


def get_setting(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            '%r tag requires arguments' % (token.contents.split()[0],))
    # Here we match 4 different regexs. This deals with the optional presence
    # of both a default value and a variable name.
    match = re.search(r'^([A-Za-z0-9_-]+)$', arg)
    if not match:
        match = re.search(r'^([A-Za-z0-9_-]+) (.*?)$', arg)
        if not match:
            match = re.search(r'^([A-Za-z0-9_-]+) (.*?) as ([A-Za-z0-9_]+)$', arg)
            if not match:
                match = re.search(r'^([A-Za-z0-9_-]+) as ([A-Za-z0-9_]+)$', arg)
                if not match:
                    # If all else fails, just raise an error.
                    raise template.TemplateSyntaxError('Invalid arguments for %r tag' %
                        (tag_name,))
                setting_name, var_name = match.groups()
                return SettingNode(setting_name, var_name=var_name)
            setting_name, default_value, var_name = match.groups()
            # The default value should be specified in JSON format. This makes
            # things considerably more secure than just using eval().
            default_value = json.loads(default_value)
            return SettingNode(setting_name, var_name=var_name,
                default_value=default_value)
        setting_name, default_value = match.groups()
        default_value = json.loads(default_value)
        return SettingNode(setting_name, default_value=default_value)
    setting_name = match.groups()[0]
    return SettingNode(setting_name)

register.tag('setting', get_setting)