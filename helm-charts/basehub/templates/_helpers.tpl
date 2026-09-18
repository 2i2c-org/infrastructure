# Helper template partials

# Converts helm values to python literals
{{- define "python.literal" -}}
{{- if kindIs "bool" . -}}
{{ ternary "True" "False" . }}
{{- else if kindIs "string" . -}}
{{ printf "%q" . }}
{{- else -}}
{{ . }}
{{- end -}}
{{- end -}}