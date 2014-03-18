#!/usr/bin/python
# -*- coding: utf-8 -*-
from gi.repository import Gtk, GObject, Gdk
from subprocess import Popen, PIPE
import sys, os, re, ConfigParser, time
from threading import Thread
from Queue import Queue
import traceback


PACKAGE = '@PACKAGE@'
PATH_SELF = os.path.abspath(os.path.dirname(__file__))
PATH_BASE = os.path.dirname(PATH_SELF)
PATH_CONFIG = PATH_BASE + '/@rel_config@'
PATH_BUILDER = PATH_SELF + '/gtk-builder.xml'
PATH_SCRIPTS = PATH_BASE + '/@rel_scriptsdir@'


class PrettyException(Exception):

   def __init__(self, title, reason=None, info=[]):
      message = '«' + title + '»'
      if reason != None:
         message = self._add_line(message, 'reason', str(reason))
      for key, value in info:
         message = self._add_line(message, key, value)
      Exception.__init__(self, message)

   def _add_line(self, message, key, value):
      key = key.capitalize()
      value = str(value)
      return message + '\n• ' + key + ': «' + value + '»'


class ConfigException(PrettyException):

   def __init__(self, reason=None):
      title = 'Oops! It seems that the config file is quite fucked up'
      PrettyException.__init__(self, title, reason)


class Config(ConfigParser.ConfigParser):
   
   EXPECTED_SECTIONS = ['path','command']
   EXPECTED_OPTIONS = {
      'path' : ['lampp'],
      'command' : [
         'lampp',
         'start', 'startapache', 'startmysql', 'startftp',
         'stop', 'stopapache', 'stopmysql', 'stopftp',
         'reload', 'reloadapache', 'reloadmysql', 'reloadftp',
         'restart', 'security',
         'enablessl', 'disablessl',
         'backup', 'oci8',
         'status'
      ]
   }
   
   def __init__(self):
      ConfigParser.ConfigParser.__init__(self)
      
      self.add_section('path')
      self.add_section('command')
      self.add_section('service')
      
      self.set('path','base', PATH_BASE)
      self.set('path','config', PATH_CONFIG)
      self.set('path','gui_builder', PATH_BUILDER)
      self.set('path','scripts', PATH_SCRIPTS)
      
      self.set('service', 'apache', 'httpd')
      self.set('service', 'mysql', 'mysqld')
      self.set('service', 'ftp', 'proftpd')
      
      try:
         self._user_config = ConfigParser.ConfigParser()
         self._user_config.read(self.get('path','config'))
         self._parse_user_config()
         self._resolve_refs()
      except:
         sys.exit(traceback.format_exc())
         
   def _parse_user_config(self):
      found_sections = self._user_config.sections()
      for section in self.EXPECTED_SECTIONS:
         if section not in found_sections:
            raise ConfigException('section "'+section+'" not found')
         found_options = self._user_config.options(section)
         for option in self.EXPECTED_OPTIONS[section]:
            if option not in found_options:
               raise ConfigException(
                  'option "'+option+'" from section "'+section+'" not found')
            else:
               self.set(section, option, self._user_config.get(section, option))
   
   def _resolve_refs(self, limit=10):
      ref_found = False
      r = re.compile('%(\w+)%')
      sections = self.sections()
      for section in sections:
         for option in self.options(section):
            value = self.get(section, option)
            m = r.match(value)
            if m:
               ref = m.group(1).split('_',1)
               if len(ref) == 1:
                  continue
               ref_section = ref.pop(0)
               ref_option = ref.pop(0)
               try:
                  replacement = self.get(ref_section, ref_option)
                  search = m.group(0)
                  value = value.replace(search, replacement)
                  self.set(section, option, value)
                  ref_found = True
               except:
                  continue
      if ref_found:
         if limit==0:
            raise ConfigException('too much recursion in references')
         else:
            self._resolve_refs(limit-1)

   def __str__(self):
      result = []
      for section in self.sections():
         result.append('[' + section + ']')
         for option in self.options(section):
            result.append(option + ': ' + str(self.get(section, option)))
      return '\n'.join(result)


config = Config()


class CommandException(PrettyException):

   def __init__(self, command, reason=None):
      title = 'Oops! Something naughty happened while executing a command'
      info = [
         ('command name'    , self._format_name(command)),
         ('command'         , command.command),
         ('exit code'       , command.process.returncode),
         ('standard output' , self._format_std(command.stdout)),
         ('standard error'  , self._format_std(command.stderr))
      ]
      PrettyException.__init__(self, title, reason, info)

   def _format_std(self, std):
      arr = std.rsplit('\n',1)
      if len(arr) == 2 and arr[1] == '':
         return arr[0]
      return std

   def _format_name(self, command):
      if command.command_name == command.command:
         return None
      return command.command_name


class Command:
   
   def __init__(self, command, shell=True, config=config):
      self.command_name = command
      self.shell = shell
      if config:
         self.command = config.get('command',command)
      else:
         self.command = command
      self.stdout = None
      self.stderr = None
      self.process = None
   
   def run(self):
      self.process = Popen(
         self.command, shell=self.shell, stdout=PIPE, stderr=PIPE)
      (self.stdout, self.stderr) = self.process.communicate()
      return self
   
   def failed(self):
      return self.process.returncode or self.stderr


