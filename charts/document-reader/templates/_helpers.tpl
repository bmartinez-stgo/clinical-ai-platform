{{- define "document-reader.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "document-reader.fullname" -}}
{{- printf "%s" .Chart.Name -}}
{{- end -}}

{{- define "document-reader.labels" -}}
app.kubernetes.io/name: {{ include "document-reader.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.app.serviceVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "document-reader.selectorLabels" -}}
app.kubernetes.io/name: {{ include "document-reader.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
