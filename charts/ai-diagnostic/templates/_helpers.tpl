{{- define "ai-diagnostic.name" -}}
{{- .Values.app.name -}}
{{- end -}}

{{- define "ai-diagnostic.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}

{{- define "ai-diagnostic.labels" -}}
app.kubernetes.io/name: {{ include "ai-diagnostic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "ai-diagnostic.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ai-diagnostic.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
