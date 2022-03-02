{{- define "cloudResources.gcp.serviceAccountName" -}}
{{ .Release.Name }}-user-sa
{{- end }}

{{- define "cloudResources.scratchBucket.name" -}}
{{- if eq .Values.jupyterhub.custom.cloudResources.provider "gcp" -}}
{{ .Values.jupyterhub.custom.cloudResources.gcp.projectId }}-{{ .Release.Name }}-scratch-bucket
{{- end }}
{{- end }}
