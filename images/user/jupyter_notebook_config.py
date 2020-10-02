# This is sh (dash) by default, not $SHELL
c.NotebookApp.terminado_settings = { "shell_command": ["bash"] }

c.ServerProxy.servers = {
  'http-server': {
    'command': ['python3', '-m', 'http.server', '{port}'],
    'absolute_url': False,
    'launcher_entry': {
      'title': "HTTP Server"
    }
  }
}