class ServiceGui:
   
   def __init__(self, parent, builder, name):
      self.parent = parent
      self.label = builder.get_object("label_"+name)
      self.button_start = builder.get_object("button_start_"+name)
      self.button_stop = builder.get_object("button_stop_"+name)
      self.button_reload = builder.get_object("button_reload_"+name)
      self.spinner = builder.get_object("spinner_"+name)
      self.button_start.connect("clicked", self.on_button_start_clicked)
      self.button_stop.connect("clicked", self.on_button_stop_clicked)
      self.button_reload.connect("clicked", self.on_button_reload_clicked)
      self.label_pid = builder.get_object("label_pid_"+name)
      self.label_ports = builder.get_object("label_ports_"+name)
      self.loading = False
      self.start_command = 'start'+name
      self.stop_command = 'stop'+name
      self.reload_command = 'reload'+name
   
   def change_view(self, start=True, stop=False, reload=False,
                   spinner=False, pid=None, ports=None):
      self.button_start.set_sensitive(start)
      self.button_stop.set_sensitive(stop)
      self.button_reload.set_sensitive(reload)
      self.spinner.set_visible(spinner)
      if pid==None:
         if spinner:
            self.label_pid.hide()
         else:
            self.label_pid.show()
            self.label_pid.set_markup('none')
            self.label_pid.set_sensitive(False)
         self.label_ports.set_markup('none')
         self.label_ports.set_sensitive(False)
      else:
         self.label_pid.set_markup(pid)
         self.label_pid.set_sensitive(True)
         self.label_pid.show()
         self.label_ports.set_markup(', '.join(ports))
         self.label_ports.set_sensitive(True)
   
   def run_command_callback(self, command):
      try:
         if command.failed():
            raise CommandException(command)
         self.loading = False
         self.parent.update_view()
      except:
         sys.exit(traceback.format_exc())
   
   def run_command(self, command):
      self.loading = True
      self.change_view(False, False, False, True)
      self.parent.run_command(command, self.run_command_callback)
   
   def on_button_start_clicked(self, widget, data=None):
      self.run_command(self.start_command)

   def on_button_stop_clicked(self, widget, data=None):
      self.run_command(self.stop_command)

   def on_button_reload_clicked(self, widget, data=None):
      self.run_command(self.reload_command)
   
   def update_view(self, pid=None, ports=None):
      if not self.loading:
         if pid==None:
            self.change_view(True, False, False)
         else:
            self.change_view(False, True, True, False, pid, ports)


class GLampp ():
   
   def __init__(self):
      b = Gtk.Builder()
      b.add_from_file(config.get('path','gui_builder'))
      
      self.window_main = b.get_object("window_main")
      self.window_main.connect("delete-event", self.on_window_main_delete)
      self.window_main.connect("focus-in-event", self.on_window_main_focus)
      
      self.service_apache = ServiceGui(self, b, "apache")
      self.service_mysql = ServiceGui(self, b, "mysql")
      self.service_proftpd = ServiceGui(self, b, "ftp")
      
      b.connect_signals(self)
      self.updater = Updater()
      #self.update_view(sleep=None)
      self.window_main.set_wmclass (PACKAGE,PACKAGE)
      self.window_main.show()

      Gdk.notify_startup_complete()
      
   def update_view(self, command=None, sleep=0.2):
      if command != None:
         try:
            if command.failed():
               raise CommandException(command)
            
            status = command.stdout
            
            args = {
               'httpd'   : [None, None],
               'mysqld'  : [None, None],
               'proftpd' : [None, None]
            }
            
            for line in status.split('\n'):
               if line == '':
                  continue
               info = line.split(' ')
               if len(info) < 3:
                  raise CommandException(
                     command, 'bad line format "' + line + '"')
               service = info.pop(0)
               if service not in args:
                  raise CommandException(
                     command, 'unknown service "' + service + '"')
               pid = info.pop(0)
               port = info.pop(0)
               if args[service][0] == None:
                  args[service] = [pid, [port]]
               else:
                  if args[service][0] == pid:
                     args[service][1].append(port)
                  else:
                     raise CommandException(
                        command, 'multiple PIDs for service "' + service + '"')
            
            self.service_apache.update_view(*args['httpd'])
            self.service_mysql.update_view(*args['mysqld'])
            self.service_proftpd.update_view(*args['proftpd'])
         
         except:
            sys.exit(traceback.format_exc())
      else:
         self.run_command('status', self.update_view, sleep=sleep)
   
   def run_command(self, command, callback, callback_args=[], sleep=None):
      self.updater.add_update(
         Command(command).run, [], callback, callback_args, sleep)
   
   def on_window_main_focus(self, widget, data=None):
      self.update_view(sleep=None)
   
   def on_window_main_delete(self, widget, data=None):
      Gtk.main_quit()


class Updater:

   def __init__(self):
      self._queue = Queue(maxsize=100)
      for _ in range(9):
         t = Thread(target=self._work)
         t.daemon = True
         t.start()

   def _work(self):
      # executed in background thread
      for work, work_args, callback, callback_args, sleep in iter(
         self._queue.get, None):
         output = None
         try:
            if sleep:
               time.sleep(sleep)
            output = work(*work_args)
         except:
            pass
         if callback:
            # signal task completion; run callback() in the main thread
            GObject.idle_add(callback, output, *callback_args)

   def add_update(
      self, work, work_args=[], callback=None, callback_args=[], sleep=None):
      self._queue.put((work, work_args, callback, callback_args, sleep))


def main():
   try:
      GObject.threads_init()
      Gdk.set_program_class(PACKAGE)
      app = GLampp()
      Gtk.main()
   except:
      sys.exit(traceback.format_exc())

if __name__ == "__main__":
   sys.exit(main())

