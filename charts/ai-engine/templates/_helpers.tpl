{{- define "ai-engine.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "ai-engine.fullname" -}}
{{- printf "%s" .Chart.Name -}}
{{- end -}}

{{- define "ai-engine.labels" -}}
app.kubernetes.io/name: {{ include "ai-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.app.serviceVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "ai-engine.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ai-engine.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
