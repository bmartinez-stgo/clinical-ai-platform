{{- define "clinical-chat.name" -}}
{{- .Values.app.name -}}
{{- end -}}

{{- define "clinical-chat.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}

{{- define "clinical-chat.labels" -}}
app.kubernetes.io/name: {{ include "clinical-chat.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/component: api
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "clinical-chat.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clinical-chat.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
