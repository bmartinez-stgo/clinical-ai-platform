{{- define "gateway.name" -}}
gateway
{{- end }}

{{- define "gateway.fullname" -}}
{{ .Release.Name }}-gateway
{{- end }}
