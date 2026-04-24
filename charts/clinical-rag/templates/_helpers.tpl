{{- define "clinical-rag.name" -}}
{{- .Values.app.name -}}
{{- end -}}

{{- define "clinical-rag.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}

{{- define "clinical-rag.labels" -}}
app.kubernetes.io/name: {{ include "clinical-rag.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "clinical-rag.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clinical-rag.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
