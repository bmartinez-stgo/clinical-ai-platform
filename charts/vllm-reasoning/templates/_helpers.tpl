{{- define "vllm-reasoning.fullname" -}}
{{- .Values.app.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "vllm-reasoning.labels" -}}
app: {{ include "vllm-reasoning.fullname" . }}
{{- end }}

{{- define "vllm-reasoning.selectorLabels" -}}
app: {{ include "vllm-reasoning.fullname" . }}
{{- end }}
