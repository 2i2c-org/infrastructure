{{- define "cloudResources.gcp.serviceAccountName" -}}
{{.Release.Name}}-user-sa
{{- end }}

{{- define "cloudResources.scratchBucket.name" -}}
{{- if eq .Values.jupyterhub.cloudResources.provider "gcp" -}}
{{ .Values.jupyterhub.cloudResources.gcp.projectId }}-{{ .Release.Name }}-scratch-bucket
{{- end -}}
{{- end }}