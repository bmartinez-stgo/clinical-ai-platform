{{- define "vllm-server.fullname" -}}
{{- .Values.app.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "vllm-server.labels" -}}
app: {{ include "vllm-server.fullname" . }}
{{- end }}

{{- define "vllm-server.selectorLabels" -}}
app: {{ include "vllm-server.fullname" . }}
{{- end }}
