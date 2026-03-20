{{- define "auth.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "auth.fullname" -}}
{{- printf "%s" .Chart.Name -}}
{{- end -}}

{{- define "auth.labels" -}}
app.kubernetes.io/name: {{ include "auth.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.app.serviceVersion | quote }}
app.kubernetes.io/component: auth
app.kubernetes.io/part-of: clinical-ai-platform
{{- end -}}

{{- define "auth.selectorLabels" -}}
app.kubernetes.io/name: {{ include "auth.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
